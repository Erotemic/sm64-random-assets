SM64 Randomized Asset Generator
===============================

Generates non-copyrighted randomized assets so sm64 and sm64-port can be used
for educational purposes.

This has only been tested for building the US variant, and only on Linux.

For each asset it generates a random texture, except in special cases like text
where it was possible to generate reasonable textures with open source tools.
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

   pip install kwimage opencv-python-headless ubelt numpy ruamel.yaml PyYAML scriptconfig rich parse


PC Port Example Usage
---------------------

The following instructions were written on an Ubuntu 22.04 PC

.. code:: bash

    # PC Port Dependencies
    sudo apt install -y git build-essential pkg-config libusb-1.0-0-dev libsdl2-dev

    # You can set your "code" directory path - the place where you will clone
    # this repo - to be somewhere convenient for you
    CODE_DPATH=$HOME/code

    # Ensure your code directory exists
    mkdir -p $CODE_DPATH

    # Clone this repo
    git clone https://github.com/Erotemic/sm64-random-assets.git $CODE_DPATH/sm64-random-assets

    # Move into the root of this repo and initialize the sm64-port submodule,
    # which will clone the official PC port repo.
    cd $CODE_DPATH/sm64-random-assets
    git submodule update --init tpl/sm64-port

    # Run the asset generator
    python $CODE_DPATH/sm64-random-assets/generate_assets.py --dst $CODE_DPATH/sm64-random-assets/tpl/sm64-port

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

    # Ensure your code directory exists
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

This ROM can now be flashed on an N64 cartage, copied onto an Everdrive, or run
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

I have verified that I cen enter every major stage and complete every bowser
fight, so I think all of the crashes have been resolved by reducing texture
sizes. I have completed a 16 star run on real N64 hardware with this.


Development
-----------

While I'll try to keep the above instructions working / maintained, the
``build.sh`` script is the end-to-end entry point for developers. Starting from
a fresh repo, the ``build.sh`` script will take care of the entire process from
initializing submodules, generating assets, compiling the binaries, and even
running them with the pc-port, in an emulator, or copying ROMs to an EverDrive.
Environment variables can be used to control the build.sh behavior.

The following are several common examples:

.. code::

   # Build and run the PC port
   TEST_LOCALLY=1 TARGET=pc ./build.sh

   # Build and run the ROM in an emulator (m64py)
   TEST_LOCALLY=1 TARGET=rom EMULATOR=m64py ./build.sh

Resources
---------

* Mupen64Plus Emulator: https://wiki.debian.org/Mupen64Plus

* Python Frontend for Mupen64Plus: https://github.com/mupen64plus/mupen64plus-ui-python

* Everdrive 64 X7: https://krikzz.com/our-products/cartridges/ed64x7.html

* The SM64 Port: https://github.com/sm64-port/sm64-port

* The SM64 Decomp: https://github.com/n64decomp/sm64

* The SM64 Decomp Discord: https://discord.gg/DuYH3Fh

* Kaze Emanuar ROM Hacks: https://www.notabug.org/anomie/kaze-emanuar-romhacks

* High resolution redrawn textures: https://github.com/TechieAndroid/sm64redrawn

* SM64 Randomizer: https://github.com/andrelikesdogs/sm64-randomizer

* List of SM64 Hacks and Ports: https://en.wikipedia.org/wiki/List_of_Super_Mario_64_ROM_hacks,_mods_and_ports

* SM64 plus: https://github.com/MorsGames/sm64plus

* SM64 ex: https://github.com/sm64pc/sm64ex
