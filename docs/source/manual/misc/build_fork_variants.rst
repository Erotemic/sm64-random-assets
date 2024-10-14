Building Forked Variants
------------------------

By default this repo targets the stable sm64 or sm64-port repos. This document
provides quick invocations to build different variants.

sm64
----



.. code:: bash

   sudo apt install -y binutils-mips-linux-gnu build-essential git libcapstone-dev pkgconf python3

   # Build and run the ROM in an emulator (m64py)
   export ASSET_CONFIG='
       png: generate
       aiff: generate
       m64: generate
       bin: generate
   '
   export NUM_CPUS=all
   export TARGET=sm64
   ./build.sh


sm64ex
------

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

.. code:: bash

   # Build and run the ROM in an emulator (m64py)
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

.. code:: bash

   # Build and run the ROM in an emulator (m64py)
   export EXTERNAL_ROM_FPATH=baserom.us.z64
   export BUILD_REFERENCE=1
   export ASSET_CONFIG='
       png: generate
       aiff: generate
       m64: generate
       bin: generate
   '
   export NUM_CPUS=1
   export TARGET=SM64CoopDX
   ./build.sh
