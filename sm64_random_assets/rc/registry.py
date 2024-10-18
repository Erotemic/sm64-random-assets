"""
A registry of resource files bundled with the this package
"""
from importlib import resources as importlib_resources
import ubelt as ub


def requirement_path(fname):
    """
    CommandLine:
        xdoctest -m kwcoco.rc.registry requirement_path

    Example:
        >>> # xdoctest: +SKIP
        >>> from sm64_random_assets.rc.registry import requirement_path
        >>> fname = 'runtime.txt'
        >>> requirement_path(fname)
    """
    raise NotImplementedError
    with importlib_resources.path('sm64_random_assets.rc.requirements', f'{fname}') as p:
        orig_pth = ub.Path(p)
        return orig_pth


def find_resource_path(fname):
    """
    Robustly find the path to a module resource.

    CommandLine:
        xdoctest -m sm64_random_assets.rc.registry find_resource_path

    Example:
        >>> from sm64_random_assets.rc.registry import find_resource_path
        >>> print(find_resource_path('asset_metadata.json'))
    """
    with importlib_resources.path('sm64_random_assets.rc', fname) as p:
        orig_pth = ub.Path(p)
        return orig_pth
