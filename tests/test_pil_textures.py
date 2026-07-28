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
    assert classify_texture_subject('actors/goomba/goomba_face_blink.rgba16.png') == 'eye'
    assert classify_texture_role('actors/door/metal_door_overlay.rgba16.png') == 'overlay'
    assert classify_texture_role('actors/water_bubble/water_bubble.rgba16.png') == 'sprite'
    assert analyze_texture_intent('actors/door/metal_door.rgba16.png')['role'] == 'door'


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
