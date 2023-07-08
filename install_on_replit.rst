.. .. posted questions on fixing this in:
.. .. https://ask.replit.com/t/installing-the-mips-binutils-toolchain/42490
.. .. https://stackoverflow.com/questions/76528113/mips-binutils-on-nixos



Replit Instructions
-------------------

These instructions outlines the steps to compile a SM64 ROM on Replit.

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
        pkgs.binutils
        pkgs.binutils-unwrapped-all-targets
        pkgsCross.mipsel-linux-gnu.buildPackages.bintools


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
        pkgs.binutils
        pkgs.binutils-unwrapped-all-targets
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

In our new configured shell we will install the prerequisites. Due to some
weirdness with Replit, opencv fails to find its config, which causes an error
if we try to use it. A quick patch makes this error go away.

.. code:: bash

   pip install kwimage[headless]

   # Normally you only need the above line, but this patches an issue on replit
   SITE_PACKAGE_DPATH=$(python -c "import sysconfig; print(sysconfig.get_paths()['platlib'])")
   cat $SITE_PACKAGE_DPATH/cv2/__init__.py
   sed -i "s|LOADER_DIR =.*|LOADER_DIR = '$SITE_PACKAGE_DPATH/cv2'|" $SITE_PACKAGE_DPATH/cv2/__init__.py


Now we are going to download the code for generating random assets and the sm64
code itself.

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
   git submodule update --init tpl/sm64


Now we can use the asset autogeneration code to populate the assets in the main repo.

.. code:: bash

   # Run the asset generator
   python $CODE_DPATH/sm64-random-assets/generate_assets.py --dst $CODE_DPATH/sm64-random-assets/tpl/sm64


Now we are ready to build the game. We move into the sm64 directory and run
``make`` with a few environment variables.

.. code:: bash

   # Move into the sm64 directory
   cd $CODE_DPATH/sm64-random-assets/tpl/sm64

   # Compile
   NOEXTRACT=1 COMPARE=0 NON_MATCHING=0 VERSION=us make


If all goes well, the final compiled ROM will live in:


.. code::

   build/us/sm64.us.z64


Warnings about things like ``__STRICT_ANSI_``, ``sigset``, and ``mkstemp`` are
expected and ok.


If all does not go well, you may get an error. I'm currently seeing output that
indicates that something in the make process was killed and there isn't much
more debugging information.


.. code::

    gcc: fatal error: Killed signal terminated program cc1
    compilation terminated.
    make[1]: *** [Makefile:35: copt] Error 1
    make: *** [Makefile:76: ido5.3_recomp] Error 2
    Makefile:192: *** Failed to build tools.  Stop.


The following are the warnings that were generated above, and this should not be an issue:

.. code::

       ==== Build Options ====
    Version:        us
    Microcode:      f3d_old
    Target:         sm64.us
    Compare ROM:    no
    Build Matching: no
    =======================
    Building tools...

    In file included from /nix/store/1gf2flfqnpqbr1b4p4qz2f72y42bs56r-gcc-11.3.0/include/c++/11.3.0/cstdio:41,
                     from armips.cpp:51:
    /nix/store/1gf2flfqnpqbr1b4p4qz2f72y42bs56r-gcc-11.3.0/include/c++/11.3.0/x86_64-unknown-linux-gnu/bits/c++config.h:573:2: warning: #warning "__STRICT_ANSI__ seems to have been undefined; this is not supported" [-Wcpp]
      573 | #warning "__STRICT_ANSI__ seems to have been undefined; this is not supported"
          |  ^~~~~~~
    armips.cpp:1273:9: warning: ISO C++ prohibits anonymous structs [-Wpedantic]
     1273 |         {
          |         ^
    armips.cpp: In member function ‘wchar_t TextFile::readCharacter()’:
    armips.cpp:15054:50: warning: ‘value’ may be used uninitialized in this function [-Wmaybe-uninitialized]
    15054 |         if (value == L'\r' && recursion == false && atEnd() == false)
          |             ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^~~~~~~~~~~~~~~~~~~
    In constructor ‘ExpressionValue::ExpressionValue(ExpressionValue&&)’,
        inlined from ‘ExpressionValue ExpressionInternal::evaluate()’ at armips.cpp:18031:10:
    armips.cpp:1225:8: warning: ‘val.ExpressionValue::<anonymous>’ may be used uninitialized [-Wmaybe-uninitialized]
     1225 | struct ExpressionValue
          |        ^~~~~~~~~~~~~~~
    armips.cpp: In member function ‘ExpressionValue ExpressionInternal::evaluate()’:
    armips.cpp:17923:25: note: ‘val’ declared here
    17923 |         ExpressionValue val;
          |                         ^~~
    In constructor ‘ExpressionValue::ExpressionValue(ExpressionValue&&)’,
        inlined from ‘ExpressionValue Expression::evaluate()’ at armips.cpp:18145:10:
    armips.cpp:1225:8: warning: ‘invalid.ExpressionValue::<anonymous>’ may be used uninitialized [-Wmaybe-uninitialized]
     1225 | struct ExpressionValue
          |        ^~~~~~~~~~~~~~~
    armips.cpp: In member function ‘ExpressionValue Expression::evaluate()’:
    armips.cpp:18144:33: note: ‘invalid’ declared here
    18144 |                 ExpressionValue invalid;
          |                                 ^~~~~~~
    armips.cpp: In member function ‘bool CDirectiveConditional::evaluate()’:
    armips.cpp:9626:33: warning: ‘value’ may be used uninitialized in this function [-Wmaybe-uninitialized]
     9626 |                 return value != 0;
          |                                 ^
    armips.cpp: In function ‘std::unique_ptr<CAssemblerCommand> parseDirectiveConditional(Parser&, int)’:
    armips.cpp:70:31: warning: ‘type’ may be used uninitialized in this function [-Wmaybe-uninitialized]
       70 |     return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
          |                               ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    armips.cpp:11038:23: note: ‘type’ was declared here
    11038 |         ConditionType type;
          |                       ^~~~
    libc_impl.c: In function ‘wrapper_sigset’:
    libc_impl.c:2284:5: warning: ‘sigset’ is deprecated: Use the signal and sigprocmask functions instead [-Wdeprecated-declarations]
     2284 |     return (uint32_t)(uintptr_t)sigset(signum, handler); // for now only support SIG_DFL etc. as return value
          |     ^~~~~~
    In file included from /nix/store/4pqv2mwdn88h7xvsm7a5zplrd8sxzvw0-glibc-2.35-163-dev/include/sys/wait.h:36,
                     from libc_impl.c:28:
    /nix/store/4pqv2mwdn88h7xvsm7a5zplrd8sxzvw0-glibc-2.35-163-dev/include/signal.h:367:23: note: declared here
      367 | extern __sighandler_t sigset (int __sig, __sighandler_t __disp) __THROW
          |                       ^~~~~~
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_tmpnam':
    libc_impl.c:(.text+0x4c4b): warning: the use of `tmpnam' is dangerous, better use `mkstemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_tempnam':
    libc_impl.c:(.text+0x4b88): warning: the use of `tempnam' is dangerous, better use `mkstemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_mktemp':
    libc_impl.c:(.text+0x4d3c): warning: the use of `mktemp' is dangerous, better use `mkstemp' or `mkdtemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_tmpnam':
    libc_impl.c:(.text+0x4c4b): warning: the use of `tmpnam' is dangerous, better use `mkstemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_tempnam':
    libc_impl.c:(.text+0x4b88): warning: the use of `tempnam' is dangerous, better use `mkstemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_mktemp':
    libc_impl.c:(.text+0x4d3c): warning: the use of `mktemp' is dangerous, better use `mkstemp' or `mkdtemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_tmpnam':
    libc_impl.c:(.text+0x4c4b): warning: the use of `tmpnam' is dangerous, better use `mkstemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_tempnam':
    libc_impl.c:(.text+0x4b88): warning: the use of `tempnam' is dangerous, better use `mkstemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_mktemp':
    libc_impl.c:(.text+0x4d3c): warning: the use of `mktemp' is dangerous, better use `mkstemp' or `mkdtemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_tmpnam':
    libc_impl.c:(.text+0x4c4b): warning: the use of `tmpnam' is dangerous, better use `mkstemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_tempnam':
    libc_impl.c:(.text+0x4b88): warning: the use of `tempnam' is dangerous, better use `mkstemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_mktemp':
    libc_impl.c:(.text+0x4d3c): warning: the use of `mktemp' is dangerous, better use `mkstemp' or `mkdtemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_tmpnam':
    libc_impl.c:(.text+0x4c4b): warning: the use of `tmpnam' is dangerous, better use `mkstemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_tempnam':
    libc_impl.c:(.text+0x4b88): warning: the use of `tempnam' is dangerous, better use `mkstemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_mktemp':
    libc_impl.c:(.text+0x4d3c): warning: the use of `mktemp' is dangerous, better use `mkstemp' or `mkdtemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_tmpnam':
    libc_impl.c:(.text+0x4c4b): warning: the use of `tmpnam' is dangerous, better use `mkstemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_tempnam':
    libc_impl.c:(.text+0x4b88): warning: the use of `tempnam' is dangerous, better use `mkstemp'
    /nix/store/039g378vc3pc3dvi9dzdlrd0i4q93qwf-binutils-2.39/bin/ld: libc_impl.o: in function `wrapper_mktemp':
    libc_impl.c:(.text+0x4d3c): warning: the use of `mktemp' is dangerous, better use `mkstemp' or `mkdtemp'
