Generates non-copyrighted randomized assets so sm64-port can be used for
educational purposes.


Python Requirements:

.. code:: bash

   pip install kwimage opencv-python-headless ubelt numpy


This has only been tested for building the US variant, and only on Linux.

For each asset it generates a random texture, except in special cases like text
where it was possible to generate reasonable textures with open source tools.
The result is surprisingly playable.


.. image:: https://i.imgur.com/iiMPSTZ.png


PC Port Example Usage
---------------------

.. code:: bash

    # PC Port Dependencies
    sudo apt install -y git build-essential pkg-config libusb-1.0-0-dev libsdl2-dev

    # Make a temporary directory
    mkdir -p $HOME/tmp/test_assets

    # Clone the sm64 port repo
    git clone https://github.com/sm64-port/sm64-port $HOME/tmp/test_assets/sm64-port-test

    # Clone this repo
    git clone https://github.com/Erotemic/sm64-random-assets.git $HOME/tmp/test_assets/sm64-random-assets

    # Run the asset generator
    python $HOME/tmp/test_assets/sm64-random-assets/generate_assets.py --dst $HOME/tmp/test_assets/sm64-port-test

    # Move into the port directory
    cd $HOME/tmp/test_assets/sm64-port-test

    # Compile
    make VERSION=us -j16

    # Run the executable
    build/us_pc/sm64.us

Headless ROM Usage
------------------

.. code:: bash

    # Make a temporary directory
    ROOT_DPATH=$HOME/tmp/tmp-code
    mkdir -p $ROOT_DPATH

    # Clone the ROM-only sm64 repo
    git clone https://github.com/n64decomp/sm64.git $ROOT_DPATH/code/sm64

    # Clone this repo
    git clone https://github.com/Erotemic/sm64-random-assets.git $ROOT_DPATH/code/sm64-random-assets

    # Run the asset generator
    python $ROOT_DPATH/code/sm64-random-assets/generate_assets.py --dst $ROOT_DPATH/code/sm64

    # Move into the sm64 directory
    cd $ROOT_DPATH/code/sm64

    # Compile
    NUM_CPUS=$(nproc --all)
    COMPARE=0 NON_MATCHING=1 make VERSION=us -j$NUM_CPUS

    # The compiled ROM is:
    build/us/sm64.us.z64


Known Issues
------------

Something is causing the first Bowser fight to lock on real N64 hardware.
