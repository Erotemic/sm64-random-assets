
import numpy as np

from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking.menu_pointers import (
    MENU_POINTER_FILES,
    render_menu_pointer,
)


def test_menu_pointer_manifest_and_states():
    assert MENU_POINTER_FILES['levels/menu/main_menu_seg7.06328.rgba16.png'] == 'open'
    assert MENU_POINTER_FILES['levels/menu/main_menu_seg7.06B28.rgba16.png'] == 'pressed'
    assert MENU_POINTER_FILES['textures/intro_raw/hand_open.rgba16.png'] == 'open'
    assert MENU_POINTER_FILES['textures/intro_raw/hand_closed.rgba16.png'] == 'pressed'


def test_menu_pointer_rendering_has_clean_transparency_and_strong_state_change():
    open_ptr = render_menu_pointer(
        'levels/menu/main_menu_seg7.06328.rgba16.png',
        (32, 32, 4),
        np.random.RandomState(0),
    )
    pressed_ptr = render_menu_pointer(
        'levels/menu/main_menu_seg7.06B28.rgba16.png',
        (32, 32, 4),
        np.random.RandomState(0),
    )
    for data in [open_ptr, pressed_ptr]:
        assert data.shape == (32, 32, 4)
        assert data.dtype == np.uint8
        assert data[..., 3].min() == 0
        assert data[..., 3].max() > 245
        occupied = (data[..., 3] > 16).mean()
        assert 0.22 < occupied < 0.82
        assert data[..., :3][data[..., 3] > 128].mean() > 135
    assert np.abs(open_ptr.astype(np.int16) - pressed_ptr.astype(np.int16)).mean() > 20
    assert not np.array_equal(open_ptr, pressed_ptr)


def test_intro_and_menu_pointer_states_share_renderer_but_not_pixels():
    intro_open = render_menu_pointer('textures/intro_raw/hand_open.rgba16.png', (32, 32, 4))
    intro_closed = render_menu_pointer('textures/intro_raw/hand_closed.rgba16.png', (32, 32, 4))
    assert not np.array_equal(intro_open, intro_closed)
