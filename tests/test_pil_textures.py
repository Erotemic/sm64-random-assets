import numpy as np

from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking.pil_textures import (
    analyze_texture_intent,
    classify_texture_role,
    classify_texture_subject,
    render_pil_texture,
)


def test_texture_subject_and_role_classification():
    assert classify_texture_subject('levels/water/water_01.rgba16.png') == 'water'
    assert classify_texture_subject('actors/door/metal_door.rgba16.png') == 'metal'
    assert classify_texture_subject('actors/bowser/bowser_shell.rgba16.png') == 'shell'
    assert classify_texture_subject('actors/penguin/penguin_beak.rgba16.png') == 'beak'
    assert classify_texture_subject('actors/bookend/bookend_pages.rgba16.png') == 'pages'
    assert classify_texture_subject('actors/mad_piano/mad_piano_keys.rgba16.png') == 'piano_keys'
    assert classify_texture_subject('actors/yoshi_egg/yoshi_egg_0_unused.rgba16.png') == 'egg'
    assert classify_texture_subject('actors/coin/coin_front.ia16.png') == 'coin'
    assert classify_texture_subject('textures/generic/bob_textures.00000.rgba16.png') == 'grass'
    assert classify_texture_subject('actors/mario/mario_eyes_center.rgba16.png') == 'eye'
    assert classify_texture_role('actors/door/metal_door_overlay.rgba16.png') == 'overlay'
    assert classify_texture_role('actors/water_bubble/water_bubble.rgba16.png') == 'sprite'
    assert classify_texture_role('actors/mario/mario_eyes_closed.rgba16.png') == 'face'


def test_texture_intent_exposes_family_and_motif():
    intent = analyze_texture_intent('actors/lakitu_cameraman/lakitu_camera_lens.rgba16.png')
    assert intent.family == 'lakitu_cameraman'
    assert intent.subject == 'lens'
    assert intent.motif == 'lens'
    mario_eye = analyze_texture_intent('actors/mario/mario_eyes_left_unused.rgba16.png')
    assert mario_eye.motif == 'mario_eye'
    water = analyze_texture_intent('textures/water/jrb_textures.00000.rgba16.png')
    assert water.motif == 'sea_water'
    grass = analyze_texture_intent('textures/grass/wf_textures.00000.rgba16.png')
    assert grass.motif == 'wildflower_grass'


def test_render_pil_texture_is_deterministic_and_nontrivial():
    fname = 'textures/custom/stone_floor.rgba16.png'
    arr1 = render_pil_texture(fname, (32, 32, 4), np.random.RandomState(0))
    arr2 = render_pil_texture(fname, (32, 32, 4), np.random.RandomState(0))
    assert np.array_equal(arr1, arr2)
    assert arr1.shape == (32, 32, 4)
    assert arr1.dtype == np.uint8
    assert np.unique(arr1.reshape(-1, 4), axis=0).shape[0] > 12


def test_render_pil_texture_handles_intensity_alpha():
    fname = 'textures/custom/water.ia16.png'
    arr = render_pil_texture(fname, (24, 24, 2), np.random.RandomState(0))
    assert arr.shape == (24, 24, 2)
    assert arr.dtype == np.uint8
    assert arr[:, :, 0].std() > 0
    assert arr[:, :, 1].max() > 0


def test_render_sprite_uses_transparency():
    fname = 'actors/water_bubble/water_bubble.rgba16.png'
    arr = render_pil_texture(fname, (32, 32, 4), np.random.RandomState(0))
    assert arr.shape == (32, 32, 4)
    assert arr[:, :, 3].min() == 0
    assert arr[:, :, 3].max() > 0


def test_render_semantic_part_textures_have_structure():
    egg = render_pil_texture('actors/yoshi_egg/yoshi_egg_0_unused.rgba16.png', (32, 32, 4), np.random.RandomState(0))
    keys = render_pil_texture('actors/mad_piano/mad_piano_keys.rgba16.png', (32, 32, 4), np.random.RandomState(0))
    shell = render_pil_texture('actors/bowser/bowser_shell.rgba16.png', (32, 32, 4), np.random.RandomState(0))
    assert egg[:, :, 3].max() > 0
    assert keys[:, :, 0].std() > 20
    assert shell[:, :, 1].mean() > shell[:, :, 0].mean()


def test_render_coin_and_bobomb_textures_have_specialized_structure():
    coin = render_pil_texture('actors/coin/coin_front.ia16.png', (32, 32, 2), np.random.RandomState(0))
    bomb = render_pil_texture('actors/bobomb/bob-omb_left_side.rgba16.png', (32, 32, 4), np.random.RandomState(0))
    battlefield = render_pil_texture('textures/generic/bob_textures.00000.rgba16.png', (32, 32, 4), np.random.RandomState(0))
    assert coin.shape == (32, 32, 2)
    assert coin[:, :, 1].max() > 0
    assert coin[:, :, 0].std() > 10
    assert bomb[:, :, 0:3].std() > 10
    assert battlefield[:, :, 1].mean() > battlefield[:, :, 0].mean()


def test_render_mario_eye_water_and_grass_have_semantic_structure():
    mario_eye = render_pil_texture('actors/mario/mario_eyes_left_unused.rgba16.png', (32, 32, 4), np.random.RandomState(0))
    water = render_pil_texture('textures/water/jrb_textures.00000.rgba16.png', (32, 32, 4), np.random.RandomState(0))
    grass = render_pil_texture('textures/grass/wf_textures.00000.rgba16.png', (32, 32, 4), np.random.RandomState(0))
    assert mario_eye[:, :, 2].mean() > mario_eye[:, :, 0].mean()  # blue iris bias
    assert water[:, :, 2].mean() > water[:, :, 1].mean() > water[:, :, 0].mean()
    assert grass[:, :, 1].mean() > grass[:, :, 0].mean()
    assert grass[:, :, 1].std() > 10
