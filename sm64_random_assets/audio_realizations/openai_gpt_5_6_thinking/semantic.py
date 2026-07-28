from __future__ import annotations

import math
import numpy as np


def _moving_average(data, width):
    width = max(1, min(int(width), len(data)))
    if width <= 1 or len(data) == 0:
        return data.copy()
    csum = np.cumsum(np.pad(data, (1, 0)), dtype=np.float64)
    smooth = (csum[width:] - csum[:-width]) / width
    left = np.full(width // 2, smooth[0])
    right_count = len(data) - len(smooth) - len(left)
    right = np.full(max(0, right_count), smooth[-1])
    return np.concatenate([left, smooth, right])[:len(data)]


def _noise(rng, n, smooth=1):
    data = rng.normal(0.0, 1.0, int(n))
    if smooth > 1:
        data = _moving_average(data, smooth)
    std = float(data.std())
    if std > 0:
        data = data / std
    return data


def _phase(n, sample_rate, target_frequency):
    """Create a phase with an integral cycle count for smooth wrapping."""
    n = max(1, int(n))
    cycles = max(1, int(round(float(target_frequency) * n / float(sample_rate))))
    return (2 * np.pi * cycles / n) * np.arange(n, dtype=np.float64)


def _harmonic_wave(phase, harmonics):
    signal = np.zeros_like(phase)
    for multiple, amplitude in harmonics:
        signal += float(amplitude) * np.sin(float(multiple) * phase)
    return signal


def _triangle(phase):
    return (2 / np.pi) * np.arcsin(np.sin(phase))


def _saw(phase, harmonics=10):
    signal = np.zeros_like(phase)
    for idx in range(1, harmonics + 1):
        signal += ((-1) ** (idx + 1)) * np.sin(idx * phase) / idx
    return signal


def _square(phase, harmonics=9):
    signal = np.zeros_like(phase)
    for idx in range(1, harmonics + 1, 2):
        signal += np.sin(idx * phase) / idx
    return signal


def _attack_release(n, attack_fraction=0.01, release_fraction=0.08):
    env = np.ones(int(n), dtype=np.float64)
    attack = min(len(env), max(1, int(len(env) * attack_fraction)))
    release = min(len(env), max(1, int(len(env) * release_fraction)))
    env[:attack] *= np.sin(np.linspace(0, np.pi / 2, attack)) ** 2
    env[-release:] *= np.cos(np.linspace(0, np.pi / 2, release)) ** 2
    return env


def _decay(n, rate=7.0, attack_fraction=0.002):
    x = np.linspace(0.0, 1.0, int(n), endpoint=False)
    env = np.exp(-float(rate) * x)
    attack = min(len(env), max(1, int(len(env) * attack_fraction)))
    env[:attack] *= np.linspace(0.0, 1.0, attack)
    return env


def _soft_clip(signal):
    return np.tanh(signal)


def _normalize(signal, peak=0.38):
    signal = np.asarray(signal, dtype=np.float64)
    if len(signal) == 0:
        return signal
    signal = signal - float(np.mean(signal))
    maximum = float(np.max(np.abs(signal)))
    if maximum > 0:
        signal = signal * (float(peak) / maximum)
    return np.clip(signal, -0.98, 0.98)


def _seed_frequency(rng, low=90.0, high=330.0):
    semitone_count = max(1, int(round(12 * math.log2(high / low))))
    step = int(rng.randint(0, semitone_count + 1))
    return low * (2 ** (step / 12))


def _sustained_instrument(name, n, sample_rate, rng):
    frequency = _seed_frequency(rng, 82.0, 330.0)
    phase = _phase(n, sample_rate, frequency)

    if 'sine' in name:
        signal = np.sin(phase)
    elif 'square' in name:
        signal = _square(phase, 9)
    elif 'saw' in name:
        signal = _saw(phase, 10)
    elif any(token in name for token in ['organ', 'accordion', 'harmonica']):
        signal = _harmonic_wave(phase, [(1, 1.0), (2, 0.45), (3, 0.28), (4, 0.18), (6, 0.08)])
        signal *= 0.93 + 0.07 * np.sin(phase / max(1, int(round(frequency / 4))))
    elif any(token in name for token in ['string', 'choir', 'brass', 'trumpet', 'trombone', 'horn']):
        signal = _harmonic_wave(phase, [(1, 1.0), (2, 0.33), (3, 0.22), (4, 0.12), (5, 0.08)])
        signal += 0.025 * _noise(rng, n, smooth=max(2, int(sample_rate / 5000)))
    elif any(token in name for token in ['flute', 'whistle']):
        signal = _harmonic_wave(phase, [(1, 1.0), (2, 0.12), (3, 0.04)])
        signal += 0.018 * _noise(rng, n, smooth=max(2, int(sample_rate / 3500)))
    elif 'bass' in name:
        phase = _phase(n, sample_rate, _seed_frequency(rng, 45.0, 110.0))
        signal = 0.8 * np.sin(phase) + 0.22 * _triangle(phase)
    else:
        signal = 0.72 * _triangle(phase) + 0.22 * np.sin(2 * phase)
    return _normalize(_soft_clip(signal), peak=0.34)


def _pitched_decay(name, n, sample_rate, rng):
    frequency = _seed_frequency(rng, 180.0, 880.0)
    phase = _phase(n, sample_rate, frequency)
    if any(token in name for token in ['bell', 'vibraphone', 'music_box', 'triangle', 'steel_drum']):
        signal = _harmonic_wave(phase, [(1.0, 1.0), (2.01, 0.35), (3.96, 0.18), (6.1, 0.08)])
        envelope = _decay(n, rate=4.5)
    elif any(token in name for token in ['piano', 'rhodes', 'harpsichord']):
        signal = _harmonic_wave(phase, [(1, 1.0), (2, 0.38), (3, 0.21), (4, 0.12), (6, 0.06)])
        signal += 0.025 * _noise(rng, n, smooth=2)
        envelope = _decay(n, rate=5.5)
    elif any(token in name for token in ['banjo', 'guitar', 'sitar', 'pizzicato']):
        signal = 0.72 * _triangle(phase) + 0.25 * _saw(phase, 8)
        envelope = _decay(n, rate=6.5)
    else:
        signal = np.sin(phase) + 0.22 * np.sin(2.7 * phase)
        envelope = _decay(n, rate=5.5)
    return _normalize(signal * envelope, peak=0.40)


def _drum_or_metal(name, n, sample_rate, rng):
    x = np.arange(n, dtype=np.float64) / float(sample_rate)
    noise = _noise(rng, n, smooth=1)

    if 'kick' in name or 'timpani' in name or 'landing' in name:
        start_freq = 105.0 if 'kick' in name else 145.0
        end_freq = 42.0
        duration = max(x[-1] if len(x) else 0.001, 0.001)
        freq_curve = end_freq + (start_freq - end_freq) * np.exp(-7 * x / duration)
        phase = 2 * np.pi * np.cumsum(freq_curve) / sample_rate
        signal = np.sin(phase) * _decay(n, rate=9.0)
        signal += 0.08 * noise * _decay(n, rate=24.0)
    elif any(token in name for token in ['hihat', 'cymbal', 'tambourine', 'cabasa', 'sleigh']):
        high = noise - _moving_average(noise, max(2, int(sample_rate / 5000)))
        metallic = np.sin(2 * np.pi * 2371 * x) + 0.7 * np.sin(2 * np.pi * 3191 * x)
        signal = (0.72 * high + 0.18 * metallic) * _decay(n, rate=8.5 if 'open' in name else 18.0)
    elif any(token in name for token in ['snare', 'rimshot', 'clave', 'conga', 'stick']):
        tone = np.sin(2 * np.pi * (220 + int(rng.randint(0, 180))) * x)
        signal = (0.65 * noise + 0.35 * tone) * _decay(n, rate=16.0)
    else:
        signal = noise * _decay(n, rate=12.0)
    return _normalize(signal, peak=0.42)


def _voice_chirp(name, n, sample_rate, rng):
    x = np.arange(n, dtype=np.float64) / float(sample_rate)
    duration = max(float(n) / sample_rate, 0.001)
    syllables = max(1, min(4, int(round(duration * 4))))
    base = _seed_frequency(rng, 115.0, 220.0)
    vibrato = 1.0 + 0.018 * np.sin(2 * np.pi * 5.2 * x)
    contour = 1.0 + 0.12 * np.sin(2 * np.pi * syllables * x / duration)
    frequency = base * vibrato * contour
    phase = 2 * np.pi * np.cumsum(frequency) / sample_rate
    source = _harmonic_wave(phase, [(1, 1.0), (2, 0.42), (3, 0.22), (4, 0.11)])

    # A lightweight vowel-like coloration using amplitude-modulated harmonics.
    formant = (
        0.55 * np.sin(2 * np.pi * 650 * x) +
        0.25 * np.sin(2 * np.pi * 1150 * x) +
        0.12 * np.sin(2 * np.pi * 2350 * x)
    )
    syllable_env = 0.45 + 0.55 * np.maximum(0.0, np.sin(np.pi * syllables * x / duration))
    signal = (0.78 * source + 0.20 * formant * source) * syllable_env
    signal += 0.018 * _noise(rng, n, smooth=max(2, int(sample_rate / 4000)))
    signal *= _attack_release(n, attack_fraction=0.015, release_fraction=0.12)
    return _normalize(_soft_clip(signal), peak=0.34)


def _water_or_soft_effect(name, n, sample_rate, rng):
    noise = _noise(rng, n, smooth=max(2, int(sample_rate / 2200)))
    x = np.arange(n, dtype=np.float64) / float(sample_rate)
    if any(token in name for token in ['splash', 'plunge', 'swim', 'water']):
        bubble = np.sin(2 * np.pi * (160 + 90 * np.exp(-5 * x)) * x)
        signal = (0.65 * noise + 0.22 * bubble) * _decay(n, rate=6.0)
    elif 'step_' in name:
        low = np.sin(2 * np.pi * (75 + int(rng.randint(0, 55))) * x)
        signal = (0.55 * noise + 0.28 * low) * _decay(n, rate=18.0)
    elif any(token in name for token in ['camera_buzz', 'brushing']):
        signal = noise * _attack_release(n, 0.01, 0.15)
    else:
        chirp_freq = 220 + 520 * np.exp(-5 * x / max(x[-1] if len(x) else 1.0, 0.001))
        phase = 2 * np.pi * np.cumsum(chirp_freq) / sample_rate
        signal = (0.48 * np.sin(phase) + 0.34 * noise) * _decay(n, rate=8.0)
    return _normalize(signal, peak=0.32)


def _classify(name):
    if any(token in name for token in [
        'kick', 'timpani', 'snare', 'rimshot', 'hihat', 'cymbal',
        'tambourine', 'cabasa', 'clave', 'conga', 'triangle', 'sleigh',
        'steel_drum', 'landing',
    ]):
        return 'percussion'
    if any(token in name for token in [
        'piano', 'rhodes', 'harpsichord', 'music_box', 'bell', 'vibraphone',
        'banjo', 'guitar', 'sitar', 'pizzicato', 'orchestra_hit',
    ]):
        return 'pitched_decay'
    if any(token in name for token in [
        'organ', 'accordion', 'harmonica', 'string', 'choir', 'brass',
        'trumpet', 'trombone', 'horn', 'flute', 'whistle', 'bass',
        'sawtooth', 'square_synth',
    ]):
        return 'sustained'
    if '/sfx_mario' in name or '/sfx_mario_peach' in name or any(token in name for token in [
        'yoshi', '_la.', 'course_start', 'bark',
    ]):
        return 'voice'
    return 'effect'


def generate_semantic_sample(fname, params, rng, identity=None):
    """Generate deterministic, moderate-level clean-room PCM from the filename."""
    nframes = int(params.nframes)
    nchannels = int(params.nchannels)
    sample_rate = max(1, int(params.framerate))
    name = str(fname).lower()

    category = _classify(name)
    if category == 'percussion':
        mono = _drum_or_metal(name, nframes, sample_rate, rng)
    elif category == 'pitched_decay':
        mono = _pitched_decay(name, nframes, sample_rate, rng)
    elif category == 'sustained':
        mono = _sustained_instrument(name, nframes, sample_rate, rng)
    elif category == 'voice':
        mono = _voice_chirp(name, nframes, sample_rate, rng)
    else:
        mono = _water_or_soft_effect(name, nframes, sample_rate, rng)

    # Quantize below full scale. AIFF PCM is encoded later in big-endian order.
    pcm = np.round(mono * 32767.0).astype(np.int16)
    if nchannels > 1:
        pcm = np.repeat(pcm[:, None], nchannels, axis=1).reshape(-1)
    return pcm


__all__ = ['generate_semantic_sample']
