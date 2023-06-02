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


Troubleshooting
---------------

On NixOS opencv seems to behave oddly and raises an error. Test for the issue via:

.. code::

   python -c "import sys; sys.OpenCV_LOADER_DEBUG=1; import cv2"


You have the issue if it gives the following error:

.. code::

    ImportError: OpenCV loader: missing configuration file: ['config.py']. Check OpenCV installation.

I found a reference discussing the issue `here <https://scratch.mit.edu/discuss/topic/666732/?page=1>`_.

It seems that the problem is that it is not identifying the correct loader
directory. A workaround can be done by modifing the file with some
`UNIX magic <https://jpmens.net/media/2021a/Ql6c5GU.jpg>`_.

.. code::

   SITE_PACKAGE_DPATH=$(python -c "import sysconfig; print(sysconfig.get_paths()['platlib'])")
   cat $SITE_PACKAGE_DPATH/cv2/__init__.py
   sed -i "s|LOADER_DIR =.*|LOADER_DIR = '$SITE_PACKAGE_DPATH/cv2'|" $SITE_PACKAGE_DPATH/cv2/__init__.py

   python -c "import cv2"

Also on NixOS you will need to install ``hexdump``. Type ``hexdump`` and it
will give you a list of packages to install it from. Choose the first one.

.. code::

   git clone https://github.com/wahern/hexdump.git $HOME/tmp/hexdump
   cd $HOME/tmp/hexdump
   mkdir -p $HOME/.local/bin
   cp ./hexdump $HOME/.local/bin

   export PATH=$HOME/.local/bin:$PATH

   git clone https://gitlab.freedesktop.org/pkg-config/pkg-config.git $HOME/tmp/pkg-config
   cd $HOME/tmp/pkg-config
   # And now I'm stuck


REPLit NixOS Instructions V2
----------------------------

Start a bash REPL

type ``hexdump`` and install the first recommended package
type ``pkg-config`` and install the first recommended package

When doing this it seems to hang, ctrl-c and it seems to do fine.

Install pyenv

.. code::
    curl https://pyenv.run | bash

    export PYENV_ROOT="$HOME/.pyenv"
    command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"

    pyenv install mambaforge-4.10.1-4

    # Activate it
    pyenv global mambaforge-4.10.1-4

    # Install X11 (doesnt seem to help)
    # conda install -c conda-forge xorg-libx11
    # conda install -c conda-forge libusb
    conda install -c conda-forge capstone

Headless Usage:

.. code:: bash

    # Make a temporary directory
    mkdir -p $HOME/tmp/test_assets

    # Clone the sm64 port repo
    git clone https://github.com/n64decomp/sm64.git $HOME/tmp/test_assets/sm64-test

    # Clone this repo
    git clone https://github.com/Erotemic/sm64-random-assets.git $HOME/tmp/test_assets/sm64-random-assets

    # Run the asset generator
    python $HOME/tmp/test_assets/sm64-random-assets/generate_assets.py --dst $HOME/tmp/test_assets/sm64-test

    # Move into the port directory
    cd $HOME/tmp/test_assets/sm64-test

    # Compile
    make VERSION=us -j16

    # Run the executable
    build/us_pc/sm64.us

