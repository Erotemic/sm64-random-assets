import numpy as np

from sm64_random_assets.image_catalog import determine_asset_identity
from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking.bowser_peach_textures import (
    FAKEOUT_PORTRAIT_FILES,
    render_bowser_peach_texture,
)


def test_fakeout_portrait_identity_is_coherent_family():
    peach = determine_asset_identity('levels/castle_inside/5.rgba16.png')
    bowser = determine_asset_identity('levels/castle_inside/6.rgba16.png')
    assert peach.family == 'castle.fakeout_portrait'
    assert bowser.family == 'castle.fakeout_portrait'
    assert peach.member == 'peach'
    assert bowser.member == 'bowser'


def test_fakeout_portrait_pair_is_distinct_and_nontrivial():
    peach = render_bowser_peach_texture(
        'levels/castle_inside/5.rgba16.png',
        (64, 32, 4),
        np.random.RandomState(0),
    )
    bowser = render_bowser_peach_texture(
        'levels/castle_inside/6.rgba16.png',
        (64, 32, 4),
        np.random.RandomState(0),
    )
    assert peach.shape == (64, 32, 4)
    assert bowser.shape == (64, 32, 4)
    assert peach.dtype == np.uint8
    assert bowser.dtype == np.uint8
    assert np.unique(peach.reshape(-1, 4), axis=0).shape[0] > 80
    assert np.unique(bowser.reshape(-1, 4), axis=0).shape[0] > 80
    assert np.abs(peach.astype(np.int16) - bowser.astype(np.int16)).mean() > 30
    # Peach is deliberately pink / gold biased; Bowser is green / red biased.
    assert peach[..., 0].mean() > peach[..., 1].mean()
    assert bowser[..., 1].mean() > peach[..., 1].mean() * 0.60
    assert FAKEOUT_PORTRAIT_FILES['levels/castle_inside/5.rgba16.png'] == 'peach'
    assert FAKEOUT_PORTRAIT_FILES['levels/castle_inside/6.rgba16.png'] == 'bowser'


def test_bowser_named_parts_are_visually_differentiated():
    shell = render_bowser_peach_texture(
        'actors/bowser/bowser_shell.rgba16.png',
        (32, 32, 4),
        np.random.RandomState(0),
    )
    chest = render_bowser_peach_texture(
        'actors/bowser/bowser_chest.rgba16.png',
        (32, 32, 4),
        np.random.RandomState(0),
    )
    hair = render_bowser_peach_texture(
        'actors/bowser/bowser_hair.rgba16.png',
        (64, 32, 4),
        np.random.RandomState(0),
    )
    eye = render_bowser_peach_texture(
        'actors/bowser/bowser_eye_center_0.rgba16.png',
        (32, 64, 4),
        np.random.RandomState(0),
    )
    assert shell[..., 1].mean() > shell[..., 0].mean()
    assert chest[..., 0].mean() > chest[..., 1].mean()
    assert hair[..., 0].mean() > hair[..., 1].mean() * 2
    assert eye[..., :3].std() > 20
    assert np.abs(shell.astype(np.int16) - chest.astype(np.int16)).mean() > 25


def test_peach_named_parts_are_visually_differentiated():
    dress = render_bowser_peach_texture(
        'actors/peach/peach_dress.rgba16.png',
        (32, 32, 4),
        np.random.RandomState(0),
    )
    eye = render_bowser_peach_texture(
        'actors/peach/peach_eye_open.rgba16.png',
        (32, 32, 4),
        np.random.RandomState(0),
    )
    jewel = render_bowser_peach_texture(
        'actors/peach/peach_crown_jewel.rgba16.png',
        (16, 16, 4),
        np.random.RandomState(0),
    )
    assert dress[..., 0].mean() > dress[..., 1].mean()
    assert eye[..., 2].max() > 180
    assert jewel[..., 2].mean() > jewel[..., 0].mean()
    assert np.abs(dress.astype(np.int16) - eye.astype(np.int16)).mean() > 20


def test_bowser_flame_frames_have_transparency_and_animation_difference():
    frame0 = render_bowser_peach_texture(
        'actors/bowser_flame/bowser_flame_0.rgba16.png',
        (64, 64, 4),
        np.random.RandomState(0),
    )
    frame7 = render_bowser_peach_texture(
        'actors/bowser_flame/bowser_flame_7.rgba16.png',
        (64, 64, 4),
        np.random.RandomState(0),
    )
    assert frame0[..., 3].min() == 0
    assert frame0[..., 3].max() > 200
    assert frame7[..., 3].min() == 0
    assert np.abs(frame0.astype(np.int16) - frame7.astype(np.int16)).mean() > 3
