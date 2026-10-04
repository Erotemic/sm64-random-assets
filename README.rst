SM64 Randomized Asset Generator
===============================

|Pypi| |PypiDownloads| |ReadTheDocs| |GithubActions| |Codecov|

+---------------+-----------------------------------------------------+
| Read the Docs | http://sm64-random-assets.readthedocs.io/en/latest/ |
+---------------+-----------------------------------------------------+
| Pypi          | https://pypi.org/project/sm64_random_assets         |
+---------------+-----------------------------------------------------+

Generates non-copyrighted randomized assets so `sm64 <https://github.com/n64decomp/sm64>`_ and `sm64-port <https://github.com/sm64-port/sm64-port>`_ can be used
for educational purposes.

This has only been tested for building the US variant, and only on Linux.

For each asset in the game, this system generates a random texture, except in special cases like text
where it is possible to generate reasonable textures with open source tools.
The result is surprisingly playable.

Future work will support configurable and procedural generation of assets.


.. image:: https://i.imgur.com/iiMPSTZ.png

.. image:: https://i.imgur.com/5OsOH1F.png

.. image:: https://i.imgur.com/yFI8WV2.png

.. image:: https://i.imgur.com/jlXDyMJ.png

Python Requirements
-------------------

To run the asset generation script, the following requirements are needed.

.. code:: bash

   pip install kwimage opencv-python-headless ubelt numpy ruamel.yaml PyYAML kwconf rich parse

   OR

   pip install -r requirements/runtime.txt



High-Exposure Texture Pass
--------------------------

At high target quality, frequently visible assets use a focused semantic
realization before the general PIL fallback.  The first pass covers Mario's
persistent detail textures, stars and coins, actor shadows, smoke / sparkle /
water-splash effects, trees, doors, common boxes and switches, signposts,
Goombas, and Koopa shells.  The prioritization table is kept in
``frequent_textures.py`` so later passes can extend it methodically.

PC Port Example Usage
---------------------

The following instructions were written on an Ubuntu 22.04 PC

.. code:: bash

    # PC Port Dependencies
    sudo apt install -y git build-essential pkg-config libusb-1.0-0-dev libsdl2-dev

    # You can set your "code" directory path - the place where you will clone
    # this repo - to be somewhere convenient for you
    CODE_DPATH=$HOME/code

    # Ensure your "code" directory exists
    mkdir -p "$CODE_DPATH"

    # Clone this repo
    git clone https://github.com/Erotemic/sm64-random-assets.git $CODE_DPATH/sm64-random-assets

    # Move into the root of this repo and initialize the sm64-port submodule,
    # which will clone the official PC port repo.
    cd "$CODE_DPATH"/sm64-random-assets
    git submodule update --init tpl/sm64-port

    # Run the asset generator
    python "$CODE_DPATH"/sm64-random-assets/generate_assets.py --dst $CODE_DPATH/sm64-random-assets/tpl/sm64-port

    # Prefer the best available human-authored semantic assets
    python "$CODE_DPATH"/sm64-random-assets/generate_assets.py --dst $CODE_DPATH/sm64-random-assets/tpl/sm64-port --target_quality=1 --include_authors "human:*"

    # Move into the PC port directory
    cd $CODE_DPATH/sm64-random-assets/tpl/sm64-port

    # Compile
    make NOEXTRACT=1 VERSION=us -j16


The compiled executable can now be run directly:

.. code:: bash

    # Run the executable
    build/us_pc/sm64.us


Headless ROM Usage
------------------

.. code:: bash

    # ROM-only dependencies
    sudo apt install -y binutils-mips-linux-gnu build-essential git libcapstone-dev pkgconf python3

    # You can set your "code" directory path - the place where you will clone
    # this repo - to be somewhere convenient for you
    CODE_DPATH=$HOME/code

    # Ensure your "code" directory exists
    mkdir -p $CODE_DPATH

    # Clone this repo
    git clone https://github.com/Erotemic/sm64-random-assets.git $CODE_DPATH/sm64-random-assets

    # Move into the root of this repo and initialize the sm64 submodule,
    # which will clone the official ROM-only sm64 repo.
    cd $CODE_DPATH/sm64-random-assets
    git submodule update --init tpl/sm64

    # Run the asset generator
    python $CODE_DPATH/sm64-random-assets/generate_assets.py --dst $CODE_DPATH/sm64-random-assets/tpl/sm64

    # Move into the ROM-only sm64 directory
    cd $CODE_DPATH/sm64-random-assets/tpl/sm64

    # Compile
    NUM_CPUS=$(nproc --all)
    NOEXTRACT=1 COMPARE=0 NON_MATCHING=0 VERSION=us make -j$NUM_CPUS

    # The compiled ROM is: build/us/sm64.us.z64

This ROM can now be flashed on an N64 cartridge, copied onto an Everdrive, or run
using an N64 emulator (like Mupen64Plus). For instance, if you have Mupen64Plus
installed (e.g. ``sudo apt install mupen64plus-qt``) you can run:

.. code:: bash

   mupen64plus build/us/sm64.us.z64


N64 Limitations
---------------

On real N64 hardware truly randomizing all textures will cause the system to
lock up. This is because the N64 has 4 megabytes of RAM, and many of the
original PNG textures are optimized to reduce their memory usage by having
large continuous sections of the same color. Naively randomizing every pixel
does not generate data well suited for PNG compression.

I have verified that I can enter every major stage and complete every Bowser
fight, so I think all of the crashes have been resolved by reducing texture
sizes. I have completed a 16 star run on real N64 hardware with this.


Development
-----------

While I'll try to keep the above instructions working / maintained, the
``build.sh`` script is the end-to-end entry point for developers. Starting from
a fresh repo, the ``build.sh`` script will take care of the entire process from
initializing submodules, generating assets, compiling the binaries, and even
running them with the PC port, in an emulator, or copying ROMs to an EverDrive.
Environment variables can be used to control the build.sh behavior.

The build configuration separates the SM64 codebase (``VARIANT``), the
execution/runtime target (``TARGET``), and convenient named configurations
(``PRESET``). The following are several common examples:

.. code::

   # Build and run sm64-port for this machine
   TEST_LOCALLY=1 VARIANT=sm64-port TARGET=host ./build.sh

   # Build and run the ROM in an emulator (m64py)
   TEST_LOCALLY=1 PRESET=n64 EMULATOR=m64py ./build.sh

   # Build an x86_64 Steam Runtime binary for Steam Deck
   PRESET=steamdeck ./build.sh

   # One-time setup when building ARM64 on an x86_64 Docker host
   ./dev/setup_docker_binfmt.sh arm64

   # Build the preferred ARM64 Steam Frame frontend (sm64ex + SDL2)
   PRESET=steamframe ./build.sh

   # Deploy tpl/sm64ex/build/us_pc with SteamOS Devkit Client. On the Frame,
   # select Steam Linux Runtime 4.0 ARM64 and start sm64.us.f3dex2e.

   # Presets and variants are independent; override when testing another port
   PRESET=steamframe VARIANT=sm64-port ./build.sh

Asset source is independent as well. With no baserom specified,
``ASSET_MODE=generate`` remains the default. Use ``reuse`` to compile assets
already present in the selected variant tree. Supplying ``BASEROM_FPATH``
selects ``ASSET_MODE=baserom`` by default and bypasses the random asset
generator entirely:

.. code:: bash

   PRESET=steamframe ASSET_MODE=reuse ./build.sh
   PRESET=steamframe BASEROM_FPATH=baserom.us.z64 ./build.sh

``BASEROM_FPATH`` is intentionally unambiguous: when it is set, the build is
baserom-only and ``ASSET_MODE=generate``/``reuse`` are rejected. Baseline assets
are kept in a persistent sibling checkout such as ``tpl/sm64ex-baserom`` rather
than cleaning the randomized ``tpl/sm64ex`` checkout. The first baserom build
extracts the original assets; later builds reuse that extraction and compatible
native build outputs. Upstream ``extract_assets.py`` already has its own
``.assets-local.txt`` cache and returns immediately when extraction is current.
Nothing in the randomized checkout is deleted when switching modes.

For Steam Runtime builds the wrapper resolves ``BASEROM_FPATH`` on the host
*before* building the container image. A repo-local path such as
``BASEROM_FPATH=baserom.us.z64`` is already visible through the repository's
``/work`` bind mount and is forwarded as ``/work/baserom.us.z64``. A baserom
outside the repository receives a dedicated read-only ``/inputs`` mount. The
wrapper prints both resolved paths. If the outer wrapper saw a baserom but the
inner build cannot see it, the build aborts rather than falling back to asset
generation.

To supply a ROM only for reference generation while continuing to randomize
assets, use ``EXTERNAL_ROM_FPATH`` together with ``BUILD_REFERENCE=1``. The
historical ``EXTERNAL_ROM_FPATH`` spelling keeps its original behavior.

Legacy ``TARGET=pc``, ``TARGET=rom``, and ``TARGET=<variant>`` spellings are
still accepted with a warning.


Specialized Install Documentation
---------------------------------

See specialized install docs for:

* `Windows <docs/source/manual/install_docs/install-on-windows.rst>`_
* `Replit <docs/source/manual/install_docs/install_on_replit.rst>`_
* `Steam Deck <docs/source/manual/install_docs/install_on_steamdeck.rst>`_
* `Steam Frame <docs/source/manual/install_docs/install_on_steamframe.rst>`_


Resources
---------

* Learning the basics slides: https://docs.google.com/presentation/d/1Ab8wlJfT7b7TlbOohgvsX43TqSAYQQ3azuJTkNdaB0c/edit?pli=1#slide=id.p

* Educational Templates: https://github.com/Erotemic/cc_game_templates

* High resolution redrawn textures: https://github.com/TechieAndroid/sm64redrawn

* SM64 Randomizer: https://github.com/andrelikesdogs/sm64-randomizer

* SM64 PC Subreddit: https://www.reddit.com/r/SM64PC/


N64 Stuff
~~~~~~~~~

* Everdrive 64 X7: https://krikzz.com/our-products/cartridges/ed64x7.html

Emulator Stuff
~~~~~~~~~~~~~~

* Mupen64Plus Emulator: https://wiki.debian.org/Mupen64Plus

* Python Frontend for Mupen64Plus: https://github.com/mupen64plus/mupen64plus-ui-python

Rom Stuff
~~~~~~~~~

* Kaze Emanuar ROM Hacks: https://www.notabug.org/anomie/kaze-emanuar-romhacks

* List of SM64 Hacks and Ports: https://en.wikipedia.org/wiki/List_of_Super_Mario_64_ROM_hacks,_mods_and_ports

PC Port Extension Repos
~~~~~~~~~~~~~~~~~~~~~~~

* SM64: https://github.com/n64decomp/sm64 - the original decomp

* SM64-Port: https://github.com/sm64-port/sm64-port - the basic port

* SM64-Plus: https://github.com/MorsGames/sm64plus

* SM64ex: https://github.com/sm64pc/sm64ex

* libsm64: https://github.com/libsm64/libsm64

* Sm64ex-alo: https://github.com/AloUltraExt/sm64ex-alo

* Render96ex: https://github.com/Render96/Render96ex - actively developed in 2024

* SM64CoopDX: https://github.com/coop-deluxe/sm64coopdx - actively developed in 2024


Other
~~~~~~

* The SM64 Decomp Discord: https://discord.gg/DuYH3Fh

.. |Pypi| image:: https://img.shields.io/pypi/v/sm64-random-assets.svg
    :target: https://pypi.python.org/pypi/sm64-random-assets
.. |PypiDownloads| image:: https://img.shields.io/pypi/dm/sm64-random-assets.svg
    :target: https://pypistats.org/packages/sm64-random-assets
.. |ReadTheDocs| image:: https://readthedocs.org/projects/sm64-random-assets/badge/?version=latest
    :target: http://sm64-random-assets.readthedocs.io/en/latest/
.. |GithubActions| image:: https://github.com/Erotemic/sm64-random-assets/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/Erotemic/sm64-random-assets/actions?query=branch%3Amain
.. |Codecov| image:: https://codecov.io/github/Erotemic/sm64-random-assets/badge.svg?branch=main&service=github
    :target: https://codecov.io/github/Erotemic/sm64-random-assets?branch=main


Audio Quality
-------------

The quality lever also controls generated AIFF samples. Quality ``0`` keeps
Jon Crall's original full-range random audio realization. Higher targets select
a deterministic clean-room synthesizer authored by ``openai:gpt-5.6-thinking``.
It uses the sample filename to choose conservative synthesized instruments,
percussion, vocal-like chirps, or softened effects while preserving the exact
sample length and rate required by the game.

For the best currently registered image and audio realizations::

    python generate_assets.py --dst tpl/sm64 --target_quality=1

To preserve only the original human-authored realizations::

    python generate_assets.py --dst tpl/sm64 --target_quality=1 --include_authors='human:*'

This improves sample quality only. Music sequence composition in the ``.m64``
files remains unchanged for now.


Simple generated music
----------------------

At higher quality levels the generator now emits compact clean-room M64
sequences instead of zero-filled music files.  The initial realization is
intentionally modest: a melody and bass voice, selected from suitable pitched
instruments in each target sound bank.  Level and menu tracks loop, while
short event and cutscene tracks end normally.

The default build selects these assets::

    ./build.sh

The original zero-filled music behavior remains available::

    TARGET_QUALITY=0 ./build.sh

The generated music realization is registered as ``openai.simple-music`` with
version ``1`` and estimated quality ``0.60``.

At higher `--target_quality` values, unmatched PNG textures are now produced by a deterministic PIL-based procedural texture generator instead of pure random noise. Semantic human-authored glyph and HUD textures still take precedence when available.

The PIL texture realization now performs a more semantic filename-based interpretation. It distinguishes between tileable surfaces, doors, boxes, signs, eyes/faces, overlays, and particle-like sprites, and then renders material-appropriate textures such as masonry, brick, wood grain, water ripples, lava crust, brushed metal, sand ripples, snow drifts, clouded sky, and transparent bubble/particle sprites.

The latest refinement makes this more methodical and family-aware: the generator now infers actor family, role, motif, and material/part type from asset paths, then renders purpose-built substitutes for shells, scales, fur, feathers, beaks, ivory, flowers, jewels, pages, book covers, piano keys, eggs, lenses, signs, doors, boxes, skyboxes, smoke, splashes, sparkles, flames, and tree sprites. The goal is not pixel-perfect imitation, but interesting art that better matches what each asset was probably trying to represent while remaining clearly disjoint from original source data.

The latest PIL-texture pass also explicitly defers to the human-authored glyph and HUD/life-bar generator by quality rating, improves Bob-omb / King Bob-omb surface rendering, adds specialized coin textures, and treats Bob-omb Battlefield texture groups as grass rather than generic stone.

The realization policy now treats the human semantic generator as the preferred source for glyphs and the HUD life bar, while semantic character-part textures such as eyes are left to the PIL semantic renderer. The PIL pass also now includes a better Mario-eye treatment and richer water / grass variants.

Bob-omb Battlefield uses the castle painting pair ``levels/castle_inside/17.rgba16.png`` and ``levels/castle_inside/18.rgba16.png``. These two 64x32 halves now use a dedicated scenic renderer and combine into a coherent 64x64 course portrait. The similarly named ``levels/bob/*`` assets remain battlefield course textures rather than painting tiles.

Bowser / Peach fake-out and character differentiation
-----------------------------------------------------

The castle hallway fake-out uses code-authored Peach and Bowser portraits for
``levels/castle_inside/5.rgba16.png`` and ``6.rgba16.png``.  A focused
``openai.bowser-peach-textures`` realization also differentiates named Bowser
and Peach actor parts and gives Bowser flame frames transparent animated
silhouettes.


Broader actor and animation differentiation
-------------------------------------------

The ``openai.differentiated-textures`` realization adds filename-aware code
renderers for 198 additional textures across common enemies, NPCs, props, and
effects.  Multi-part actors now use coherent family palettes while their eyes,
mouths, shells, scales, fur, foliage, machinery, locks, bars, and other named
parts remain visually distinct.  Flame, explosion, smoke, water-wave, and
Yoshi-egg frame sequences also change shape and phase across frames instead of
reusing nearly identical generic art.
