#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
"""
Module entry point
"""
from sm64_random_assets.main import main


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/sm64-random-assets/generate_assets.py --dst ~/code/sm64-port-safe
        cd ~/code/sm64-port-safe
        make VERSION=us -j16
        build/us_pc/sm64.us
    """
    main()
