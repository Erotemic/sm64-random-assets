#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
"""
Forward to the real main script for backwards comaptability
"""
from sm64_random_assets.cli import generate


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/sm64-random-assets/generate_assets.py --dst ~/code/sm64-random-assets/tpl/sm64-port
        cd ~/code/sm64-random-assets/tpl/sm64-port
        make VERSION=us -j16
        build/us_pc/sm64.us
    """
    generate.__cli__.main()
