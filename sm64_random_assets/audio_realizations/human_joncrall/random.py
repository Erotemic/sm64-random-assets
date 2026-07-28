from __future__ import annotations

import numpy as np


def generate_random_sample(fname, params, rng, identity=None):
    """The original full-range random PCM strategy."""
    size = int(params.nframes) * int(params.nchannels)
    return rng.randint(-32768, 32767, size, dtype=np.int16)


__all__ = ['generate_random_sample']
