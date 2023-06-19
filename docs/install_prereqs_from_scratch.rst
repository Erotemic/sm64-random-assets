
Building m4, autotools, pkg-config and capstone from scratch

.. code:: bash

   ROOT_DPATH=$HOME/M64Test2
   LOCAL_PREFIX=$ROOT_DPATH/.local

   export PATH=$LOCAL_PREFIX/bin:$PATH
   export LD_LIBRARY_PATH=$LOCAL_PREFIX/lib:$LD_LIBRARY_PATH
   export CPATH=$LOCAL_PREFIX/include:$CPATH

   mkdir -p $LOCAL_PREFIX
   mkdir -p $ROOT_DPATH/code

   # First grab Python
   export PYENV_ROOT="$ROOT_DPATH/.pyenv"

   curl https://pyenv.run | bash
   command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
   eval "$(pyenv init -)"
   pyenv install mambaforge-4.10.1-4
   pyenv global mambaforge-4.10.1-4
   # Test that Python is available
   python --version
   which python
   # Install the required Python dependencies
   pip install kwimage[headless]

   # Free up some space in resource constrained environments
   conda clean --all --yes
   rm -rf $ROOT_DPATH/.pyenv/.git

   # Build M4 from source
   cd $ROOT_DPATH/code
   curl -O https://ftp.gnu.org/gnu/m4/m4-1.4.18.tar.gz
   gunzip m4-1.4.18.tar.gz
   tar xvf m4-1.4.18.tar
   rm m4-1.4.18.tar
   cd m4-1.4.18
   # Getting m4 to build is not easy, need several patches
   # Ref: https://github.com/openwrt/openwrt/issues/9055
   # Ref: https://askubuntu.com/questions/1099392/compilation-of-m4-1-4-10-to-1-4-18-fails-due-to-please-port-gnulib-freadahead-c
   curl -O https://raw.githubusercontent.com/keyfour/openwrt/2722d51c5cf6a296b8ecf7ae09e46690403a6c3d/tools/m4/patches/011-fix-sigstksz.patch
   curl -O https://src.fedoraproject.org/rpms/m4/raw/814d592134fad36df757f9a61422d164ea2c6c9b/f/m4-1.4.18-glibc-change-work-around.patch
   git apply 011-fix-sigstksz.patch
   git apply m4-1.4.18-glibc-change-work-around.patch
   ./configure --prefix="$LOCAL_PREFIX"
   make
   make install

   # Build autoconf from source
   cd $ROOT_DPATH/code
   curl -O http://ftp.gnu.org/gnu/autoconf/autoconf-2.71.tar.gz
   tar xvfz autoconf-2.71.tar.gz
   rm autoconf-2.71.tar.gz
   cd autoconf-2.71
   ./configure --prefix=$LOCAL_PREFIX
   make
   make install

   # Build automake
   cd $ROOT_DPATH/code
   curl -O http://ftp.gnu.org/gnu/automake/automake-1.16.tar.gz
   tar xvfz automake-1.16.tar.gz
   rm automake-1.16.tar.gz
   cd automake-1.16
   ./configure --prefix=$LOCAL_PREFIX
   make
   make install

   # Install libtool (https://noknow.info/it/os/install_libtool_from_source?lang=en)
   cd $ROOT_DPATH/code
   curl -O http://ftp.jaist.ac.jp/pub/GNU/libtool/libtool-2.4.6.tar.gz
   tar xvfz libtool-2.4.6.tar.gz
   rm libtool-2.4.6.tar.gz
   cd libtool-2.4.6
   ./configure --prefix=$LOCAL_PREFIX
   make
   make install

   # used pkg-config hash d97db4fae4c1cd099b506970b285dc2afd818ea2
   git clone https://gitlab.freedesktop.org/pkg-config/pkg-config.git  $ROOT_DPATH/code/pkg-config
   cd $ROOT_DPATH/code/pkg-config
   rm -rf .git
   ./autogen.sh
   ./configure --prefix=$LOCAL_PREFIX --with-internal-glib
   make
   make install

   # used capstone hash: e9fd6f4800be1584124e9eee92cf15ab947d33ec
   git clone https://github.com/capstone-engine/capstone.git $ROOT_DPATH/code/capstone
   cd $ROOT_DPATH/code/capstone
   # on replit we need to save as much space as possible
   rm -rf .git
   # Hack
   sed -i "s|PREFIX .= /usr/local|PREFIX ?= $LOCAL_PREFIX|g" Makefile
   sed -i "s|PREFIX .= /usr|PREFIX ?= $LOCAL_PREFIX|g" Makefile
   make
   make install
   # After we install capstone remove the source because it is 200M
   rm -rf $ROOT_DPATH/code/capstone

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
   #INCLUDE_DIRS=$LOCAL_PREFIX/include COMPARE=0 make VERSION=us -j$NUM_CPUS
   #ln -s $LOCAL_PREFIX/include/capstone capstone
   #ln -s $LOCAL_PREFIX/include/capstone include/capstone
   COMPARE=0 make VERSION=us CFLAGS="-I$LOCAL_PREFIX/include/capstone" -j$NUM_CPUS

   # The compiled ROM is:
   build/us/sm64.us.z64


If replit crashes:

.. code:: bash

   ROOT_DPATH=$HOME/M64Test2
   LOCAL_PREFIX=$ROOT_DPATH/.local

   export PATH=$LOCAL_PREFIX/bin:$PATH
   export LD_LIBRARY_PATH=$LOCAL_PREFIX/lib:$LD_LIBRARY_PATH
   export CPATH=$LOCAL_PREFIX/include:$CPATH
   export PYENV_ROOT="$ROOT_DPATH/.pyenv"

   mkdir -p $LOCAL_PREFIX
   mkdir -p $ROOT_DPATH/code

   # First grab Python
   command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
   eval "$(pyenv init -)"
   python --version
   which python

   pip cache purge


   # Clear out space
   rm -rf $PYENV_ROOT/versions/mambaforge-4.10.1-4/pkgs

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

    # Install the mamba version of conda / anaconda
    pyenv install mambaforge-4.10.1-4

    # Activate it
    pyenv global mambaforge-4.10.1-4

    # DONT Use conda to install binary dependencies
    # conda remove -c conda-forge capstone pkg-config

    # Test that Python is available
    python --version
    which python

    # Install the required Python dependencies
    pip install kwimage[headless]


Try with simple nix


.. code:: bash

    nix-shell -p capstone
    nix-shell -p pkg-config
    nix-shell -p python311Packages.pip
    nix-shell -p python311


# Replit Config
# https://search.nixos.org/packages

.. code::

    { pkgs }: {
      deps = [
        pkgs.bashInteractive
        pkgs.capstone
        pkgs.pkg-config
        pkgs.nodePackages.bash-language-server
        pkgs.man
        python311Packages.pip
      ];
    }


    OR?

.. code::

    { pkgs }: {
      deps = [
        pkgs.python310Full
        pkgs.replitPackages.prybar-python310
        pkgs.replitPackages.stderred
        pkgs.capstone
        pkgs.pkg-config
        pkgs.python311Packages.pkgconfig

      ];
      env = {
        PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
          # Needed for pandas / numpy
          pkgs.stdenv.cc.cc.lib
          pkgs.zlib
          # Needed for pygame
          pkgs.glib
          # Needed for matplotlib
          pkgs.xorg.libX11
        ];
        PYTHONHOME = "${pkgs.python310Full}";
        PYTHONBIN = "${pkgs.python310Full}/bin/python3.10";
        LANG = "en_US.UTF-8";
        STDERREDBIN = "${pkgs.replitPackages.stderred}/bin/stderred";
        PRYBAR_PYTHON_BIN = "${pkgs.replitPackages.prybar-python310}/bin/prybar-python310";
      };
    }

.. code:: bash

   pip install kwimage[headless]

   SITE_PACKAGE_DPATH=$(python -c "import sysconfig; print(sysconfig.get_paths()['platlib'])")
   cat $SITE_PACKAGE_DPATH/cv2/__init__.py
   sed -i "s|LOADER_DIR =.*|LOADER_DIR = '$SITE_PACKAGE_DPATH/cv2'|" $SITE_PACKAGE_DPATH/cv2/__init__.py

   ROOT_DPATH=$HOME/$REPL_SLUG
   echo $ROOT_DPATH
   mkdir -p $ROOT_DPATH/code

   # Clone the ROM-only sm64 repo
   git clone https://github.com/n64decomp/sm64.git $ROOT_DPATH/code/sm64

   # Clone this repo
   git clone https://github.com/Erotemic/sm64-random-assets.git $ROOT_DPATH/code/sm64-random-assets

   # Run the asset generator
   python $ROOT_DPATH/code/sm64-random-assets/generate_assets.py --dst $ROOT_DPATH/code/sm64

   # Move into the sm64 directory
   cd $ROOT_DPATH/code/sm64

   # Compile
   #INCLUDE_DIRS=$LOCAL_PREFIX/include COMPARE=0 make VERSION=us -j$NUM_CPUS
   #ln -s $LOCAL_PREFIX/include/capstone capstone
   #ln -s $LOCAL_PREFIX/include/capstone include/capstone
   COMPARE=0 make VERSION=us
   NOEXTRACT=1 COMPARE=0 NON_MATCHING=1 make VERSION=us

   # The compiled ROM is:
   build/us/sm64.us.z64


Getting
-------

.. code::

    libc_impl.c:(.text+0x4b88): warning: the use of `tempnam' is dangerous, better use `mkstemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_mktemp':
    libc_impl.c:(.text+0x4d3c): warning: the use of `mktemp' is dangerous, better use `mkstemp' or `mkdtemp'
    gcc: fatal error: Killed signal terminated program cc1
    compilation terminated.
    make[1]: *** [Makefile:35: copt] Error 1
    make: *** [Makefile:76: ido5.3_recomp] Error 2
    Makefile:192: *** Failed to build tools.  Stop.



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
