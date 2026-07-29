
import numpy as np
import pytest

pytest.importorskip('kwimage')

from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking import transparency_masks


@pytest.mark.parametrize('fname,shape', [
    ('levels/castle_grounds/5.ia8.png', (32, 64, 2)),
    ('levels/castle_inside/castle_light.ia16.png', (32, 32, 2)),
    ('actors/flame/flame_3.ia16.png', (32, 32, 2)),
    ('textures/segment2/shadow_quarter_circle.ia8.png', (16, 16, 2)),
    ('levels/ssl/1.ia16.png', (32, 32, 2)),
])
def test_render_transparency_masks_have_meaningful_alpha(fname, shape):
    data = transparency_masks.render_transparency_mask(fname, shape)
    assert data.shape == shape
    assert data.dtype == np.uint8
    alpha = data[:, :, 1]
    assert alpha.max() > 180
    assert alpha.min() < 20
    assert np.unique(alpha).size > 8


def test_supports_transparency_mask_rejects_glyph_like_assets():
    class Identity:
        def __init__(self, fname):
            self.fname = fname
    assert not transparency_masks.supports_transparency_mask(
        Identity('textures/segment2/font_graphics.05900.ia4.png'),
        {'fname': 'textures/segment2/font_graphics.05900.ia4.png', 'shape': [8, 16, 2]},
    )
    assert not transparency_masks.supports_transparency_mask(
        Identity('levels/menu/main_menu_seg7_us.0AC40.ia8.png'),
        {'fname': 'levels/menu/main_menu_seg7_us.0AC40.ia8.png', 'shape': [8, 8, 2]},
    )


def test_render_transparency_mask_accepts_realization_identity_argument():
    class Identity:
        fname = 'actors/flame/flame_0.ia16.png'

    data = transparency_masks.render_transparency_mask(
        Identity.fname,
        (32, 32, 2),
        np.random.RandomState(0),
        Identity(),
    )
    assert data.shape == (32, 32, 2)
    assert data.dtype == np.uint8
