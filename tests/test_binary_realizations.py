from sm64_random_assets.generators import binary_generator
from sm64_random_assets.music_catalog import determine_binary_identity


def test_high_quality_selects_music_for_m64_and_zero_for_bin():
    policy = binary_generator.build_realization_policy(target_quality=1.0)
    music_info = {
        'fname': 'sound/sequences/us/03_level_grass.m64',
        'size': 5122,
    }
    music_identity = determine_binary_identity(music_info)
    music_realization = policy.resolve(music_identity, music_info)
    assert music_realization.id == 'openai.simple-music'

    binary_info = {'fname': 'sound/samples/something.bin', 'size': 32}
    binary_identity = determine_binary_identity(binary_info)
    binary_realization = policy.resolve(binary_identity, binary_info)
    assert binary_realization.id == 'human.zero-binary'


def test_low_quality_preserves_zero_m64_realization():
    policy = binary_generator.build_realization_policy(target_quality=0.0)
    info = {'fname': 'sound/sequences/us/03_level_grass.m64', 'size': 5122}
    realization = policy.resolve(determine_binary_identity(info), info)
    assert realization.id == 'human.zero-binary'
