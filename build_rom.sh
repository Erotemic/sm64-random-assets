#!/bin/bash
__doc__="
Build the ROM in this repo
"

# ROM-only dependencies
#sudo apt install -y binutils-mips-linux-gnu build-essential git libcapstone-dev pkgconf python3

# You can set your "code" directory path - the place where you will clone
# this repo - to be somewhere convenient for you
#CODE_DPATH=$HOME/code

## Ensure your code directory exists
#mkdir -p "$CODE_DPATH"

# Clone this repo
#git clone https://github.com/Erotemic/sm64-random-assets.git "$CODE_DPATH/sm64-random-assets"

# Move into the root of this repo and initialize the sm64 submodule,
# which will clone the official ROM-only sm64 repo.
#cd "$CODE_DPATH/sm64-random-assets" || exit
git submodule update --init tpl/sm64

# Run the asset generator
#python "$CODE_DPATH/sm64-random-assets/generate_assets.py" --dst "$CODE_DPATH/sm64-random-assets/tpl/sm64"



git clone ./tpl/sm64/.git ./tpl/sm64-ref

#(cd ./tpl/sm64-ref &&
# ipfs get ... -o "baserom.us.z64" && \
#make
#)

#python3 ./generate_assets.py --dst "tpl/sm64" --help
python3 ./generate_assets.py --dst "tpl/sm64" \
    --reference "./tpl/sm64-ref" \
    --hybrid_mode \
    --compare \
    --reference-config "
        png: 0
        aiff: 1
        m64: 0
        bin: 0
    "



# Compile
NUM_CPUS=$(nproc --all)

# Move into the ROM-only sm64 directory
( cd "tpl/sm64" && NOEXTRACT=1 COMPARE=0 NON_MATCHING=0 VERSION=us make -j"$NUM_CPUS" )

# The compiled ROM is: tpl/sm64/build/us/sm64.us.z64

cp tpl/sm64/build/us/sm64.us.z64 /media/joncrall/9DC3-BFF3/Custom/sm64.us.z64
