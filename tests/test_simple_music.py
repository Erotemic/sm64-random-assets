import json
from pathlib import Path

from sm64_random_assets.music_realizations.openai_gpt_5_6_thinking.simple_music import (
    build_simple_sequence,
    choose_instruments,
    generate_simple_music,
    inspect_simple_sequence,
)


def test_simple_sequence_is_deterministic_and_structurally_valid():
    data1, meta1 = build_simple_sequence('03_level_grass')
    data2, meta2 = build_simple_sequence('03_level_grass')
    assert data1 == data2
    assert meta1 == meta2
    summary = inspect_simple_sequence(data1)
    assert len(summary['channel_offsets']) == 2
    assert len(summary['layer_offsets']) == 2
    assert summary['total_notes'] == 12


def test_looping_and_one_shot_tracks_differ():
    loop_data, loop_meta = build_simple_sequence('03_level_grass')
    jingle_data, jingle_meta = build_simple_sequence('12_event_high_score')
    assert loop_meta['looping'] is True
    assert jingle_meta['looping'] is False
    assert loop_data != jingle_data
    inspect_simple_sequence(loop_data)
    inspect_simple_sequence(jingle_data)


def test_choose_instruments_uses_target_sound_bank(tmp_path):
    sound = tmp_path / 'sound'
    banks = sound / 'sound_banks'
    banks.mkdir(parents=True)
    (sound / 'sequences.json').write_text(json.dumps({
        '03_level_grass': ['22'],
    }))
    (banks / '22.json').write_text(json.dumps({
        'instruments': {
            'drum': {'sound': '06_kick_drum_1'},
            'lead': {'sound': '19_brass_Eb3'},
            'bass': {'sound': '1A_slap_bass_G#2'},
        },
        'instrument_list': ['drum', 'lead', 'bass'],
    }))
    melody, bass = choose_instruments(tmp_path, '03_level_grass', 'major')
    assert melody == 1
    assert bass == 2


def test_all_us_manifest_sequences_fit_original_asset_sizes():
    manifest_fpath = Path(__file__).parents[1] / 'sm64_random_assets' / 'rc' / 'asset_metadata.json'
    items = json.loads(manifest_fpath.read_text())
    found = 0
    for info in items:
        if info['fname'].endswith('.m64') and '/us/' in info['fname']:
            data, meta = generate_simple_music(Path('/missing-target'), info)
            assert len(data) == info['size']
            assert meta['unpadded_size'] <= info['size']
            inspect_simple_sequence(data[:meta['unpadded_size']])
            assert data[:meta['unpadded_size']] != b'\x00' * meta['unpadded_size']
            found += 1
    assert found == 34
