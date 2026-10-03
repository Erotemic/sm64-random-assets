Steam Frame Instructions
------------------------

Steam Frame is represented as a build preset, not as a special SM64 codebase.
The preset selects the ARM64 Steam Linux Runtime 3 target while ``VARIANT``
continues to select the SM64 implementation.

Build Off-Device
================

From an x86_64 or ARM64 Linux development machine with Docker and Docker
Buildx installed:

.. code:: bash

    PRESET=steamframe ./build.sh

The default variant is ``sm64-port``. Other native variants can use the same
preset:

.. code:: bash

    PRESET=steamframe VARIANT=sm64ex ./build.sh

The build runs in Valve's ARM64 Steam Runtime 3 (Sniper) SDK container. On an
x86_64 build host Docker needs ARM64 ``binfmt``/QEMU support so it can execute
the ARM64 SDK image. Configure that once with:

.. code:: bash

    ./dev/setup_docker_binfmt.sh arm64

This is host-side build support only. No compiler, QEMU, or development
packages need to be installed on the Steam Frame. The build checks Docker's
supported platforms before starting and reports this setup command instead of
failing later with ``exec /bin/sh: exec format error``.

The low-level configuration selected by the preset is:

.. code:: bash

    TARGET=steamrt3-aarch64

``TARGET`` can be used directly when scripting, but ``PRESET=steamframe`` is
preferred for interactive use.

Deploy
======

Upload the produced native Linux binary to the Steam Frame with the SteamOS
Devkit Client and select ``Steam Linux Runtime 3.0 ARM64 (Sniper)`` as the
runtime.
