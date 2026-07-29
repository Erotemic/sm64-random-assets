import json
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip('PIL')

from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking.frequent_textures import (
    FREQUENT_TEXTURE_SPECS,
    classify_frequent_texture,
    render_frequent_texture,
)


def test_priority_catalog_is_ordered_and_explained():
    scores = [spec.exposure_score for spec in FREQUENT_TEXTURE_SPECS]
    assert scores == sorted(scores, reverse=True)
    assert all(spec.reason for spec in FREQUENT_TEXTURE_SPECS)
    assert classify_frequent_texture('actors/mario/mario_mustache.rgba16.png').name == 'mario_details'
    assert classify_frequent_texture('actors/door/metal_door.rgba16.png').name == 'doors'
    assert classify_frequent_texture('levels/bob/0.rgba16.png') is None


@pytest.mark.parametrize('fname, shape', [
    ('actors/mario/mario_mustache.rgba16.png', (32, 32, 4)),
    ('actors/star/star_eye.rgba16.png', (32, 32, 4)),
    ('actors/tree/snowy_pine_tree.rgba16.png', (64, 32, 4)),
    ('actors/door/polished_wooden_door.rgba16.png', (64, 32, 4)),
    ('actors/exclamation_box/exclamation_box_front.rgba16.png', (32, 32, 4)),
    ('actors/smoke/smoke.ia16.png', (32, 32, 2)),
    ('actors/water_splash/water_splash_4.rgba16.png', (64, 32, 4)),
    ('actors/goomba/goomba_face.rgba16.png', (32, 32, 4)),
    ('actors/koopa_shell/koopa_shell_front.rgba16.png', (32, 32, 4)),
    ('textures/segment2/shadow_quarter_circle.ia8.png', (16, 16, 2)),
])
def test_frequent_texture_shape_dtype_and_determinism(fname, shape):
    arr1 = render_frequent_texture(fname, shape, np.random.RandomState(0))
    arr2 = render_frequent_texture(fname, shape, np.random.RandomState(0))
    assert arr1.shape == shape
    assert arr1.dtype == np.uint8
    assert np.array_equal(arr1, arr2)
    assert arr1.std() > 0


def test_semantic_outputs_are_not_generic_blobs():
    mustache = render_frequent_texture(
        'actors/mario/mario_mustache.rgba16.png', (32, 32, 4), np.random.RandomState(0))
    tree = render_frequent_texture(
        'actors/tree/pine_tree.rgba16.png', (64, 32, 4), np.random.RandomState(0))
    star = render_frequent_texture(
        'actors/star/star_eye.rgba16.png', (32, 32, 4), np.random.RandomState(0))
    splash0 = render_frequent_texture(
        'actors/water_splash/water_splash_0.rgba16.png', (64, 32, 4), np.random.RandomState(0))
    splash7 = render_frequent_texture(
        'actors/water_splash/water_splash_7.rgba16.png', (64, 32, 4), np.random.RandomState(0))

    assert (mustache[..., 3] == 0).mean() > 0.25
    assert tree[..., 1].mean() > tree[..., 0].mean()
    assert (star[..., 3] > 0).mean() < 0.45
    assert not np.array_equal(splash0, splash7)


def test_every_manifest_texture_claimed_by_frequent_pass_renders():
    manifest_fpath = Path(__file__).parents[1] / 'sm64_random_assets/rc/asset_metadata.json'
    manifest = json.loads(manifest_fpath.read_text())
    rendered = 0
    for info in manifest:
        fname = info['fname']
        shape = info.get('shape')
        if shape is None or classify_frequent_texture(fname) is None:
            continue
        arr = render_frequent_texture(fname, tuple(shape), np.random.RandomState(0))
        assert arr.shape == tuple(shape), fname
        assert arr.dtype == np.uint8, fname
        rendered += 1
    assert rendered >= 90
