from collections import namedtuple

import numpy as np

from sm64_random_assets.audio_catalog import determine_audio_identity
from sm64_random_assets.audio_realizations.openai_gpt_5_6_thinking.semantic import (
    generate_semantic_sample,
)
from sm64_random_assets.generators.audio_generator import (
    default_audio_realization_registry,
    samples_to_aiff_bytes,
)


Params = namedtuple(
    'Params',
    'nchannels sampwidth framerate nframes comptype compname',
)


def _params(nframes=16000, framerate=32000):
    return Params(
        nchannels=1,
        sampwidth=2,
        framerate=framerate,
        nframes=nframes,
        comptype=b'NONE',
        compname=b'not compressed',
    )


def test_aiff_pcm_is_big_endian():
    samples = np.array([1, 256, -2], dtype=np.int16)
    assert samples_to_aiff_bytes(samples, 2) == b'\x00\x01\x01\x00\xff\xfe'


def test_audio_identity_groups_sound_bank():
    a = determine_audio_identity('sound/samples/instruments/01_banjo_1.aiff')
    b = determine_audio_identity('sound/samples/instruments/44_grand_piano.aiff')
    assert a.family == b.family == 'audio.bank.instruments'
    assert a.member == '01_banjo_1'


def test_registry_quality_selects_semantic_audio():
    registry = default_audio_realization_registry()
    identity = determine_audio_identity('sound/samples/instruments/35_gospel_organ.aiff')
    chosen = registry.choose(identity, {}, target_quality=1.0)
    assert chosen.id == 'openai.semantic-synth'
    assert chosen.author == 'openai:gpt-5.6-thinking'


def test_semantic_samples_are_deterministic_moderate_and_nonstatic():
    names = [
        'sound/samples/instruments/35_gospel_organ.aiff',
        'sound/samples/instruments/06_kick_drum_1.aiff',
        'sound/samples/instruments/44_grand_piano.aiff',
        'sound/samples/sfx_mario/04_mario_yahoo.aiff',
        'sound/samples/sfx_water/01_splash.aiff',
        'sound/samples/sfx_5/0A.aiff',
    ]
    params = _params()
    for name in names:
        sample1 = generate_semantic_sample(
            name, params, np.random.RandomState(12345))
        sample2 = generate_semantic_sample(
            name, params, np.random.RandomState(12345))
        assert np.array_equal(sample1, sample2)
        assert sample1.shape == (params.nframes,)
        assert sample1.dtype == np.int16
        assert np.unique(sample1).size > 32
        peak = np.max(np.abs(sample1.astype(np.int32))) / 32767
        rms = np.sqrt(np.mean(sample1.astype(np.float64) ** 2)) / 32767
        assert 0.05 < peak <= 0.45
        assert 0.005 < rms < 0.35
        assert abs(float(sample1.mean())) < 128
