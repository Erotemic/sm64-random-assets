from __future__ import annotations


def generate_zero_binary(output_dpath, info, rng=None, identity=None):
    size = info.get('size', None)
    if size is None:
        return None
    return b'\x00' * int(size)


__all__ = ['generate_zero_binary']
