from __future__ import annotations

import numpy as np

from sm64_random_assets.audio_catalog import determine_audio_identity
from sm64_random_assets.audio_realizations.human_joncrall import random as human_random
from sm64_random_assets.audio_realizations.openai_gpt_5_6_thinking import semantic as openai_semantic
from sm64_random_assets.realizations import (
    AssetRealization,
    RealizationPolicy,
    RealizationRegistry,
)
from sm64_random_assets.util import util_random


_DEFAULT_AUDIO_REALIZATION_REGISTRY = None


def default_audio_realization_registry():
    global _DEFAULT_AUDIO_REALIZATION_REGISTRY
    if _DEFAULT_AUDIO_REALIZATION_REGISTRY is None:
        registry = RealizationRegistry()
        registry.register(AssetRealization(
            id='human.random-audio',
            author='human:joncrall',
            version=1,
            estimated_quality=0.0,
            generator=human_random.generate_random_sample,
            families=frozenset({'*'}),
            notes='Original full-range random PCM strategy.',
        ))
        registry.register(AssetRealization(
            id='openai.semantic-synth',
            author='openai:gpt-5.6-thinking',
            version=1,
            estimated_quality=0.65,
            generator=openai_semantic.generate_semantic_sample,
            families=frozenset({'*'}),
            notes='Deterministic filename-aware synthetic instruments and effects.',
        ))
        _DEFAULT_AUDIO_REALIZATION_REGISTRY = registry
    return _DEFAULT_AUDIO_REALIZATION_REGISTRY


def build_realization_policy(target_quality=0.0, include_authors=None,
                             exclude_authors=None, registry=None):
    registry = default_audio_realization_registry() if registry is None else registry
    include_authors = ('*',) if include_authors is None else tuple(include_authors)
    exclude_authors = () if exclude_authors is None else tuple(exclude_authors)
    return RealizationPolicy(
        registry=registry,
        target_quality=float(target_quality),
        include_authors=include_authors,
        exclude_authors=exclude_authors,
    )


def samples_to_aiff_bytes(samples, sampwidth=2):
    """Encode signed PCM bytes in AIFF's big-endian byte order."""
    samples = np.asarray(samples)
    if int(sampwidth) == 2:
        return samples.astype('>i2', copy=False).tobytes()
    if int(sampwidth) == 1:
        return samples.astype(np.int8, copy=False).tobytes()
    raise NotImplementedError(f'Unsupported AIFF sample width: {sampwidth!r}')


def generate_audio(output_dpath, info, realization_policy=None):
    """Generate a valid deterministic clean-room AIFF sample."""
    from sm64_random_assets.vendor import aifc

    if info.get('params', None) is None:
        return {'status': 'value-error: audio has no params'}

    params_dict = info['params'].copy()
    params_dict['comptype'] = params_dict['comptype'].encode()
    params_dict['compname'] = params_dict['compname'].encode()
    params = aifc._aifc_params(**params_dict)

    out_fpath = output_dpath / info['fname']
    out_fpath.parent.ensuredir()

    if info.get('use_ref') == 'zero':
        new_data = b'\x00' * (
            int(params.nframes) * int(params.nchannels) * int(params.sampwidth)
        )
        out = {'status': 'zeroed'}
    else:
        realization_policy = (
            build_realization_policy()
            if realization_policy is None else realization_policy
        )
        identity = determine_audio_identity(info)
        realization = realization_policy.resolve(identity, info)
        if realization is None:
            return {
                'status': 'value-error: no compatible audio realization',
                'identity_family': identity.family,
                'identity_member': identity.member,
            }

        rng = util_random.ensure_rng(info['fname'])
        samples = realization.generator(info['fname'], params, rng, identity)
        expected_samples = int(params.nframes) * int(params.nchannels)
        samples = np.asarray(samples).reshape(-1)
        if len(samples) != expected_samples:
            raise ValueError(
                f'Audio realization {realization.registry_key()!r} produced '
                f'{len(samples)} samples, expected {expected_samples}'
            )
        new_data = samples_to_aiff_bytes(samples, params.sampwidth)
        out = {
            'status': (
                'randomized'
                if realization.id == 'human.random-audio'
                else 'generated'
            ),
            'identity_family': identity.family,
            'identity_member': identity.member,
            'realization_id': realization.id,
            'realization_author': realization.author,
            'realization_version': realization.version,
            'realization_estimated_quality': realization.estimated_quality,
        }

    with open(out_fpath, 'wb') as file:
        new_file = aifc.open(file, 'wb')
        try:
            new_file.setparams(params)
            new_file.writeframes(new_data)
        finally:
            new_file.close()

    out['out_fpath'] = out_fpath
    return out


__all__ = [
    'build_realization_policy',
    'default_audio_realization_registry',
    'generate_audio',
    'samples_to_aiff_bytes',
]
