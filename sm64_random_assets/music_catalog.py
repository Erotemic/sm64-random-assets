from __future__ import annotations

from pathlib import PurePosixPath

from sm64_random_assets.realizations import AssetIdentity


def determine_binary_identity(info_or_fname):
    if isinstance(info_or_fname, dict):
        fname = str(info_or_fname['fname'])
    else:
        fname = str(info_or_fname)
    path = PurePosixPath(fname)
    if path.suffix == '.m64':
        return AssetIdentity(
            fname=fname,
            family='music.sequence',
            member=path.stem,
        )
    return AssetIdentity(
        fname=fname,
        family='binary.raw',
        member=path.name,
    )


__all__ = ['determine_binary_identity']
