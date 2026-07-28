import numpy as np
import pytest
import ubelt as ub

from sm64_random_assets.generators.image_generator import generate_image
from sm64_random_assets.realizations import NoMatchingRealizationError
from sm64_random_assets.realizations import RealizationPolicy


def test_quality_lever_selects_random_or_semantic(tmp_path):
    info = {
        'fname': 'actors/blue_coin_switch/blue_coin_switch_side.rgba16.png',
        'shape': [16, 32, 4],
    }
    root = ub.Path(tmp_path)

    random_out = generate_image(
        root / 'random',
        info,
        realization_policy=RealizationPolicy(target_quality=0.0),
    )
    semantic_out = generate_image(
        root / 'semantic',
        info,
        realization_policy=RealizationPolicy(target_quality=1.0),
    )

    assert random_out['realization_id'] == 'human.random-v1'
    assert random_out['realization_author'] == 'human:joncrall'
    assert random_out['realization_version'] == 1
    assert random_out['status'] == 'randomized'

    assert semantic_out['realization_id'] == 'human.semantic-v1'
    assert semantic_out['realization_author'] == 'human:joncrall'
    assert semantic_out['realization_version'] == 1
    assert semantic_out['status'] == 'generated'

    import kwimage
    random_image = kwimage.imread(random_out['out_fpath'])
    semantic_image = kwimage.imread(semantic_out['out_fpath'])
    assert random_image.shape == semantic_image.shape == (16, 32, 4)
    assert not np.array_equal(random_image, semantic_image)


def test_random_realization_remains_deterministic(tmp_path):
    info = {
        'fname': 'textures/example/example.rgba16.png',
        'shape': [16, 16, 4],
    }
    root = ub.Path(tmp_path)
    policy = RealizationPolicy(target_quality=0.0)
    out1 = generate_image(root / 'one', info, realization_policy=policy)
    out2 = generate_image(root / 'two', info, realization_policy=policy)
    assert out1['out_fpath'].read_bytes() == out2['out_fpath'].read_bytes()


def test_author_filter_can_preserve_or_exclude_human_code(tmp_path):
    info = {
        'fname': 'textures/example/example.rgba16.png',
        'shape': [8, 8, 4],
    }
    root = ub.Path(tmp_path)

    human_policy = RealizationPolicy(
        target_quality=1.0,
        include_authors=('human:joncrall',),
    )
    out = generate_image(root / 'human', info, realization_policy=human_policy)
    assert out['realization_author'] == 'human:joncrall'

    with pytest.raises(NoMatchingRealizationError):
        generate_image(
            root / 'model-only',
            info,
            realization_policy=RealizationPolicy(
                target_quality=1.0,
                include_authors=('openai:*',),
            ),
        )
