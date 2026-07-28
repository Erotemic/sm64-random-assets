from __future__ import annotations

import numpy as np
import kwimage


def generate_random_image_data(fname, shape, rng, identity=None):
    """Original fully random fallback preserved as a stable realization."""
    shape = tuple(shape)
    if len(shape) == 3 and shape[2] == 2:
        shape = tuple(shape)

    if str(fname).endswith('.ia1.png'):
        new_data = (rng.rand(*shape) * 255).astype(np.uint8)
    elif str(fname).endswith('.ia4.png'):
        new_data = (rng.rand(*shape) * 255).astype(np.uint8)
    elif str(fname).endswith('.ia8.png'):
        new_data = (rng.rand(*shape) * 255).astype(np.uint8)
        new_data[new_data < 127] = 0
        new_data[new_data >= 127] = 255
        new_data[:] = 0
    elif str(fname).endswith('.ia16.png'):
        new_data = (rng.rand(*shape) * 255).astype(np.uint8)
    elif str(fname).endswith('.rgba16.png'):
        new_data = (rng.rand(*shape) * 255).astype(np.uint8)
    else:
        new_data = (rng.rand(*shape) * 255).astype(np.uint8)

    smaller = kwimage.imresize(new_data, scale=0.5, interpolation='nearest')
    new_data = kwimage.imresize(smaller, dsize=shape[0:2][::-1], interpolation='nearest')
    return new_data


__all__ = ['generate_random_image_data']
