from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath


class SequenceBuilder:
    """Assembler for the small SM64 sequence-command subset used here."""

    def __init__(self):
        self.data = bytearray()
        self.labels = {}
        self.fixups = []

    @property
    def offset(self):
        return len(self.data)

    def label(self, name):
        if name in self.labels:
            raise KeyError(f'Duplicate sequence label: {name!r}')
        self.labels[name] = self.offset

    def emit(self, *values):
        for value in values:
            value = int(value)
            if not 0 <= value <= 0xFF:
                raise ValueError(f'Byte out of range: {value!r}')
            self.data.append(value)

    def emit_var(self, value):
        value = int(value)
        if not 0 <= value <= 0x7FFF:
            raise ValueError(f'Variable-length integer out of range: {value!r}')
        if value >= 0x80:
            self.emit(0x80 | ((value >> 8) & 0x7F), value & 0xFF)
        else:
            self.emit(value)

    def emit_ref(self, opcode, label):
        self.emit(opcode, 0, 0)
        self.fixups.append((self.offset - 2, label))

    def finish(self):
        for pos, label in self.fixups:
            if label not in self.labels:
                raise KeyError(f'Unknown sequence label: {label!r}')
            offset = int(self.labels[label])
            if not 0 <= offset <= 0xFFFF:
                raise ValueError(f'Sequence offset out of range: {offset!r}')
            self.data[pos] = (offset >> 8) & 0xFF
            self.data[pos + 1] = offset & 0xFF
        return bytes(self.data)


TRACK_PROFILES = {
    'major': {
        'scale': (0, 2, 4, 7, 9),
        'melody': (0, 2, 4, 2, 7, 4, 2, 0),
        'bass': (0, 7, 9, 7),
        'tempo': 112,
    },
    'gentle': {
        'scale': (0, 2, 5, 7, 9),
        'melody': (0, 2, 5, 7, 5, 2, 0, 2),
        'bass': (0, 5, 7, 5),
        'tempo': 88,
    },
    'minor': {
        'scale': (0, 3, 5, 7, 10),
        'melody': (0, 3, 5, 3, 7, 5, 3, 0),
        'bass': (0, 7, 5, 7),
        'tempo': 104,
    },
    'urgent': {
        'scale': (0, 3, 5, 7, 10),
        'melody': (0, 3, 5, 7, 10, 7, 5, 3),
        'bass': (0, 0, 7, 7),
        'tempo': 148,
    },
}


def _classify_track(stem):
    stem = stem.lower()
    if any(token in stem for token in ['race', 'slide', 'hot', 'boss', 'koopa_road', 'metal_cap']):
        mood = 'urgent'
    elif any(token in stem for token in ['spooky', 'underground', 'endless_stairs', 'koopa_message']):
        mood = 'minor'
    elif any(token in stem for token in ['water', 'snow', 'inside_castle', 'peach', 'toad', 'intro', 'ending']):
        mood = 'gentle'
    else:
        mood = 'major'

    looping = (
        stem.startswith('02_menu_')
        or stem.startswith('03_level_')
        or stem.startswith('04_level_')
        or stem.startswith('05_level_')
        or stem.startswith('06_level_')
        or stem.startswith('07_level_')
        or stem.startswith('08_level_')
        or stem.startswith('09_level_')
        or stem.startswith('0a_level_')
        or stem.startswith('0c_level_')
        or stem.startswith('11_level_')
        or stem.startswith('13_event_merry_go_round')
        or stem.startswith('18_event_endless_stairs')
        or stem.startswith('19_level_')
        or stem.startswith('21_menu_')
    )
    return mood, looping


def _strip_json_comments(text):
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
    return text


def _load_json(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return json.loads(_strip_json_comments(Path(path).read_text()))


def _sound_name(instrument):
    if not isinstance(instrument, dict):
        return ''
    for key in ['sound', 'sound_lo', 'sound_hi']:
        sound = instrument.get(key, None)
        if isinstance(sound, str):
            return sound.lower()
        if isinstance(sound, dict):
            sample = sound.get('sample', '')
            if sample:
                return str(sample).lower()
    return ''


def _instrument_preferences(mood):
    preferred = {
        'major': ['guitar', 'brass', 'flute', 'organ', 'piano', 'vibraphone', 'bell', 'string', 'synth'],
        'gentle': ['flute', 'bell', 'music_box', 'vibraphone', 'organ', 'string', 'choir', 'piano', 'guitar'],
        'minor': ['organ', 'choir', 'string', 'bell', 'synth', 'brass', 'bass', 'guitar'],
        'urgent': ['brass', 'synth', 'guitar', 'organ', 'bass', 'string', 'piano'],
    }[mood]
    return preferred


def _score_instrument(sample_name, mood):
    bad = ['kick', 'snare', 'hihat', 'cymbal', 'tambourine', 'cabasa', 'rimshot', 'conga', 'clave']
    score = 0
    if any(token in sample_name for token in bad):
        score -= 100
    for rank, token in enumerate(_instrument_preferences(mood)):
        if token in sample_name:
            score += 60 - rank * 4
    if any(token in sample_name for token in ['bass', 'low']):
        score += 5
    return score


def choose_instruments(output_dpath, sequence_stem, mood):
    """Choose two pitched instrument slots from the target repo's sound bank."""
    output_dpath = Path(output_dpath)
    fallback = (0, 0)
    try:
        sequences = _load_json(output_dpath / 'sound' / 'sequences.json')
        bank_spec = sequences.get(sequence_stem, None)
        if isinstance(bank_spec, dict):
            bank_names = bank_spec.get('banks', [])
        else:
            bank_names = bank_spec or []
        if not bank_names:
            return fallback
        bank_name = bank_names[0]
        bank = _load_json(output_dpath / 'sound' / 'sound_banks' / f'{bank_name}.json')
        instrument_list = bank.get('instrument_list', [])
        instrument_defs = bank.get('instruments', {})
        scored = []
        for index, name in enumerate(instrument_list):
            if not name:
                continue
            inst = instrument_defs.get(name, {})
            sample_name = _sound_name(inst)
            scored.append((_score_instrument(sample_name, mood), index, sample_name))
        if not scored:
            return fallback
        scored.sort(key=lambda item: (-item[0], item[1]))
        melody = scored[0][1]
        bass_candidates = [item for item in scored if 'bass' in item[2]]
        if bass_candidates:
            bass_candidates.sort(key=lambda item: (-item[0], item[1]))
            bass = bass_candidates[0][1]
        elif len(scored) > 1:
            bass = scored[1][1]
        else:
            bass = melody
        return melody, bass
    except Exception:
        return fallback


def _emit_sequence_header(builder, *, tempo, looping, total_ticks):
    builder.emit(0xD3, 0x60)  # seq_setmutebhv
    builder.emit(0xD5, 0x00)  # seq_setmutescale
    builder.emit(0xDB, 88)    # seq_setvol
    builder.emit(0xDD, tempo) # seq_settempo
    builder.emit(0xD7, 0x00, 0x03)  # seq_initchannels 0 and 1
    builder.emit_ref(0x90, 'channel_melody')
    builder.emit_ref(0x91, 'channel_bass')
    if looping:
        builder.label('sequence_wait')
        builder.emit(0xFD)
        builder.emit_var(0x7FFF)
        builder.emit_ref(0xFB, 'sequence_wait')
    else:
        builder.emit(0xFD)
        builder.emit_var(total_ticks + 8)
        builder.emit(0xFF)


def _emit_channel(builder, *, label, layer_label, instrument, volume, pan,
                  looping, total_ticks):
    builder.label(label)
    builder.emit(0xC4)                 # chan_largenoteson
    builder.emit(0xC1, instrument)     # chan_setinstr
    builder.emit(0xDF, volume)         # chan_setvol
    builder.emit(0xDC, 127)            # chan_setpanmix
    builder.emit(0xDD, pan)            # chan_setpan
    builder.emit(0xD4, 8)              # chan_setreverb
    builder.emit_ref(0x90, layer_label)  # chan_setlayer 0 (US/JP opcode)
    if looping:
        builder.label(label + '_wait')
        builder.emit(0xFD)
        builder.emit_var(0x7FFF)
        builder.emit_ref(0xFB, label + '_wait')
    else:
        builder.emit(0xFD)
        builder.emit_var(total_ticks + 4)
        builder.emit(0xFF)


def _emit_layer(builder, *, label, notes, duration, velocity, looping):
    builder.label(label)
    builder.label(label + '_loop')
    for pitch in notes:
        if pitch is None:
            builder.emit(0xC0)
            builder.emit_var(duration)
        else:
            pitch = max(0, min(63, int(pitch)))
            builder.emit(0x40 + pitch)
            builder.emit_var(duration)
            builder.emit(velocity)
    if looping:
        builder.emit_ref(0xFB, label + '_loop')
    else:
        builder.emit(0xFF)


def build_simple_sequence(sequence_stem, *, melody_instrument=0, bass_instrument=0):
    mood, looping = _classify_track(sequence_stem)
    profile = TRACK_PROFILES[mood]

    # The note command uses a compact 0..63 pitch domain. Keep this conservative.
    root = 30 if mood in {'major', 'gentle'} else 28
    melody = [root + degree for degree in profile['melody']]
    bass_root = root - 12
    bass = [bass_root + degree for degree in profile['bass']]
    note_duration = 12 if mood != 'urgent' else 8
    bass_duration = note_duration * 2
    total_ticks = len(melody) * note_duration

    builder = SequenceBuilder()
    _emit_sequence_header(
        builder,
        tempo=profile['tempo'],
        looping=looping,
        total_ticks=total_ticks,
    )
    _emit_channel(
        builder,
        label='channel_melody',
        layer_label='layer_melody',
        instrument=melody_instrument,
        volume=72,
        pan=52,
        looping=looping,
        total_ticks=total_ticks,
    )
    _emit_channel(
        builder,
        label='channel_bass',
        layer_label='layer_bass',
        instrument=bass_instrument,
        volume=54,
        pan=76,
        looping=looping,
        total_ticks=total_ticks,
    )
    _emit_layer(
        builder,
        label='layer_melody',
        notes=melody,
        duration=note_duration,
        velocity=74,
        looping=looping,
    )
    _emit_layer(
        builder,
        label='layer_bass',
        notes=bass,
        duration=bass_duration,
        velocity=58,
        looping=looping,
    )
    data = builder.finish()
    return data, {
        'mood': mood,
        'looping': looping,
        'tempo': profile['tempo'],
        'melody_instrument': melody_instrument,
        'bass_instrument': bass_instrument,
        'unpadded_size': len(data),
    }



def _read_var(data, pos):
    first = data[pos]
    if first & 0x80:
        return ((first & 0x7F) << 8) | data[pos + 1], pos + 2
    return first, pos + 1


def _read_ref(data, pos):
    return (data[pos] << 8) | data[pos + 1]


def inspect_simple_sequence(data):
    """Validate and summarize the command subset emitted by this module."""
    data = bytes(data)
    pos = 0
    channel_offsets = []
    saw_sequence_terminal = False
    while pos < len(data):
        opcode = data[pos]
        pos += 1
        if opcode in {0xD3, 0xD5, 0xDB, 0xDD}:
            pos += 1
        elif opcode == 0xD7:
            pos += 2
        elif 0x90 <= opcode <= 0x9F:
            ref = _read_ref(data, pos)
            pos += 2
            channel_offsets.append(ref)
        elif opcode == 0xFD:
            _, pos = _read_var(data, pos)
        elif opcode == 0xFB:
            ref = _read_ref(data, pos)
            pos += 2
            if not 0 <= ref < len(data):
                raise ValueError(f'Invalid sequence jump target: {ref}')
            saw_sequence_terminal = True
            break
        elif opcode == 0xFF:
            saw_sequence_terminal = True
            break
        else:
            raise ValueError(f'Unexpected sequence opcode 0x{opcode:02X} at {pos - 1}')
    if not saw_sequence_terminal or len(channel_offsets) != 2:
        raise ValueError('Expected two channels and a sequence terminal')

    layer_offsets = []
    for channel_offset in channel_offsets:
        if not 0 <= channel_offset < len(data):
            raise ValueError(f'Invalid channel offset: {channel_offset}')
        pos = channel_offset
        saw_layer = False
        saw_terminal = False
        while pos < len(data):
            opcode = data[pos]
            pos += 1
            if opcode == 0xC4:
                continue
            elif opcode in {0xC1, 0xDF, 0xDC, 0xDD, 0xD4}:
                pos += 1
            elif opcode == 0x90:
                ref = _read_ref(data, pos)
                pos += 2
                layer_offsets.append(ref)
                saw_layer = True
            elif opcode == 0xFD:
                _, pos = _read_var(data, pos)
            elif opcode == 0xFB:
                ref = _read_ref(data, pos)
                pos += 2
                if not 0 <= ref < len(data):
                    raise ValueError(f'Invalid channel jump target: {ref}')
                saw_terminal = True
                break
            elif opcode == 0xFF:
                saw_terminal = True
                break
            else:
                raise ValueError(f'Unexpected channel opcode 0x{opcode:02X} at {pos - 1}')
        if not saw_layer or not saw_terminal:
            raise ValueError('Channel is missing a layer or terminal')

    total_notes = 0
    for layer_offset in layer_offsets:
        if not 0 <= layer_offset < len(data):
            raise ValueError(f'Invalid layer offset: {layer_offset}')
        pos = layer_offset
        saw_terminal = False
        layer_notes = 0
        while pos < len(data):
            opcode = data[pos]
            pos += 1
            if 0x40 <= opcode <= 0x7F:
                _, pos = _read_var(data, pos)
                pos += 1
                layer_notes += 1
            elif opcode == 0xC0:
                _, pos = _read_var(data, pos)
            elif opcode == 0xFB:
                ref = _read_ref(data, pos)
                pos += 2
                if not 0 <= ref < len(data):
                    raise ValueError(f'Invalid layer jump target: {ref}')
                saw_terminal = True
                break
            elif opcode == 0xFF:
                saw_terminal = True
                break
            else:
                raise ValueError(f'Unexpected layer opcode 0x{opcode:02X} at {pos - 1}')
        if not saw_terminal or layer_notes == 0:
            raise ValueError('Layer is missing notes or a terminal')
        total_notes += layer_notes
    return {
        'channel_offsets': tuple(channel_offsets),
        'layer_offsets': tuple(layer_offsets),
        'total_notes': total_notes,
    }

def generate_simple_music(output_dpath, info, rng=None, identity=None):
    fname = str(info['fname'])
    if not fname.endswith('.m64'):
        return None
    if '/us/' not in fname:
        # The bundled manifest only has authoritative sizes for the US sequences.
        return None
    sequence_stem = PurePosixPath(fname).stem
    mood, _ = _classify_track(sequence_stem)
    melody_instrument, bass_instrument = choose_instruments(
        output_dpath, sequence_stem, mood)
    data, metadata = build_simple_sequence(
        sequence_stem,
        melody_instrument=melody_instrument,
        bass_instrument=bass_instrument,
    )
    inspect_simple_sequence(data)
    requested_size = info.get('size', None)
    if requested_size is not None and len(data) < int(requested_size):
        # Unreachable bytes after seq/layer jumps or ends are harmless, and retaining
        # the manifest size avoids surprising the existing extraction/build rules.
        data = data + (b'\xFF' * (int(requested_size) - len(data)))
    return data, metadata


__all__ = [
    'SequenceBuilder',
    'build_simple_sequence',
    'choose_instruments',
    'generate_simple_music',
    'inspect_simple_sequence',
]
