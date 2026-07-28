from __future__ import annotations

from sm64_random_assets.music_catalog import determine_binary_identity
from sm64_random_assets.music_realizations.human_joncrall import zero as human_zero
from sm64_random_assets.music_realizations.openai_gpt_5_6_thinking import simple_music
from sm64_random_assets.realizations import (
    AssetRealization,
    RealizationPolicy,
    RealizationRegistry,
)
from sm64_random_assets.util import util_random


_DEFAULT_BINARY_REALIZATION_REGISTRY = None


def _supports_simple_music(identity, info):
    return identity.family == 'music.sequence'


def default_binary_realization_registry():
    global _DEFAULT_BINARY_REALIZATION_REGISTRY
    if _DEFAULT_BINARY_REALIZATION_REGISTRY is None:
        registry = RealizationRegistry()
        registry.register(AssetRealization(
            id='human.zero-binary',
            author='human:joncrall',
            version=1,
            estimated_quality=0.0,
            generator=human_zero.generate_zero_binary,
            families=frozenset({'*'}),
            notes='Original fixed-size zero-filled binary and M64 strategy.',
        ))
        registry.register(AssetRealization(
            id='openai.simple-music',
            author='openai:gpt-5.6-thinking',
            version=1,
            estimated_quality=0.60,
            generator=simple_music.generate_simple_music,
            supports=_supports_simple_music,
            notes='Compact clean-room two-voice melodies and bass lines.',
        ))
        _DEFAULT_BINARY_REALIZATION_REGISTRY = registry
    return _DEFAULT_BINARY_REALIZATION_REGISTRY


def build_realization_policy(target_quality=0.0, include_authors=None,
                             exclude_authors=None, registry=None):
    registry = default_binary_realization_registry() if registry is None else registry
    include_authors = ('*',) if include_authors is None else tuple(include_authors)
    exclude_authors = () if exclude_authors is None else tuple(exclude_authors)
    return RealizationPolicy(
        registry=registry,
        target_quality=float(target_quality),
        include_authors=include_authors,
        exclude_authors=exclude_authors,
    )


def generate_binary(output_dpath, info, realization_policy=None):
    """Generate zero-filled generic binaries or simple M64 music sequences."""
    if info.get('size', None) is None:
        return {'status': 'value-error: binary has no size'}

    realization_policy = (
        build_realization_policy()
        if realization_policy is None else realization_policy
    )
    identity = determine_binary_identity(info)
    rng = util_random.ensure_rng(info['fname'])

    tried = set()
    data = None
    metadata = {}
    realization = None
    while True:
        realization = realization_policy.resolve(identity, info, exclude_keys=tried)
        if realization is None:
            break
        result = realization.generator(output_dpath, info, rng, identity)
        if result is not None:
            if isinstance(result, tuple):
                data, metadata = result
            else:
                data = result
            break
        tried.add(realization.registry_key())

    if data is None or realization is None:
        return {
            'status': 'value-error: no compatible binary realization',
            'identity_family': identity.family,
            'identity_member': identity.member,
        }

    out_fpath = output_dpath / info['fname']
    out_fpath.parent.ensuredir()
    out_fpath.write_bytes(data)

    status = 'zeroed' if realization.id == 'human.zero-binary' else 'generated'
    out = {
        'status': status,
        'out_fpath': out_fpath,
        'identity_family': identity.family,
        'identity_member': identity.member,
        'realization_id': realization.id,
        'realization_author': realization.author,
        'realization_version': realization.version,
        'realization_estimated_quality': realization.estimated_quality,
    }
    out.update(metadata)
    return out


__all__ = [
    'build_realization_policy',
    'default_binary_realization_registry',
    'generate_binary',
]
