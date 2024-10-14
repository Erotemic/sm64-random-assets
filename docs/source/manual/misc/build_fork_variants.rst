Building Forked Variants
------------------------

By default this repo targets the stable sm64 or sm64-port repos. This document
provides quick invocations to build different variants.


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
   TARGET=sm64ex ./build.sh


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
   TARGET=Render96ex ./build.sh


SM64CoopDX
----------

.. code:: bash

   # Build and run the ROM in an emulator (m64py)
   export ASSET_CONFIG='
       png: generate
       aiff: generate
       m64: generate
       bin: generate
   '
   TARGET=SM64CoopDX ./build.sh
