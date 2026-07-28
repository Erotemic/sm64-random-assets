from sm64_random_assets.realizations import (
    AssetIdentity,
    AssetRealization,
    RealizationPolicy,
    RealizationRegistry,
)


def _dummy_generator(fname, shape, rng, identity):
    return object()


def test_registry_allows_same_id_across_versions():
    registry = RealizationRegistry()
    registry.register(AssetRealization(
        id='human.semantic', author='human:joncrall', version=1,
        estimated_quality=0.6, generator=_dummy_generator))
    registry.register(AssetRealization(
        id='human.semantic', author='human:joncrall', version=2,
        estimated_quality=0.75, generator=_dummy_generator))
    assert len(list(registry.iter_candidates(AssetIdentity('x', 'x'), {}))) == 2


def test_choose_nearest_quality_tiebreaks_to_higher_quality_and_version():
    registry = RealizationRegistry()
    registry.register(AssetRealization(
        id='a', author='human:joncrall', version=1,
        estimated_quality=0.4, generator=_dummy_generator))
    registry.register(AssetRealization(
        id='b', author='human:joncrall', version=1,
        estimated_quality=0.6, generator=_dummy_generator))
    chosen = registry.choose(AssetIdentity('x', 'fam'), {}, target_quality=0.5)
    assert chosen.id == 'b'

    registry = RealizationRegistry()
    registry.register(AssetRealization(
        id='same', author='human:joncrall', version=1,
        estimated_quality=0.6, generator=_dummy_generator))
    registry.register(AssetRealization(
        id='same', author='human:joncrall', version=2,
        estimated_quality=0.6, generator=_dummy_generator))
    chosen = registry.choose(AssetIdentity('x', 'fam'), {}, target_quality=0.6)
    assert chosen.version == 2


def test_author_filtering():
    registry = RealizationRegistry()
    registry.register(AssetRealization(
        id='a', author='human:joncrall', version=1,
        estimated_quality=0.2, generator=_dummy_generator))
    registry.register(AssetRealization(
        id='b', author='openai:gpt', version=1,
        estimated_quality=0.9, generator=_dummy_generator))
    chosen = registry.choose(
        AssetIdentity('x', 'fam'), {}, target_quality=1.0,
        include_authors=['human:*'], exclude_authors=[])
    assert chosen.author == 'human:joncrall'


def test_family_selection_cached_once_per_family():
    registry = RealizationRegistry()
    registry.register(AssetRealization(
        id='low', author='human:joncrall', version=1,
        estimated_quality=0.0, generator=_dummy_generator,
        families=frozenset({'fam'})))
    registry.register(AssetRealization(
        id='high', author='human:joncrall', version=1,
        estimated_quality=0.8, generator=_dummy_generator,
        families=frozenset({'fam'})))
    policy = RealizationPolicy(registry=registry, target_quality=1.0)
    a = policy.resolve(AssetIdentity('one', 'fam', 'm1'), {})
    b = policy.resolve(AssetIdentity('two', 'fam', 'm2'), {})
    assert a is b
    assert a.id == 'high'
