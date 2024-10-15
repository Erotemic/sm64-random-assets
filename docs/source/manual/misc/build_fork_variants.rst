Building Forked Variants
------------------------

By default this repo targets the stable sm64 or sm64-port repos. This document
provides quick invocations to build different variants.

Note: currently only sm64 and sm64-port have been robustly tested, and other
variants may need development effort to fully support.

sm64
----

The original ROM decomp.

.. code:: bash

   sudo apt install -y binutils-mips-linux-gnu build-essential git libcapstone-dev pkgconf python3

   # Build and run the ROM in an emulator (m64py)
   export TEST_LOCALLY=0
   export ASSET_CONFIG='
       png: generate
       aiff: generate
       m64: generate
       bin: generate
   '
   export NUM_CPUS=all
   export TARGET=sm64
   ./build.sh


sm64-port
---------

The original PC port.

.. code:: bash

   export EXTERNAL_ROM_FPATH=baserom.us.z64
   export BUILD_REFERENCE=1
   export ASSET_CONFIG='
       png: generate
       aiff: generate
       m64: generate
       bin: generate
   '
   export NUM_CPUS=1
   export TARGET=sm64-port
   ./build.sh


sm64ex
------

An extension of the PC port with extra features.

.. code:: bash

   # Build and run the ROM in an emulator (m64py)
   export ASSET_CONFIG='
       png: generate
       aiff: generate
       m64: generate
       bin: generate
   '
   export NUM_CPUS=all
   export TARGET=sm64ex
   ./build.sh


Render96ex
----------

An extension of sm64ex with even more features.

.. code:: bash

   # Build the Render96ex port
   export ASSET_CONFIG='
       png: generate
       aiff: generate
       m64: generate
       bin: generate
   '
   export NUM_CPUS=all
   export TARGET=Render96ex
   ./build.sh


SM64CoopDX
----------

An extension of PC port with co-op

.. code:: bash

   # Build the SM64CoopDX port
   export EXTERNAL_ROM_FPATH=baserom.us.z64
   export BUILD_REFERENCE=0
   export ASSET_CONFIG='
       png: generate
       aiff: generate
       m64: generate
       bin: generate
   '
   export NUM_CPUS=all
   export TARGET=SM64CoopDX
   ./build.sh
