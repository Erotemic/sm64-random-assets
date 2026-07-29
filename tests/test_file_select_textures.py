import itertools

import numpy as np

from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking.file_select_textures import (
    FILE_SELECT_TEXTURE_SPECS,
    render_file_select_texture,
)


SHAPES = {
    'levels/menu/main_menu_seg7.00018.rgba16.png': (32, 32, 4),
    'levels/menu/main_menu_seg7.00818.rgba16.png': (32, 32, 4),
    'levels/menu/main_menu_seg7.01018.rgba16.png': (32, 64, 4),
    'levels/menu/main_menu_seg7.02018.rgba16.png': (32, 64, 4),
    'levels/menu/main_menu_seg7.03468.rgba16.png': (32, 32, 4),
    'levels/menu/main_menu_seg7.03C68.rgba16.png': (32, 32, 4),
    'levels/menu/main_menu_seg7.04468.rgba16.png': (32, 32, 4),
    'levels/menu/main_menu_seg7.04C68.rgba16.png': (32, 32, 4),
    'levels/menu/main_menu_seg7.05468.rgba16.png': (32, 32, 4),
    'levels/menu/main_menu_seg7.0D1A8.rgba16.png': (32, 64, 4),
    'levels/menu/main_menu_seg7.0E1A8.rgba16.png': (32, 64, 4),
}


def test_file_select_texture_spec_matches_manifest_shapes():
    assert set(FILE_SELECT_TEXTURE_SPECS) == set(SHAPES)
    for fname, shape in SHAPES.items():
        data = render_file_select_texture(fname, shape, np.random.RandomState(0))
        assert data.shape == shape
        assert data.dtype == np.uint8
        assert data[..., 3].min() == 255
        assert np.unique(data[..., :3].reshape(-1, 3), axis=0).shape[0] > 20


def test_occupied_and_empty_save_slots_are_visibly_different():
    occupied = render_file_select_texture(
        'levels/menu/main_menu_seg7.01018.rgba16.png', (32, 64, 4))
    empty = render_file_select_texture(
        'levels/menu/main_menu_seg7.02018.rgba16.png', (32, 64, 4))
    assert not np.array_equal(occupied, empty)
    assert np.abs(occupied.astype(np.int16) - empty.astype(np.int16)).mean() > 24
    # Occupied state carries a warmer gold accent; empty state is brighter blue/silver.
    assert occupied[..., 0].max() > 220
    assert empty[..., 2].mean() > empty[..., 0].mean()


def test_action_button_materials_are_pairwise_differentiated():
    fnames = [
        'levels/menu/main_menu_seg7.03468.rgba16.png',
        'levels/menu/main_menu_seg7.03C68.rgba16.png',
        'levels/menu/main_menu_seg7.04468.rgba16.png',
        'levels/menu/main_menu_seg7.04C68.rgba16.png',
        'levels/menu/main_menu_seg7.05468.rgba16.png',
    ]
    rendered = {
        fname: render_file_select_texture(fname, (32, 32, 4))
        for fname in fnames
    }
    for left, right in itertools.combinations(fnames, 2):
        assert not np.array_equal(rendered[left], rendered[right])
        assert np.abs(
            rendered[left].astype(np.int16) - rendered[right].astype(np.int16)
        ).mean() > 8


def test_backdrops_are_blue_not_generic_gray_scanlines():
    for fname in [
        'levels/menu/main_menu_seg7.00018.rgba16.png',
        'levels/menu/main_menu_seg7.00818.rgba16.png',
        'levels/menu/main_menu_seg7.0D1A8.rgba16.png',
        'levels/menu/main_menu_seg7.0E1A8.rgba16.png',
    ]:
        shape = SHAPES[fname]
        data = render_file_select_texture(fname, shape)
        rgb = data[..., :3].astype(np.float32)
        assert rgb[..., 2].mean() > rgb[..., 0].mean() + 18
        assert rgb.std() > 12
