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




def test_default_registry_uses_transparency_masks_for_ia_assets():
    policy = image_generator.build_realization_policy(target_quality=1.0)
    for info in [
        {'fname': 'levels/castle_grounds/5.ia8.png', 'shape': [32, 64, 2]},
        {'fname': 'textures/segment2/shadow_quarter_circle.ia8.png', 'shape': [16, 16, 2]},
        {'fname': 'actors/flame/flame_2.ia16.png', 'shape': [32, 32, 2]},
        {'fname': 'levels/ssl/1.ia16.png', 'shape': [32, 32, 2]},
    ]:
        identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
        realization = policy.resolve(identity, info)
        assert realization.id == 'openai.transparency-masks'
        assert realization.estimated_quality == 0.88

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


def test_default_registry_uses_dedicated_intro_realization():
    policy = image_generator.build_realization_policy(target_quality=1.0)
    for info in [
        {'fname': 'levels/intro/0.rgba16.png', 'shape': [32, 32, 4]},
        {'fname': 'textures/intro_raw/hand_open.rgba16.png', 'shape': [32, 32, 4]},
        {'fname': 'textures/intro_raw/red_star_4.rgba16.png', 'shape': [32, 32, 4]},
        {'fname': 'textures/title_screen_bg/title_screen_bg.001C0.rgba16.png', 'shape': [20, 80, 4]},
    ]:
        identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
        realization = policy.resolve(identity, info)
        assert realization.id == 'openai.intro-textures'
        assert realization.estimated_quality == 0.86


def test_intro_realization_does_not_replace_human_copyright_or_tm():
    policy = image_generator.build_realization_policy(target_quality=1.0)
    for info in [
        {'fname': 'levels/intro/2_copyright.rgba16.png', 'shape': [16, 128, 4]},
        {'fname': 'levels/intro/3_tm.rgba16.png', 'shape': [16, 16, 4]},
    ]:
        identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
        realization = policy.resolve(identity, info)
        assert realization.id == 'human.semantic'


def test_default_registry_uses_dedicated_menu_pointer_realization():
    policy = image_generator.build_realization_policy(target_quality=1.0)
    for info in [
        {'fname': 'levels/menu/main_menu_seg7.06328.rgba16.png', 'shape': [32, 32, 4]},
        {'fname': 'levels/menu/main_menu_seg7.06B28.rgba16.png', 'shape': [32, 32, 4]},
        {'fname': 'textures/intro_raw/hand_open.rgba16.png', 'shape': [32, 32, 4]},
        {'fname': 'textures/intro_raw/hand_closed.rgba16.png', 'shape': [32, 32, 4]},
    ]:
        identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
        realization = policy.resolve(identity, info)
        assert realization.id == 'openai.menu-pointers'
        assert realization.estimated_quality == 0.90


def test_default_registry_uses_file_select_texture_realization():
    policy = image_generator.build_realization_policy(target_quality=1.0)
    for info in [
        {'fname': 'levels/menu/main_menu_seg7.01018.rgba16.png', 'shape': [32, 64, 4]},
        {'fname': 'levels/menu/main_menu_seg7.02018.rgba16.png', 'shape': [32, 64, 4]},
        {'fname': 'levels/menu/main_menu_seg7.03468.rgba16.png', 'shape': [32, 32, 4]},
        {'fname': 'levels/menu/main_menu_seg7.04C68.rgba16.png', 'shape': [32, 32, 4]},
    ]:
        identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
        realization = policy.resolve(identity, info)
        assert identity.family == 'menu.file_select'
        assert realization.id == 'openai.file-select-textures'
        assert realization.estimated_quality == 0.91

