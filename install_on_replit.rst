.. .. posted questions on fixing this in:
.. .. https://ask.replit.com/t/installing-the-mips-binutils-toolchain/42490
.. .. https://stackoverflow.com/questions/76528113/mips-binutils-on-nixos
.. ..https://discourse.nixos.org/t/cant-compile-dwm-x11-xlib-h-not-found/12633/3


Replit Instructions
-------------------

These instructions outlines the steps to compile a SM64 PCPort on Replit.

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
    pkgs.binutils
    pkgs.libusb1
    pkgs.util-linux
    pkgs.SDL2
    pkgs.xorg.libX11.dev
    pkgs.xorg.libXrandr.dev
    pkgs.alsa-lib
    pkgs.libpulseaudio


The full config should look like this:


.. code::

    { pkgs }: {
      deps = [
          pkgs.python310Full
          pkgs.replitPackages.prybar-python310
          pkgs.replitPackages.stderred
          pkgs.capstone
          pkgs.pkg-config
          pkgs.binutils
          pkgs.libusb1
          pkgs.util-linux
          pkgs.SDL2
          pkgs.xorg.libX11.dev
          pkgs.xorg.libXrandr.dev
          pkgs.alsa-lib
          pkgs.libpulseaudio
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


Install the Prerequisites
=========================

In our new configured shells, we are going to download the code for generating random assets and the sm64 code itself.

.. code:: bash

   # Define where we will put the code (the REPL_SLUG is an REPL provided
   # environment variable that gives us folder name where we can put things
   # without worrying about Replit deleting them)
   CODE_DPATH=$HOME/$REPL_SLUG/code
   echo "CODE_DPATH = $CODE_DPATH"
   mkdir -p $CODE_DPATH/code

   # Clone this repo
   git clone https://github.com/Erotemic/sm64-random-assets.git $CODE_DPATH/sm64-random-assets

   cd $CODE_DPATH/sm64-random-assets
   git submodule update --init tpl/sm64-port


We will now install the dependencies of the random asset generator.

.. code:: bash

   # In the sm64-random-assets repo root
   pip install -e .[headless]

Due to some weirdness with Replit, opencv fails to find its config, which
causes an error if we try to use it. A quick patch makes this error go away.

.. code:: bash

   # Normally you only need the above line, but this patches an issue on replit
   SITE_PACKAGE_DPATH=$(python -c "import sysconfig; print(sysconfig.get_paths()['platlib'])")
   cat $SITE_PACKAGE_DPATH/cv2/__init__.py
   sed -i "s|LOADER_DIR =.*|LOADER_DIR = '$SITE_PACKAGE_DPATH/cv2'|" $SITE_PACKAGE_DPATH/cv2/__init__.py


Now we can use the asset autogeneration code to populate the assets in the main repo.

.. code:: bash

   # Run the asset generator
   python $CODE_DPATH/sm64-random-assets/generate_assets.py --dst $CODE_DPATH/sm64-random-assets/tpl/sm64-port


Now we are ready to build the game. We move into the sm64 directory and run
``make`` with a few environment variables.


.. code:: bash

   # OPTIONAL: custom code
   CODE_DPATH=${CODE_DPATH:-$HOME/$REPL_SLUG/code}
   cd $CODE_DPATH/sm64-random-assets/tpl/sm64-port
   git remote add Erotemic https://github.com/Erotemic/sm64-port
   git fetch Erotemic
   git checkout config_draw_dist

.. code:: bash

   # Move into the sm64 directory
   CODE_DPATH=${CODE_DPATH:-$HOME/$REPL_SLUG/code}
   cd $CODE_DPATH/sm64-random-assets/tpl/sm64-port

   # There is a small patch we have to apply to make this work in Replit's NIX
   # environment

   # Compile
   NOEXTRACT=1 COMPARE=0 NON_MATCHING=0 VERSION=us make


If all goes well, the final compiled exe will live in:


.. code::

   build/us_pc/sm64.us


Debugging, adding ``pkgs.valgrind`` to deps.


.. code:: bash

   CODE_DPATH=${CODE_DPATH:-$HOME/$REPL_SLUG/code}
   cd $CODE_DPATH/sm64-random-assets/tpl/sm64-port

   valgrind --track-origins=yes --dsymutil=yes build/us_pc/sm64.us


Current problem

.. code:: bash

   ==262== Invalid read of size 2
   ==262==    at 0x484FEA0: memmove (in /nix/store/qmdp39yy74091vlrvrj39c8rzbslhci8-valgrind-3.19.0/libexec/valgrind/vgpreload_memcheck-amd64-linux.so)
   ==262==    by 0x4AFC41: osPiStartDma (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x4A08C6: audio_dma_copy_immediate (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x4A117D: bank_load_immediate (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x4A1646: load_banks_immediate (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x4A17ED: load_sequence_internal (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x4A1906: load_sequence (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x49CF3C: seq_player_play_sequence (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x43FE00: thread5_game_loop (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x4AFBB8: main_func (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x404B18: main (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==  Address 0x11b011e01200114 is not stack'd, malloc'd or (recently) free'd
   ==262==
   ==262==
   ==262== Process terminating with default action of signal 11 (SIGSEGV): dumping core
   ==262==  General Protection Fault
   ==262==    at 0x484FEA0: memmove (in /nix/store/qmdp39yy74091vlrvrj39c8rzbslhci8-valgrind-3.19.0/libexec/valgrind/vgpreload_memcheck-amd64-linux.so)
   ==262==    by 0x4AFC41: osPiStartDma (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x4A08C6: audio_dma_copy_immediate (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x4A117D: bank_load_immediate (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x4A1646: load_banks_immediate (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x4A17ED: load_sequence_internal (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x4A1906: load_sequence (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x49CF3C: seq_player_play_sequence (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x43FE00: thread5_game_loop (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x4AFBB8: main_func (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==    by 0x404B18: main (in /home/runner/TestV3/code/sm64-random-assets/tpl/sm64-port/build/us_pc/sm64.us)
   ==262==
   ==262== HEAP SUMMARY:
   ==262==     in use at exit: 14,429,598 bytes in 60,207 blocks
   ==262==   total heap usage: 126,183 allocs, 65,976 frees, 58,647,530 bytes allocated
   ==262==
   ==262== LEAK SUMMARY:
   ==262==    definitely lost: 640 bytes in 1 blocks
   ==262==    indirectly lost: 0 bytes in 0 blocks
   ==262==      possibly lost: 7,816,068 bytes in 50,499 blocks
   ==262==    still reachable: 6,612,890 bytes in 9,707 blocks
   ==262==         suppressed: 0 bytes in 0 blocks
   ==262== Rerun with --leak-check=full to see details of leaked memory
   ==262==
   ==262== For lists of detected and suppressed errors, rerun with: -s
   ==262== ERROR SUMMARY: 1 errors from 1 contexts (suppressed: 0 from 0)
   Segmentation fault (core dumped)

Solved by adding "-static" to the opt flags. Also a good idea to remove "-g"
and add "-O" for speed.
