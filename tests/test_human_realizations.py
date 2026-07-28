import hashlib
import pytest

pytest.importorskip('kwimage')

from sm64_random_assets.util import util_random
from sm64_random_assets.image_realizations.human_joncrall import random as human_random
from sm64_random_assets.image_realizations.human_joncrall import semantic as human_semantic


def _hash_array(arr):
    return hashlib.sha256(memoryview(arr).tobytes()).hexdigest()


def test_random_realization_is_deterministic():
    fname = 'actors/blue_coin_switch/blue_coin_switch_side.rgba16.png'
    shape = (16, 32, 4)
    rng1 = util_random.ensure_rng(fname)
    rng2 = util_random.ensure_rng(fname)
    arr1 = human_random.generate_random_image_data(fname, shape, rng1)
    arr2 = human_random.generate_random_image_data(fname, shape, rng2)
    assert _hash_array(arr1) == _hash_array(arr2)


def test_semantic_power_meter_is_deterministic():
    fname = 'actors/power_meter/power_meter_five_segments.rgba16.png'
    shape = (64, 64, 4)
    rng1 = util_random.ensure_rng(fname)
    rng2 = util_random.ensure_rng(fname)
    arr1 = human_semantic.generate_semantic_image_data(fname, shape, rng1)
    arr2 = human_semantic.generate_semantic_image_data(fname, shape, rng2)
    assert _hash_array(arr1) == _hash_array(arr2)
