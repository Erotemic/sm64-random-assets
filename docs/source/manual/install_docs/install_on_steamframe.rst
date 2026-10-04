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
    PRESET=steamframe BASEROM_FPATH=baserom.us.z64 ./build.sh

``ASSET_MODE=baserom`` never invokes ``sm64_random_assets`` and does not clean
the randomized variant checkout. Instead it creates a persistent sibling
checkout such as ``tpl/sm64ex-baserom``. Original assets extracted there are
cached across builds, so switching between randomized and baserom builds does
not destroy either asset cache. Upstream ``extract_assets.py`` already records
its extraction revision in ``.assets-local.txt`` and returns immediately when
all required assets are current, so no additional destructive cleanup is
needed.

The build script never deletes the ``*-baserom`` checkout. Remove or rename it
manually only if you intentionally want to discard that cache.

The Steam Runtime wrapper resolves and validates an explicit baserom before it
builds the Docker image. The normal executable example,
``BASEROM_FPATH=baserom.us.z64``, resolves to the repository file and is visible
inside the container as ``/work/baserom.us.z64`` through the existing repository
bind mount. Files outside the repository are mounted read-only under ``/inputs``.
The wrapper prints ``BASEROM_HOST_FPATH`` and ``BASEROM_CONTAINER_FPATH`` so the
handoff is visible in build logs. It also passes an independent baserom-required
marker; if the path or mount is missing inside the container, the inner build
fails instead of defaulting to ``ASSET_MODE=generate``.

If ``baserom.us.z64`` is already present in the normal variant tree, set
``ASSET_MODE=baserom`` without ``BASEROM_FPATH``. ``BASEROM_FPATH`` always means
baserom-only: combining it with ``ASSET_MODE=generate`` or ``reuse`` is an error.
To provide a ROM only to ``BUILD_REFERENCE=1`` while continuing to generate
randomized assets, use the legacy ``EXTERNAL_ROM_FPATH`` input instead.

Native SM64 helper tools such as ``textconv`` are architecture-specific but
live outside the normal ``build/`` directory. The build checks their ELF
architecture and only runs ``make -C tools clean`` when an existing helper was
built for the wrong ISA. Thus an x86_64-to-ARM64 switch is repaired without
throwing away correctly built ARM64 helper tools on every subsequent build.

The low-level configuration selected by the preset is:

.. code:: bash

    TARGET=steamrt3-aarch64

``TARGET`` can be used directly when scripting, but ``PRESET=steamframe`` is
preferred for interactive use.

Deploy with SteamOS Devkit Client
=================================

The default Frame artifact is:

.. code:: text

    tpl/sm64ex/build/us_pc/sm64.us.f3dex2e

The build SDK and the launch runtime are separate choices. The repository
currently compiles the ARM64 binary inside Valve's Steam Runtime 3 (Sniper) SDK
container, but on the tested Steam Frame the Devkit title must be launched with
``Steam Linux Runtime 4.0 ARM64``. Do not select the Runtime 3.0 ARM64 launch
runtime just because the build target is named ``steamrt3-aarch64``.

A working Devkit deployment is:

#. Enable Developer Mode on the Steam Frame and pair it with the SteamOS Devkit
   Client on the development machine.
#. Open ``Title Upload`` in the Devkit Client.
#. Use the build output directory as the local folder:

   .. code:: text

       tpl/sm64ex/build/us_pc

#. Use this start command:

   .. code:: text

       sm64.us.f3dex2e

#. Select ``Steam Linux Runtime 4.0 ARM64`` as the runtime.
#. Upload the title. It should appear in the Frame library as a Devkit /
   non-Steam title and can then be launched from the normal Steam UI.

``EXTERNAL_DATA=0`` remains the upstream default, so a separate resource pack
is not required for this baseline build. SDL2 sees Steam's virtual gamepad when
the title is launched through Steam, including haptics / rumble support.

Troubleshooting Devkit launch
-----------------------------

If pressing Play briefly changes the button to Resume and then immediately back
to Play, first verify the selected runtime. With the wrong runtime the Steam
logs can show:

.. code:: text

    Invalid or Unsupported elf file.
    This is likely due to a misconfigured x86-64 RootFS
    Current RootFS path set to ''
    RootFS path doesn't exist. This is required on AArch64 hosts
    Use FEXRootFSFetcher to download a RootFS

For a binary that ``file`` identifies as ARM AArch64, this message means Steam
tried to route the native ARM64 executable through FEX instead of launching it
natively. On the tested Frame, changing the Devkit title runtime to
``Steam Linux Runtime 4.0 ARM64`` fixes that launch-path problem. Also make sure
Steam is not forcing an x86 compatibility tool for the Devkit title.

The ``LD_PRELOAD`` warnings about x86/x86_64 ``gameoverlayrenderer.so`` can
appear around the same launch attempt; they are not the decisive failure. The
FEX ``Invalid or Unsupported elf file`` / missing x86-64 RootFS message is the
useful signature for a wrong launch runtime.

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
