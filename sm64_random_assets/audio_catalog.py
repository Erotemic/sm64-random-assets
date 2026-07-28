from __future__ import annotations

from pathlib import PurePosixPath

from sm64_random_assets.realizations import AssetIdentity


def determine_audio_identity(info_or_fname) -> AssetIdentity:
    """Group related samples by their sound-bank directory."""
    if isinstance(info_or_fname, dict):
        fname = str(info_or_fname['fname'])
    else:
        fname = str(info_or_fname)
    path = PurePosixPath(fname)
    parent_name = path.parent.name or 'misc'
    family = f'audio.bank.{parent_name}'
    return AssetIdentity(fname=fname, family=family, member=path.stem)


__all__ = ['determine_audio_identity']
