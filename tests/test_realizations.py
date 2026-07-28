import pytest

from sm64_random_assets.realizations import AssetRealization
from sm64_random_assets.realizations import NoMatchingRealizationError
from sm64_random_assets.realizations import RealizationPolicy
from sm64_random_assets.realizations import RealizationRegistry


def _noop(*args, **kwargs):
    return None


def test_registry_uses_closest_quality_then_newest_version():
    registry = RealizationRegistry('demo')
    registry.register(AssetRealization(
        id='human-random-v1',
        author='human:joncrall',
        estimated_quality=0.0,
        version=1,
        generator=_noop,
    ))
    registry.register(AssetRealization(
        id='model-v1',
        author='openai:gpt-5.6-thinking',
        estimated_quality=0.8,
        version=1,
        generator=_noop,
    ))
    registry.register(AssetRealization(
        id='model-v2',
        author='openai:gpt-5.6-thinking',
        estimated_quality=0.8,
        version=2,
        generator=_noop,
    ))

    ranked = registry.require_ranked(
        {'fname': 'demo.png'},
        RealizationPolicy(target_quality=0.75),
    )
    assert [item.id for item in ranked] == [
        'model-v2', 'model-v1', 'human-random-v1']


def test_registry_author_filters():
    registry = RealizationRegistry('demo')
    registry.register(AssetRealization(
        id='human',
        author='human:joncrall',
        estimated_quality=0.2,
        version=1,
        generator=_noop,
    ))
    registry.register(AssetRealization(
        id='model',
        author='openai:gpt-5.6-thinking',
        estimated_quality=0.9,
        version=1,
        generator=_noop,
    ))

    human_only = RealizationPolicy(
        target_quality=1.0,
        include_authors=('human:*',),
    )
    assert registry.require_ranked({'fname': 'x'}, human_only)[0].id == 'human'

    no_models = RealizationPolicy(
        target_quality=1.0,
        exclude_authors=('openai:*',),
    )
    assert registry.require_ranked({'fname': 'x'}, no_models)[0].id == 'human'

    with pytest.raises(NoMatchingRealizationError):
        registry.require_ranked(
            {'fname': 'x'},
            RealizationPolicy(include_authors=('anthropic:*',)),
        )


def test_source_dependent_realizations_are_rejected():
    with pytest.raises(ValueError, match='cannot use source assets'):
        AssetRealization(
            id='derived',
            author='example:model',
            estimated_quality=0.9,
            version=1,
            generator=_noop,
            source_assets_used=True,
        )
