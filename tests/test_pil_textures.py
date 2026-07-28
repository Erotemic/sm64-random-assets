import numpy as np

from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking.pil_textures import (
    classify_texture_subject,
    render_pil_texture,
)


def test_texture_subject_classification():
    assert classify_texture_subject('levels/water/water_01.rgba16.png') == 'water'
    assert classify_texture_subject('actors/metal_box/metal_box_side.rgba16.png') == 'metal'
    assert classify_texture_subject('actors/goomba/goomba_face_blink.rgba16.png') == 'eye'


def test_render_pil_texture_is_deterministic_and_nontrivial():
    fname = 'textures/custom/stone_floor.rgba16.png'
    arr1 = render_pil_texture(fname, (32, 32, 4), np.random.RandomState(0))
    arr2 = render_pil_texture(fname, (32, 32, 4), np.random.RandomState(0))
    assert np.array_equal(arr1, arr2)
    assert arr1.shape == (32, 32, 4)
    assert arr1.dtype == np.uint8
    assert np.unique(arr1.reshape(-1, 4), axis=0).shape[0] > 8


def test_render_pil_texture_handles_intensity_alpha():
    fname = 'textures/custom/water.ia16.png'
    arr = render_pil_texture(fname, (24, 24, 2), np.random.RandomState(0))
    assert arr.shape == (24, 24, 2)
    assert arr.dtype == np.uint8
    assert arr[:, :, 0].std() > 0
    assert arr[:, :, 1].max() > 0
