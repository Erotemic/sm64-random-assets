Generates non-copyrighted randomized assets so sm64-port can be used for
educational purposes.


Python Requirements:

* kwimage
* python-opencv-headless
* ubelt
* numpy


This has only been tested for building the US variant, and only on Linux.


Example Usage:

.. code:: bash

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
