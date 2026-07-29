import json
from pathlib import Path

import numpy as np

from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking.intro_textures import (
    INTRO_TEXTURE_FILES,
    TITLE_BACKGROUND_FILES,
    render_intro_texture,
)


def _manifest_shapes():
    manifest_fpath = Path(__file__).parents[1] / 'sm64_random_assets' / 'rc' / 'asset_metadata.json'
    rows = json.loads(manifest_fpath.read_text())
    return {
        row['fname']: tuple(row['shape'])
        for row in rows
        if row.get('shape') is not None
    }


def test_intro_realization_covers_expected_startup_assets():
    assert len(INTRO_TEXTURE_FILES) == 35
    assert 'levels/intro/0.rgba16.png' in INTRO_TEXTURE_FILES
    assert 'textures/intro_raw/hand_open.rgba16.png' in INTRO_TEXTURE_FILES
    assert 'textures/intro_raw/red_star_7.rgba16.png' in INTRO_TEXTURE_FILES
    assert 'textures/title_screen_bg/title_screen_bg.05940.rgba16.png' in INTRO_TEXTURE_FILES
    # Preserve the human-authored legal text path rather than claiming it here.
    assert 'levels/intro/2_copyright.rgba16.png' not in INTRO_TEXTURE_FILES
    assert 'levels/intro/3_tm.rgba16.png' not in INTRO_TEXTURE_FILES


def test_all_intro_textures_render_with_manifest_shapes():
    shapes = _manifest_shapes()
    missing = sorted(fname for fname in INTRO_TEXTURE_FILES if fname not in shapes)
    assert not missing
    for fname in sorted(INTRO_TEXTURE_FILES):
        shape = shapes[fname]
        arr = render_intro_texture(fname, shape, np.random.RandomState(0))
        assert arr.shape == shape
        assert arr.dtype == np.uint8
        assert np.unique(arr.reshape(-1, shape[-1]), axis=0).shape[0] > 12


def test_title_background_strips_form_one_coherent_nonrepeating_image():
    strips = [
        render_intro_texture(fname, (20, 80, 4), np.random.RandomState(0))
        for fname in TITLE_BACKGROUND_FILES
    ]
    assembled = np.concatenate(strips, axis=0)
    assert assembled.shape == (160, 80, 4)
    assert assembled[..., 2].mean() > assembled[..., 1].mean() > assembled[..., 0].mean()
    assert np.unique(assembled.reshape(-1, 4), axis=0).shape[0] > 1000
    # Neighboring strips continue the same authored background but are not copies.
    for left, right in zip(strips, strips[1:]):
        assert not np.array_equal(left, right)
        boundary_jump = np.abs(left[-1].astype(np.int16) - right[0].astype(np.int16)).mean()
        assert boundary_jump < 70


def test_star_and_sparkle_animation_frames_are_distinct_and_transparent():
    for stem, count in [('red_star', 8), ('white_star', 8), ('sparkle', 6)]:
        frames = [
            render_intro_texture(
                f'textures/intro_raw/{stem}_{i}.rgba16.png',
                (32, 32, 4),
                np.random.RandomState(0),
            )
            for i in range(count)
        ]
        fingerprints = {frame.tobytes() for frame in frames}
        assert len(fingerprints) == count
        for frame in frames:
            assert frame[..., 3].min() == 0
            assert frame[..., 3].max() > 200


def test_open_and_closed_glove_are_visibly_different():
    open_hand = render_intro_texture(
        'textures/intro_raw/hand_open.rgba16.png',
        (32, 32, 4),
        np.random.RandomState(0),
    )
    closed_hand = render_intro_texture(
        'textures/intro_raw/hand_closed.rgba16.png',
        (32, 32, 4),
        np.random.RandomState(0),
    )
    assert not np.array_equal(open_hand, closed_hand)
    assert np.abs(open_hand.astype(np.int16) - closed_hand.astype(np.int16)).mean() > 20
    assert open_hand[..., 3].min() == 0
    assert closed_hand[..., 3].min() == 0


def test_face_shine_is_a_soft_intensity_alpha_mask():
    shine = render_intro_texture(
        'textures/intro_raw/mario_face_shine.ia8.png',
        (32, 32, 2),
        np.random.RandomState(0),
    )
    assert shine[..., 0].std() > 12
    assert shine[..., 1].min() == 0
    assert shine[..., 1].max() > 180
    assert len(np.unique(shine[..., 1])) > 32
