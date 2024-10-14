Third Party Libraries
---------------------

This directory contains two git submodules:

* ``sm64``, which is the original ROM-only decompolation

* ``sm64-port``, which is the sm64 decomplation with extra code to run it on a PC.

* ``sm64ex``, an extension of sm64-port with extra features.

* ``Render96ex``, testing if this is supported.

* ``SM64CoopDX``, testing if this is supported.


This repo does not require you to have these repos checked out as submodules;
the scripts can point at independent clones of either, but having them
accessible here does offer a convinient way to write instructions and internal
tests.

As a `reminder <https://git-scm.com/book/en/v2/Git-Tools-Submodules>`_, after
you clone a repository with submodules you need to initialize them seprately.


To initialize all submodules:

.. code:: bash

   submodule update --init --recursive



Assuming you are in the root of this repo, to initialize / update a specific
submodule, use on of the following commands:


For the ROM-only ``sm64`` decomp use:

.. code:: bash

   git submodule update --init tpl/sm64


And for the PC-port ``sm64-port`` use:

.. code:: bash

   git submodule update --init tpl/sm64-port



To build with a specific variant try:

.. code:: bash


    # export TARGET=rom
    # export TARGET=pc

    # export TARGET=SM64CoopDX  # currently has a bug
    # src/pc/mumble/mumble.c:21:18: fatal error: libc.h: No such file or directory

    export TARGET=Render96ex  # urrently has a bug
    # src/pc/mumble/mumble.c:21:18: fatal error: libc.h: No such file or directory

    export NUM_CPUS=all
    export ASSET_CONFIG='
        png: generate
        aiff: generate
        m64: generate
        bin: generate
    '
    ./build.sh


    # or after generating assets run
    NOEXTRACT=1 COMPARE=0 NON_MATCHING=0 VERSION=us make
