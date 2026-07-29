import numpy as np

from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking.environment_textures import (
    render_environment_texture,
    resolve_environment_motif,
)
from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking.pil_textures import (
    _CASTLE_PORTRAIT_LAYOUTS,
    _render_castle_portrait_rgba,
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
    assert classify_texture_subject('levels/bob/0.rgba16.png') == 'grass'
    assert classify_texture_subject('levels/castle_inside/17.rgba16.png') == 'portrait'
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
    bob_portrait_top = analyze_texture_intent('levels/castle_inside/17.rgba16.png')
    bob_portrait_bottom = analyze_texture_intent('levels/castle_inside/18.rgba16.png')
    assert bob_portrait_top.role == 'portrait'
    assert bob_portrait_top.motif == 'castle_portrait_bobomb_battlefield_top'
    assert bob_portrait_bottom.motif == 'castle_portrait_bobomb_battlefield_bottom'


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



def test_castle_portrait_intents_cover_every_supported_texture():
    for fname in sorted(_CASTLE_PORTRAIT_LAYOUTS):
        intent = analyze_texture_intent(fname)
        assert intent.role == 'portrait'
        assert intent.motif.startswith('castle_portrait_')


def test_render_castle_portrait_split_pair_and_singles():
    top = _render_castle_portrait_rgba('levels/castle_inside/17.rgba16.png', (32, 64, 4))
    bottom = _render_castle_portrait_rgba('levels/castle_inside/18.rgba16.png', (32, 64, 4))
    tiny = _render_castle_portrait_rgba('levels/castle_inside/29.rgba16.png', (32, 32, 4))
    huge = _render_castle_portrait_rgba('levels/castle_inside/30.rgba16.png', (32, 32, 4))
    assert top.shape == (32, 64, 4)
    assert bottom.shape == (32, 64, 4)
    assert tiny.shape == (32, 32, 4)
    assert huge.shape == (32, 32, 4)
    assert np.any(top[..., :3] != bottom[..., :3])
    assert np.any(tiny[..., :3] != huge[..., :3])
    assert top[..., 3].mean() > 200
    assert huge[..., 3].mean() > 200


def test_render_all_castle_portraits_are_nontrivial():
    shapes = {'top': (32, 64, 4), 'bottom': (32, 64, 4), 'full': (32, 32, 4)}
    for fname, (_, segment) in sorted(_CASTLE_PORTRAIT_LAYOUTS.items()):
        rgba = _render_castle_portrait_rgba(fname, shapes[segment])
        assert rgba.dtype == np.uint8
        assert rgba.shape == shapes[segment]
        assert np.unique(rgba[..., :3].reshape(-1, 3), axis=0).shape[0] > 24


def test_render_bobomb_battlefield_portrait_is_scenic():
    top = render_pil_texture('levels/castle_inside/17.rgba16.png', (32, 64, 4), np.random.RandomState(0))
    bottom = render_pil_texture('levels/castle_inside/18.rgba16.png', (32, 64, 4), np.random.RandomState(0))
    full = np.concatenate([top, bottom], axis=0)
    assert top.shape == (32, 64, 4)
    assert bottom.shape == (32, 64, 4)
    assert full.shape == (64, 64, 4)
    assert (top[:, :, 2] > top[:, :, 1]).mean() > 0.20
    assert bottom[:, :, 1].mean() > bottom[:, :, 2].mean() * 0.60
    assert (bottom[:, :, 0] < 70).mean() > 0.03
    assert (bottom[:, :, 0] > 150).mean() > 0.03
    assert np.unique(full.reshape(-1, 4), axis=0).shape[0] > 100
    assert np.abs(top.astype(int) - bottom.astype(int)).mean() > 15



def test_environment_texture_resolution_targets_early_level_families():
    assert resolve_environment_motif('levels/castle_grounds/0.rgba16.png') == 'castle_lawn'
    assert resolve_environment_motif('levels/jrb/1.rgba16.png') == 'sea_water'
    assert resolve_environment_motif('textures/generic/bob_textures.00000.rgba16.png') == 'battlefield_grass'
    assert resolve_environment_motif('textures/outside/castle_grounds_textures.0BC00.ia16.png') == 'hedge_alpha'


def test_environment_texture_rendering_emphasizes_blue_water_green_grass_and_alpha_masks():
    lawn = render_environment_texture('levels/castle_grounds/0.rgba16.png', (32, 64, 4), np.random.RandomState(0))
    water = render_environment_texture('levels/castle_grounds/1.rgba16.png', (32, 64, 4), np.random.RandomState(0))
    hedge = render_environment_texture('levels/castle_grounds/5.ia8.png', (32, 64, 2), np.random.RandomState(0))
    fence = render_environment_texture('levels/wf/5.ia8.png', (16, 16, 2), np.random.RandomState(0))
    ice = render_environment_texture('levels/ccm/9.ia16.png', (32, 32, 2), np.random.RandomState(0))
    assert lawn[:, :, 1].mean() > lawn[:, :, 0].mean()
    assert water[:, :, 2].mean() > water[:, :, 1].mean() > water[:, :, 0].mean()
    assert hedge[:, :, 1].max() > 0
    assert hedge[:, :, 1].min() == 0
    assert fence[:, :, 1].min() == 0
    assert fence[:, :, 1].max() > 0
    assert ice[:, :, 1].max() > ice[:, :, 1].min()


def test_environment_texture_bank_members_are_nontrivial():
    bob = render_environment_texture('textures/generic/bob_textures.01000.rgba16.png', (32, 32, 4), np.random.RandomState(0))
    water = render_environment_texture('textures/water/jrb_textures.00800.rgba16.png', (32, 64, 4), np.random.RandomState(0))
    outside = render_environment_texture('textures/outside/castle_grounds_textures.02000.rgba16.png', (64, 32, 4), np.random.RandomState(0))
    assert np.unique(bob.reshape(-1, 4), axis=0).shape[0] > 24
    assert np.unique(water.reshape(-1, 4), axis=0).shape[0] > 24
    assert np.unique(outside.reshape(-1, 4), axis=0).shape[0] > 24
