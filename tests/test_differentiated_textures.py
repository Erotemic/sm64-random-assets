import hashlib
import json
from pathlib import Path

import numpy as np

from sm64_random_assets.image_catalog import determine_asset_identity
from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking.differentiated_textures import (
    DIFFERENTIATED_ACTOR_FAMILIES,
    DIFFERENTIATED_ANIMATION_FAMILIES,
    render_differentiated_texture,
    supports_differentiated_texture,
)


def _metadata_items():
    fpath = Path(__file__).parents[1] / 'sm64_random_assets/rc/asset_metadata.json'
    return json.loads(fpath.read_text())


def _supported_items():
    result = []
    for info in _metadata_items():
        if not info['fname'].endswith('.png') or info.get('shape') is None:
            continue
        identity = determine_asset_identity(info)
        if supports_differentiated_texture(identity, info):
            result.append((info, identity))
    return result


def test_differentiated_texture_pass_claims_broad_named_asset_set():
    supported = _supported_items()
    families = {info['fname'].split('/')[1] for info, _ in supported}
    assert len(supported) >= 190
    assert DIFFERENTIATED_ACTOR_FAMILIES <= families
    assert DIFFERENTIATED_ANIMATION_FAMILIES <= families


def test_every_claimed_texture_renders_at_manifest_shape():
    for info, identity in _supported_items():
        shape = tuple(info['shape'])
        arr = render_differentiated_texture(
            info['fname'], shape, np.random.RandomState(0), identity)
        assert arr is not None, info['fname']
        assert arr.shape == shape, info['fname']
        assert arr.dtype == np.uint8, info['fname']
        assert np.unique(arr.reshape(-1, shape[-1]), axis=0).shape[0] > 2, info['fname']


def test_no_same_shape_files_within_claimed_family_are_byte_identical():
    hashes = {}
    for info, identity in _supported_items():
        shape = tuple(info['shape'])
        arr = render_differentiated_texture(
            info['fname'], shape, np.random.RandomState(0), identity)
        family = info['fname'].split('/')[1]
        key = (family, shape, hashlib.sha256(arr.tobytes()).hexdigest())
        assert key not in hashes, (hashes.get(key), info['fname'])
        hashes[key] = info['fname']


def test_named_actor_parts_have_strong_semantic_differences():
    cases = [
        (
            'actors/koopa/koopa_shell_back.rgba16.png',
            'actors/koopa/koopa_eyes_open.rgba16.png',
            (32, 32, 4),
        ),
        (
            'actors/piranha_plant/piranha_plant_leaf.rgba16.png',
            'actors/piranha_plant/piranha_plant_tooth.rgba16.png',
            (32, 32, 4),
        ),
        (
            'actors/chain_chomp/chain_chomp_bright_shine.rgba16.png',
            'actors/chain_chomp/chain_chomp_tongue.rgba16.png',
            (32, 32, 4),
        ),
        (
            'actors/mad_piano/mad_piano_keys.rgba16.png',
            'actors/mad_piano/mad_piano_tooth.rgba16.png',
            (32, 32, 4),
        ),
    ]
    for fname1, fname2, shape in cases:
        arr1 = render_differentiated_texture(fname1, shape, np.random.RandomState(0))
        arr2 = render_differentiated_texture(fname2, shape, np.random.RandomState(0))
        assert np.abs(arr1.astype(float) - arr2.astype(float)).mean() > 22


def test_effect_frames_change_shape_and_alpha_over_time():
    sequences = [
        ('actors/flame/flame_{}.ia16.png', 8, (32, 32, 2)),
        ('actors/explosion/explosion_{}.rgba16.png', 7, (32, 32, 4)),
        ('actors/walk_smoke/walk_smoke_{}.ia16.png', 7, (32, 32, 2)),
        ('actors/water_wave/water_wave_{}.ia16.png', 4, (32, 32, 2)),
        ('actors/yoshi_egg/yoshi_egg_{}_unused.rgba16.png', 8, (32, 32, 4)),
    ]
    for template, count, shape in sequences:
        frames = [
            render_differentiated_texture(
                template.format(idx), shape, np.random.RandomState(0))
            for idx in range(count)
        ]
        hashes = {hashlib.sha256(frame.tobytes()).hexdigest() for frame in frames}
        assert len(hashes) == count
        assert np.abs(frames[0].astype(float) - frames[-1].astype(float)).mean() > 3
        if shape[-1] in {2, 4} and 'yoshi_egg' not in template:
            assert min(frame[..., -1].min() for frame in frames) == 0
            assert max(frame[..., -1].max() for frame in frames) > 0


def test_eye_states_are_not_collapsed_together():
    names = [
        'actors/penguin/penguin_eye_open.rgba16.png',
        'actors/penguin/penguin_eye_half_closed.rgba16.png',
        'actors/penguin/penguin_eye_closed.rgba16.png',
        'actors/penguin/penguin_eye_angry.rgba16.png',
    ]
    frames = [
        render_differentiated_texture(name, (32, 32, 4), np.random.RandomState(0))
        for name in names
    ]
    assert len({hashlib.sha256(frame.tobytes()).hexdigest() for frame in frames}) == len(frames)
