"""Selection primitives for versioned asset realizations.

A realization is one way to produce an asset. Realizations are deliberately
small records: they identify their author, their estimated quality, their
version, and the callable that implements them. Registries rank compatible
realizations by distance from a requested quality target.
"""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Mapping, Optional, Sequence, Tuple


class NoMatchingRealizationError(LookupError):
    """Raised when policy filters remove every realization for an asset."""


Matcher = Callable[[Mapping[str, Any]], bool]
Generator = Callable[..., Any]


def _always_matches(info: Mapping[str, Any]) -> bool:
    return True


def _coerce_patterns(
    value: Optional[Iterable[str]],
    *,
    default: Sequence[str],
) -> Tuple[str, ...]:
    if value is None:
        return tuple(default)
    if isinstance(value, str):
        value = [value]
    return tuple(str(item) for item in value)


@dataclass(frozen=True)
class RealizationPolicy:
    """Controls which realization is selected for each asset."""

    target_quality: float = 1.0
    include_authors: Tuple[str, ...] = ("*",)
    exclude_authors: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        quality = float(self.target_quality)
        if not 0.0 <= quality <= 1.0:
            raise ValueError(
                "target_quality must be between 0.0 and 1.0, "
                f"got {self.target_quality!r}"
            )
        object.__setattr__(self, "target_quality", quality)
        object.__setattr__(
            self,
            "include_authors",
            _coerce_patterns(self.include_authors, default=("*",)),
        )
        object.__setattr__(
            self,
            "exclude_authors",
            _coerce_patterns(self.exclude_authors, default=()),
        )

    @classmethod
    def coerce(
        cls,
        data: Optional["RealizationPolicy"] = None,
        **kwargs: Any,
    ) -> "RealizationPolicy":
        if data is None:
            return cls(**kwargs)
        if isinstance(data, cls):
            if kwargs:
                raise TypeError("Cannot override an existing RealizationPolicy")
            return data
        if isinstance(data, Mapping):
            combined = dict(data)
            combined.update(kwargs)
            return cls(**combined)
        raise TypeError(f"Cannot coerce realization policy from {type(data)!r}")

    def allows_author(self, author: str) -> bool:
        included = any(
            fnmatch.fnmatchcase(author, pattern)
            for pattern in self.include_authors
        )
        excluded = any(
            fnmatch.fnmatchcase(author, pattern)
            for pattern in self.exclude_authors
        )
        return included and not excluded


@dataclass(frozen=True)
class AssetRealization:
    """A versioned implementation capable of producing an asset."""

    id: str
    author: str
    estimated_quality: float
    version: int
    generator: Generator
    matcher: Matcher = _always_matches
    result_status: str = "generated"
    description: str = ""
    source_assets_used: bool = False

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Realization id cannot be empty")
        if not self.author:
            raise ValueError("Realization author cannot be empty")
        quality = float(self.estimated_quality)
        if not 0.0 <= quality <= 1.0:
            raise ValueError(
                "estimated_quality must be between 0.0 and 1.0, "
                f"got {self.estimated_quality!r}"
            )
        version = int(self.version)
        if version < 1:
            raise ValueError(f"version must be positive, got {version!r}")
        if self.source_assets_used:
            raise ValueError(
                "Realizations registered in the clean generation registry "
                "cannot use source assets"
            )
        object.__setattr__(self, "estimated_quality", quality)
        object.__setattr__(self, "version", version)

    def matches(self, info: Mapping[str, Any]) -> bool:
        return bool(self.matcher(info))

    def metadata(self) -> Mapping[str, Any]:
        return {
            "realization_id": self.id,
            "realization_author": self.author,
            "realization_estimated_quality": self.estimated_quality,
            "realization_version": self.version,
        }


class RealizationRegistry:
    """Ordered collection of asset realizations."""

    def __init__(self, name: str):
        self.name = name
        self._realizations: List[AssetRealization] = []
        self._ids = set()

    def register(self, realization: AssetRealization) -> AssetRealization:
        if realization.id in self._ids:
            raise KeyError(
                f"Duplicate realization id {realization.id!r} in {self.name!r}"
            )
        self._ids.add(realization.id)
        self._realizations.append(realization)
        return realization

    def realization(
        self,
        *,
        id: str,
        author: str,
        estimated_quality: float,
        version: int,
        matcher: Matcher = _always_matches,
        result_status: str = "generated",
        description: str = "",
        source_assets_used: bool = False,
    ) -> Callable[[Generator], Generator]:
        """Decorator that registers an implementation function."""

        def _decorate(generator: Generator) -> Generator:
            self.register(AssetRealization(
                id=id,
                author=author,
                estimated_quality=estimated_quality,
                version=version,
                generator=generator,
                matcher=matcher,
                result_status=result_status,
                description=description,
                source_assets_used=source_assets_used,
            ))
            return generator

        return _decorate

    def ranked(
        self,
        info: Mapping[str, Any],
        policy: Optional[RealizationPolicy] = None,
    ) -> List[AssetRealization]:
        """Return compatible realizations nearest to the requested quality."""
        policy = RealizationPolicy.coerce(policy)
        candidates = [
            realization
            for realization in self._realizations
            if policy.allows_author(realization.author)
            and realization.matches(info)
        ]
        candidates.sort(key=lambda realization: (
            abs(realization.estimated_quality - policy.target_quality),
            -realization.estimated_quality,
            -realization.version,
            realization.id,
        ))
        return candidates

    def require_ranked(
        self,
        info: Mapping[str, Any],
        policy: Optional[RealizationPolicy] = None,
    ) -> List[AssetRealization]:
        policy = RealizationPolicy.coerce(policy)
        ranked = self.ranked(info, policy)
        if not ranked:
            fname = info.get("fname", "<unknown>")
            raise NoMatchingRealizationError(
                f"No realization in {self.name!r} matched {fname!r} after "
                f"author filters include={policy.include_authors!r}, "
                f"exclude={policy.exclude_authors!r}"
            )
        return ranked

    def __iter__(self):
        return iter(self._realizations)

    def __len__(self) -> int:
        return len(self._realizations)
