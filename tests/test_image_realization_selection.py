import pytest

pytest.importorskip('kwimage')

from sm64_random_assets.generators import image_generator
from sm64_random_assets.image_catalog import determine_asset_identity
from sm64_random_assets.image_realizations.human_joncrall import semantic as human_semantic


def test_default_registry_prefers_semantic_for_power_meter_at_high_quality():
    policy = image_generator.build_realization_policy(target_quality=1.0)
    info = {'fname': 'actors/power_meter/power_meter_full.rgba16.png', 'shape': [64, 64, 4]}
    identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
    realization = policy.resolve(identity, info)
    assert realization.id == 'human.semantic'


def test_validate_generated_image_enforces_shape_and_dtype():
    import numpy as np
    img = np.ones((8, 8, 1), dtype=np.float32)
    fixed = image_generator.validate_generated_image(img, (8, 8, 4))
    assert fixed.shape == (8, 8, 4)
    assert fixed.dtype == np.uint8
