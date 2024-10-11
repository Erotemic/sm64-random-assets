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


MSYS2
-----

We need MSYS2 which contains the tools needed to build C code and libraries
required by sm64-port. Unfortunately as of 2024-10-09, the latest version of
MSYS does not work with this codebase. We need to install an older version from
2023-10-26. The link to this working version of MSYS is here:

https://github.com/msys2/msys2-installer/releases/tag/2023-10-26

Download the exe installer and run it to install MSYS and MinGW64, which is the
component we will actually use.


Now, open the "MSYS2 MinGW64 Shell", which should be available in your start
menu. If you cannot find it, the executable should live in
``C:\msys64\mingw64.exe``.


Once the shell is open, we use the ``pacman`` package manager to install the
required mingw packages:

.. code::

    pacman --sync --noconfirm git make python3 mingw-w64-x86_64-gcc


Git The Code
------------

In the MSYS MinGW64 Shell, we have now installed git, which means we can
download the code.

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


The above only gives us the asset generation code. We need a sm64 submodule,
which is a third party library, and we can get that by telling git to
initialize the submodules.

.. code::

    git submodule update --init tpl/sm64-port

MSYS2 Python
------------

We could try to use the MinGW version of Python to generate random assets, which will require additional packages from pacman.
I have not had full success with this method yet.

With msys, some precompiled Python packages do no work, so it will try to build
them from source, which is brittle and can easilly fail. However, we can try to
avoid this by using the pacman versions of those packages.

.. code::

    pacman --sync --noconfirm \
        mingw-w64-x86_64-python-pip \
        mingw-w64-x86_64-python-numpy \
        mingw-w64-x86_64-python-scipy \
        mingw-w64-x86_64-python-matplotlib \
        mingw-w64-x86_64-python-opencv \
        mingw-w64-x86_64-python-scikit-image \
        mingw-w64-x86_64-python-yaml \
        mingw-w64-x86_64-python-shapely \
        mingw-w64-x86_64-cmake \
        mingw-w64-x86_64-geos

Once these core binary packages are installed, we can try to procede with the
installation of the rest of the tools needed for the asset generator.


Windows Python
--------------

The alternative is a native windows install of Python. I'm not sure exactly how
to get this. The way I've gotten it in the past is opening vscode, then opening
a powershell terminal in vscode and typing Python. It then takes me to a prompt
asking me if I want to install it. I say yes, and that gives me access to
Python in powershell.

.. code:: bash

    python3 -m pip install -r requirements/runtime.txt
    pip install -r requirements/headless.txt
    python generate_assets.py --dst tpl/sm64-port


Building The Code
-----------------

Once you have generated the assets, then in a MSYS MinGW64 shell, we
need to navigate to the sm64-port source code folder.

.. code::

    cd tpl/sm64-port


Once in the folder you can execute the build sequence with the ``make`` command:

.. code::

    make


This will only work if you have

1. Generated the random assets OR
2. Have put a legal copy of ``baserom.us.z64`` into this sm64-port folder.
   (Which is just the standard sm64-port build without random assets).



2024 MSYS Workaround
--------------------

Ok, apparently modern msys does not work, you need:
https://github.com/msys2/msys2-installer/releases/tag/2023-10-26

https://www.reddit.com/r/SuperMario64/comments/1eke8fk/cant_seem_to_get_super_mario_64_plus_to_build/

If you already have a modern MSYS install, there is a workaround discussed on
the sm64 discord, but I have not tested it. I will post it here in case it
helps:


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
