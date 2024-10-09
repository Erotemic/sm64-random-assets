Building on Windows
-------------------

There are prerequisites, and in the future we may have better instructions. For now these are notes.

Prerequisites:

* MSys2
* An editor (VSCode)
* git
* Python

* VSCode ? (maybe optional)
* (Where do we download git from? Does it come with msys?
* My machine had mingw and conda already on it, that might be a confounding factor

.. bash::

    # You can set your "code" directory path - the place where you will clone
    # this repo - to be somewhere convenient for you
    CODE_DPATH=$HOME/code
    # Ensure your code directory exists
    mkdir -p "$CODE_DPATH"
    # Clone this repo
    git clone https://github.com/Erotemic/sm64-random-assets.git $CODE_DPATH/sm64-random-assets
    # Move into the root of this repo and initialize the sm64-port submodule,
    # which will clone the official PC port repo.
    cd "$CODE_DPATH"/sm64-random-assets

.. code::

    git submodule update --init tpl/sm64-port
    
    pip install -r requirements/runtime.txt
    pip install -r requirements/headless.txt
    python generate_assets.py --dst tpl/sm64-port
    cd tpl/sm64-port

Launch MSYS2 MinGW 64-bit


c:\Users\erote\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\MSYS2\MSYS2 MINGW64.lnk

Launch: C:\msys64\mingw64.exe

Insall:

.. code::
    
    pacman -S git make python3 mingw-w64-x86_64-gcc

    cd ~/code/sm64-random-assets/tpl/sm64-port/

    make

Ok, apparently modern msys does not work, you need:
https://github.com/msys2/msys2-installer/releases/tag/2023-10-26

https://www.reddit.com/r/SuperMario64/comments/1eke8fk/cant_seem_to_get_super_mario_64_plus_to_build/


.. code:: 


Tutorial by Paradox:

"Quick announcement:
After the new GCC update, some repositories may fail to compile. So instead of waiting for a fix to be pushed, here's a little guide I made to temporarily get around this issue. Make sure you run the following commands in mingw64.exe:


1. Make a temporary directory to download GCC:

    mkdir c:/GCC
    cd c:/GCC

2. Use wget to download the specific version of GCC and GCC libraries. (If you don't have wget installed, run pacman -Syu wget:
    
    wget https://repo.msys2.org/mingw/mingw64/mingw-w64-x86_64-gcc-libs-13.2.0-2-any.pkg.tar.zst && wget https://repo.msys2.org/mingw/mingw64/mingw-w64-x86_64-gcc-13.2.0-2-any.pkg.tar.zst

3. Install the 2 packages:
    
    pacman -U mingw-w64-x86_64-gcc-13.2.0-2-any.pkg.tar.zst mingw-w64-x86_64-gcc-libs-13.2.0-2-any.pkg.tar.zst

4. Verify that the correct version is installed:

    gcc --version

5. After you confirm that the correct version is installed, reopen sm64pcbuilder2 and start compiling."
