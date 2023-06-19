REPLit Instructions
-------------------

These instructions outlines the steps to compile a SM64 ROM on REPLIT.

Navigate to `replit.com <https://replit.com/>`_

Create an account or login.


Setup The REPL
==============

Create a REPL, and use the "Python" template.

On the left there is a "Files" menu, and a "..." "meatball" menu. One of the
options is "show hidden files", click that to get access to your
``.replit.nix`` config.


In the ``deps`` section add:

.. code::

        pkgs.capstone
        pkgs.pkg-config
        pkgs.python310Packages.pkgconfig


The full config should look like this:


.. code::

    { pkgs }: {
      deps = [
        pkgs.python310Full
        pkgs.replitPackages.prybar-python310
        pkgs.replitPackages.stderred
        pkgs.capstone
        pkgs.pkg-config
        pkgs.python310Packages.pkgconfig
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


Now that we have updated our environment, click the "+" icon to create a new
"Shell".


.. .. Replit Config
.. ..  https://search.nixos.org/packages


Install the Prerequistes
========================

In our new configured shell we will install the prerequistes. Due to some
weirdness with REPLit, opencv fails to find its config, which causes an error
if we try to use it. A quick patch makes this error go away.

.. code:: bash

   pip install kwimage[headless]

   SITE_PACKAGE_DPATH=$(python -c "import sysconfig; print(sysconfig.get_paths()['platlib'])")
   cat $SITE_PACKAGE_DPATH/cv2/__init__.py
   sed -i "s|LOADER_DIR =.*|LOADER_DIR = '$SITE_PACKAGE_DPATH/cv2'|" $SITE_PACKAGE_DPATH/cv2/__init__.py


Now we are going to download the code for generating random assets and the sm64
code itself.

.. code:: bash

   # Define where we will put the code (the REPL_SLUG is an REPL provided
   # environment variable that gives us folder name where we can put things
   # without worring about REPLit deleting them)
   ROOT_DPATH=$HOME/$REPL_SLUG
   echo $ROOT_DPATH
   mkdir -p $ROOT_DPATH/code

   # Clone the ROM-only sm64 repo
   git clone https://github.com/n64decomp/sm64.git $ROOT_DPATH/code/sm64

   # Clone the asset autogeneration repo
   git clone https://github.com/Erotemic/sm64-random-assets.git $ROOT_DPATH/code/sm64-random-assets


Now we can use the asset autogeneration code to populate the assets in the main repo.

.. code:: bash

   # Run the asset generator
   python $ROOT_DPATH/code/sm64-random-assets/generate_assets.py --dst $ROOT_DPATH/code/sm64



Now we are ready to build the game. We move into the sm64 directory and run
``make`` with a few environment variables.

.. code:: bash

   # Move into the sm64 directory
   cd $ROOT_DPATH/code/sm64

   # Compile
   NOEXTRACT=1 COMPARE=0 NON_MATCHING=1 VERSION=us make


If all goes well, the final compiled ROM will live in:


.. code::

   build/us/sm64.us.z64


If all does not go well, you may get an error. I'm currently seeing output that
indicates that something in the make process was killed and there isn't much
more debugging information.
