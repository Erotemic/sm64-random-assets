Steam Deck Instructions
-----------------------

Steam Deck is represented as a build preset. The preset selects the x86_64
Steam Linux Runtime 3 target while ``VARIANT`` selects the SM64 implementation.
This keeps device names out of the low-level compiler configuration.

Build Off-Device
================

From a Linux development machine with Docker and Docker Buildx installed:

.. code:: bash

    PRESET=steamdeck ./build.sh

The default variant is ``sm64-port``. Another native variant can be selected
independently:

.. code:: bash

    PRESET=steamdeck VARIANT=sm64ex ./build.sh

The low-level target selected by the preset is:

.. code:: bash

    TARGET=steamrt3-x86_64

The old SteamOS-specific Docker recipes remain in ``dockerfiles/`` for
historical reference, but the preset-driven Steam Runtime build is the
preferred path.

Deploy
======

Copy the resulting build to the Steam Deck as before. For example, if the Deck
is reachable as ``steamdeck`` over SSH, ``rsync`` can be used to copy the build
output into a game directory under the user's home directory.
