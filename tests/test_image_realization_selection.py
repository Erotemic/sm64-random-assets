import pytest

pytest.importorskip('kwimage')

from sm64_random_assets.generators import image_generator
from sm64_random_assets.image_catalog import determine_asset_identity
from sm64_random_assets.image_realizations.human_joncrall import semantic as human_semantic
from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking import pil_textures


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


def test_high_quality_mario_eyes_use_semantic_pil_art_via_frequent_pass():
    # Mario eye files route through the high-exposure frequent pass, which
    # delegates them to the semantic PIL eye renderer. Pin the intent (eyes
    # keep getting semantic PIL art, not generic filler) via pixel equality
    # rather than the realization id, so the test does not go stale when the
    # routing quality values shift.
    import numpy as np
    policy = image_generator.build_realization_policy(target_quality=1.0)
    info = {'fname': 'actors/mario/mario_eyes_center.rgba16.png', 'shape': [32, 32, 4]}
    identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
    realization = policy.resolve(identity, info)
    assert realization.id == 'openai.frequent-textures'
    assert realization.estimated_quality == 0.80
    shape = tuple(info['shape'])
    frequent_out = np.asarray(
        realization.generator(info['fname'], shape, np.random.RandomState(42), identity))
    pil_out = np.asarray(pil_textures.render_pil_texture(info['fname'], shape, np.random.RandomState(42)))
    assert np.array_equal(frequent_out, pil_out)


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



def test_debug_texture_author_is_opt_in_and_not_selected_in_normal_builds():
    normal_policy = image_generator.build_realization_policy(target_quality=1.0)
    info = {'fname': 'levels/castle_inside/1.rgba16.png', 'shape': [32, 32, 4]}
    identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
    realization = normal_policy.resolve(identity, info)
    assert realization.id == 'openai.castle-inside-textures'

    debug_policy = image_generator.build_realization_policy(
        target_quality=-1.0,
        include_authors=['debug:*'],
    )
    debug_realization = debug_policy.resolve(identity, info)
    assert debug_realization.id == 'debug.texture-id'
