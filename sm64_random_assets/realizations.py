from __future__ import annotations

import dataclasses as dc
import fnmatch
from typing import Callable, Iterable, Optional


@dc.dataclass(frozen=True)
class AssetIdentity:
    """Logical identity for an asset."""
    fname: str
    family: str
    member: str = 'default'


GeneratorFunc = Callable[[str, tuple | list, object, AssetIdentity], object]
SupportsFunc = Callable[[AssetIdentity, dict], bool]


@dc.dataclass(frozen=True)
class AssetRealization:
    """A versioned image realization candidate."""
    id: str
    author: str
    version: int
    estimated_quality: float
    generator: GeneratorFunc
    families: Optional[frozenset[str]] = None
    supports: Optional[SupportsFunc] = None
    provenance: str = 'clean_room'
    created_with_source_assets: bool = False
    notes: str = ''

    def registry_key(self):
        return (self.id, self.version)

    def matches_identity(self, identity: AssetIdentity, info: dict) -> bool:
        if self.families is not None:
            if '*' not in self.families and identity.family not in self.families:
                return False
        if self.supports is not None and not self.supports(identity, info):
            return False
        return True


class RealizationRegistry:
    def __init__(self):
        self._items = []
        self._keys = set()

    def register(self, realization: AssetRealization) -> AssetRealization:
        key = realization.registry_key()
        if key in self._keys:
            raise KeyError(f'Duplicate realization key: {key!r}')
        self._keys.add(key)
        self._items.append(realization)
        return realization

    def iter_candidates(self, identity: AssetIdentity, info: dict) -> Iterable[AssetRealization]:
        for realization in self._items:
            if realization.created_with_source_assets:
                continue
            if realization.matches_identity(identity, info):
                yield realization

    def choose(self, identity: AssetIdentity, info: dict, *, target_quality: float,
               include_authors=None, exclude_authors=None,
               exclude_keys=None) -> Optional[AssetRealization]:
        include_authors = ['*'] if include_authors is None else list(include_authors)
        exclude_authors = [] if exclude_authors is None else list(exclude_authors)
        exclude_keys = set() if exclude_keys is None else set(exclude_keys)

        candidates = []
        for realization in self.iter_candidates(identity, info):
            if realization.registry_key() in exclude_keys:
                continue
            if not _author_is_allowed(realization.author, include_authors, exclude_authors):
                continue
            candidates.append(realization)
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda c: (
                abs(float(c.estimated_quality) - float(target_quality)),
                -float(c.estimated_quality),
                -int(c.version),
                c.id,
                c.author,
            )
        )


def _author_is_allowed(author: str, include_patterns, exclude_patterns) -> bool:
    if include_patterns:
        if not any(fnmatch.fnmatch(author, pat) for pat in include_patterns):
            return False
    if exclude_patterns:
        if any(fnmatch.fnmatch(author, pat) for pat in exclude_patterns):
            return False
    return True


@dc.dataclass
class RealizationPolicy:
    registry: RealizationRegistry
    target_quality: float = 0.0
    include_authors: tuple[str, ...] = ('*',)
    exclude_authors: tuple[str, ...] = ()
    family_cache: dict = dc.field(default_factory=dict)

    def resolve(self, identity: AssetIdentity, info: dict, *, exclude_keys=None):
        family_key = (identity.family, tuple(sorted(exclude_keys or [])))
        if family_key not in self.family_cache:
            self.family_cache[family_key] = self.registry.choose(
                identity,
                info,
                target_quality=self.target_quality,
                include_authors=self.include_authors,
                exclude_authors=self.exclude_authors,
                exclude_keys=exclude_keys,
            )
        return self.family_cache[family_key]


__all__ = [
    'AssetIdentity',
    'AssetRealization',
    'RealizationPolicy',
    'RealizationRegistry',
]
