import pytest

pytest.importorskip('kwimage')

import numpy as np

from sm64_random_assets.image_catalog import determine_asset_identity
from sm64_random_assets.image_realizations.human_joncrall import semantic as human_semantic
from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking.castle_inside_textures import (
    CASTLE_INSIDE_TEXTURE_SPECS,
    render_castle_inside_texture,
    supports_castle_inside_texture,
)
from sm64_random_assets.generators import image_generator


def test_castle_inside_texture_supports_and_renders_expected_shape():
    for fname, kind in CASTLE_INSIDE_TEXTURE_SPECS.items():
        identity = determine_asset_identity(fname)
        assert supports_castle_inside_texture(identity, {'fname': fname})
        channels = 4 if fname.endswith('.rgba16.png') else 2
        shape = (32, 32, channels)
        arr = render_castle_inside_texture(fname, shape)
        assert arr.shape == shape
        assert arr.dtype == np.uint8
        assert arr.std() > 0


def test_castle_inside_texture_renders_wide_shapes_without_crashing():
    # Some castle interior assets are wider than tall in the real game; the
    # internal 64x64 canvas must resize cleanly to wide targets as well.
    shape = (16, 64, 4)
    arr = render_castle_inside_texture('levels/castle_inside/1.rgba16.png', shape)
    assert arr.shape == shape
    assert arr.dtype == np.uint8
    assert arr.std() > 0


def test_default_registry_uses_castle_inside_realization_for_material_tiles():
    policy = image_generator.build_realization_policy(target_quality=1.0)
    info = {'fname': 'levels/castle_inside/3.rgba16.png', 'shape': [64, 32, 4]}
    identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
    realization = policy.resolve(identity, info)
    assert realization.id == 'openai.castle-inside-textures'
    assert realization.estimated_quality == 0.89
