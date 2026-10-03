import numpy as np

from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking.debug_texture_ids import (
    render_debug_texture_id,
    supports_debug_texture_id,
)


def test_debug_texture_id_supports_numeric_level_assets():
    assert supports_debug_texture_id(type('I', (), {'fname': 'levels/castle_inside/1.rgba16.png'})(), {'fname': 'levels/castle_inside/1.rgba16.png'})
    assert supports_debug_texture_id(type('I', (), {'fname': 'levels/menu/main_menu_seg7.073D0.rgba16.png'})(), {'fname': 'levels/menu/main_menu_seg7.073D0.rgba16.png'})
    assert not supports_debug_texture_id(type('I', (), {'fname': 'actors/mario/mario_eyes_center.rgba16.png'})(), {'fname': 'actors/mario/mario_eyes_center.rgba16.png'})


def test_debug_texture_id_renders_requested_shape_for_rgba_and_ia():
    rgba = render_debug_texture_id('levels/castle_inside/1.rgba16.png', (32, 32, 4))
    ia = render_debug_texture_id('levels/castle_inside/16.ia16.png', (32, 32, 2))
    assert rgba.shape == (32, 32, 4)
    assert ia.shape == (32, 32, 2)
    assert rgba.dtype == ia.dtype == np.uint8
    assert rgba.std() > 0
    assert ia[..., 1].max() > 0
