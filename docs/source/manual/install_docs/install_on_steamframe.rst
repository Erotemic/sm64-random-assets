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

The Steam Frame preset defaults to ``sm64ex``. This is deliberate: ``sm64ex``
uses SDL2 for its Linux window, audio, and controller backends, whereas the
older ``sm64-port`` Linux frontend uses GLX. The variant remains independently
overridable for diagnostics:

.. code:: bash

    PRESET=steamframe VARIANT=sm64-port ./build.sh

For ARM64 Frame builds the ``sm64ex`` compile pins ``TARGET_ARCH=armv8-a`` and
explicitly selects ``RENDER_API=GL``, ``WINDOW_API=SDL2``, ``AUDIO_API=SDL2``,
and ``CONTROLLER_API=SDL2``. This avoids deriving ``-march=native`` from the
QEMU build environment and makes the intended frontend explicit.

The build runs in Valve's ARM64 Steam Runtime 3 (Sniper) SDK container. On an
x86_64 build host Docker needs ARM64 ``binfmt``/QEMU support so it can execute
the ARM64 SDK image. Configure that once with:

.. code:: bash

    ./dev/setup_docker_binfmt.sh arm64

This is host-side build support only. No compiler, QEMU, or development
packages need to be installed on the Steam Frame. The build checks Docker's
supported platforms before starting and reports this setup command instead of
failing later with ``exec /bin/sh: exec format error``.

The Sniper SDK is based on Debian 11 (Bullseye). Since Bullseye LTS ended,
Debian's live ``bullseye-security`` repository can temporarily expose stale
indexes whose referenced package files have already been removed. The build
therefore pins Debian security packages to the final 2026-09-03 snapshot used
for this EOL transition. This makes the SDK image build reproducible instead of
depending on the state of the live Bullseye security mirror.

The snapshot can be overridden for diagnostics without changing the Dockerfile:

.. code:: bash

    STEAMRT_DEBIAN_SECURITY_SNAPSHOT=20260903T220410Z PRESET=steamframe ./build.sh

Normal builds should leave this at its default.

Asset source modes
==================

The device preset does not force asset generation. Asset provenance is selected
independently:

.. code:: bash

    # Default when no baserom is supplied: run sm64-random-assets, then compile
    PRESET=steamframe ./build.sh

    # Compile assets already present in tpl/<variant> without invoking the generator
    PRESET=steamframe ASSET_MODE=reuse ./build.sh

    # Supplying a baserom selects baserom mode by default. The random asset
    # generator is not invoked.
    PRESET=steamframe BASEROM_FPATH=/path/to/baserom.us.z64 ./build.sh

``ASSET_MODE=baserom`` first runs the selected variant's upstream
``extract_assets.py --clean`` and then re-extracts ``us`` assets from the ROM.
This cleanup is required because upstream extraction intentionally leaves
existing compatible assets alone; without it, randomized PNG/audio/binary
assets from an earlier build could survive a later baserom build. The
``sm64_random_assets`` generator is never invoked in baserom mode.

If ``baserom.us.z64`` is already present in the variant tree, set
``ASSET_MODE=baserom`` without ``BASEROM_FPATH``. ``BASEROM_FPATH`` always means
baserom-only: combining it with ``ASSET_MODE=generate`` or ``reuse`` is an error.
To provide a ROM only to ``BUILD_REFERENCE=1`` while continuing to generate
randomized assets, use the legacy ``EXTERNAL_ROM_FPATH`` input instead.

Native SM64 helper tools such as ``textconv`` are architecture-specific but
live outside the normal ``build/`` directory. Steam Runtime builds therefore
clean and rebuild those helpers inside the target container before use; this
prevents stale x86_64 helpers from being reused during ARM64 builds.

The low-level configuration selected by the preset is:

.. code:: bash

    TARGET=steamrt3-aarch64

``TARGET`` can be used directly when scripting, but ``PRESET=steamframe`` is
preferred for interactive use.

Deploy
======

The default Frame artifact is:

.. code:: text

    tpl/sm64ex/build/us_pc/sm64.us.f3dex2e

Upload that native Linux binary to the Steam Frame with the SteamOS Devkit
Client and select ``Steam Linux Runtime 3.0 ARM64 (Sniper)`` as the runtime.
``EXTERNAL_DATA=0`` remains the upstream default, so a separate resource pack
is not required for this baseline build.

Python used during the target build
-----------------------------------

The Sniper SDK's system Python is deliberately not used for asset generation.
The build image installs ``uv`` as a standalone target-architecture binary and
uses it to provision Python 3.12 inside the Steam Runtime container.  This keeps
asset generation and native compilation in one hermetic ARM64 build environment
while avoiding Sniper's older Bullseye Python 3.9.

The default matches the Python versions exercised by this project's CI and can
be overridden for diagnostics, for example::

    STEAMRT_PYTHON_VERSION=3.13 PRESET=steamframe ./build.sh

The system Python in the Steam Runtime image is left untouched.
