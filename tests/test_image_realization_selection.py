import pytest

pytest.importorskip('kwimage')

from sm64_random_assets.generators import image_generator
from sm64_random_assets.image_catalog import determine_asset_identity
from sm64_random_assets.image_realizations.human_joncrall import semantic as human_semantic


def test_default_registry_prefers_semantic_for_power_meter_at_high_quality():
    policy = image_generator.build_realization_policy(target_quality=1.0)
    info = {'fname': 'actors/power_meter/power_meter_full.rgba16.png', 'shape': [64, 64, 4]}
    identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
    realization = policy.resolve(identity, info)
    assert realization.id == 'human.semantic'


def test_default_registry_uses_pil_textures_for_generic_assets_at_high_quality():
    policy = image_generator.build_realization_policy(target_quality=1.0)
    info = {'fname': 'levels/bitdw/stone_floor.rgba16.png', 'shape': [32, 32, 4]}
    identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
    realization = policy.resolve(identity, info)
    assert realization.id == 'openai.pil-textures'


def test_validate_generated_image_enforces_shape_and_dtype():
    import numpy as np
    img = np.ones((8, 8, 1), dtype=np.float32)
    fixed = image_generator.validate_generated_image(img, (8, 8, 4))
    assert fixed.shape == (8, 8, 4)
    assert fixed.dtype == np.uint8


def test_default_registry_prefers_semantic_for_glyphs_at_high_quality():
    policy = image_generator.build_realization_policy(target_quality=1.0)
    info = {'fname': 'textures/segment2/segment2.00000.rgba16.png', 'shape': [64, 64, 4]}
    identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
    realization = policy.resolve(identity, info)
    assert realization.id == 'human.semantic'


def test_default_registry_uses_pil_textures_for_eyes_even_at_high_quality():
    policy = image_generator.build_realization_policy(target_quality=1.0)
    info = {'fname': 'actors/mario/mario_eyes_center.rgba16.png', 'shape': [32, 32, 4]}
    identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
    realization = policy.resolve(identity, info)
    assert realization.id == 'openai.pil-textures'


def test_default_registry_uses_specialized_castle_portraits():
    policy = image_generator.build_realization_policy(target_quality=1.0)
    for info in [
        {'fname': 'levels/castle_inside/17.rgba16.png', 'shape': [32, 64, 4]},
        {'fname': 'levels/castle_inside/30.rgba16.png', 'shape': [32, 32, 4]},
        {'fname': 'levels/castle_inside/39.rgba16.png', 'shape': [32, 64, 4]},
    ]:
        identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
        realization = policy.resolve(identity, info)
        assert realization.id == 'openai.castle-portraits'
        assert realization.estimated_quality == 0.82


def test_default_registry_uses_early_environment_realization_for_first_levels():
    policy = image_generator.build_realization_policy(target_quality=1.0)
    for info in [
        {'fname': 'levels/bob/0.rgba16.png', 'shape': [32, 32, 4]},
        {'fname': 'levels/castle_grounds/1.rgba16.png', 'shape': [32, 64, 4]},
        {'fname': 'textures/water/jrb_textures.00800.rgba16.png', 'shape': [32, 64, 4]},
        {'fname': 'textures/outside/castle_grounds_textures.03000.rgba16.png', 'shape': [32, 32, 4]},
    ]:
        identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
        realization = policy.resolve(identity, info)
        assert realization.id == 'openai.early-environment'
        assert realization.estimated_quality == 0.79


def test_default_registry_uses_bowser_peach_and_restored_frequent_realizations():
    policy = image_generator.build_realization_policy(target_quality=1.0)
    cases = [
        ({'fname': 'levels/castle_inside/5.rgba16.png', 'shape': [64, 32, 4]}, 'openai.bowser-peach-textures'),
        ({'fname': 'levels/castle_inside/6.rgba16.png', 'shape': [64, 32, 4]}, 'openai.bowser-peach-textures'),
        ({'fname': 'actors/bowser/bowser_shell.rgba16.png', 'shape': [32, 32, 4]}, 'openai.bowser-peach-textures'),
        ({'fname': 'actors/peach/peach_dress.rgba16.png', 'shape': [32, 32, 4]}, 'openai.bowser-peach-textures'),
        ({'fname': 'actors/door/castle_door.rgba16.png', 'shape': [64, 32, 4]}, 'openai.frequent-textures'),
    ]
    for info, expected in cases:
        identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
        realization = policy.resolve(identity, info)
        assert realization.id == expected


def test_default_registry_uses_differentiated_textures_for_samey_actor_families():
    policy = image_generator.build_realization_policy(target_quality=1.0)
    for info in [
        {'fname': 'actors/koopa/koopa_eyes_open.rgba16.png', 'shape': [32, 32, 4]},
        {'fname': 'actors/piranha_plant/piranha_plant_leaf.rgba16.png', 'shape': [64, 32, 4]},
        {'fname': 'actors/explosion/explosion_3.rgba16.png', 'shape': [32, 32, 4]},
        {'fname': 'actors/water_wave/water_wave_2.ia16.png', 'shape': [32, 32, 2]},
    ]:
        identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
        realization = policy.resolve(identity, info)
        assert realization.id == 'openai.differentiated-textures'
        assert realization.estimated_quality == 0.83
