#!/bin/bash
__doc__="
Build the ROM in this repo
"

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
    # Use bash magic to get the path to this file if running as a script
    THIS_DPATH=$(python -c "import pathlib; print(pathlib.Path('${BASH_SOURCE[0]}'))")
    echo "THIS_DPATH = $THIS_DPATH"
else
    # Assume CWD
    THIS_DPATH="."
fi

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


HYBRID_MODE=1
NUM_CPUS=$(nproc --all)
if [[ "$HYBRID_MODE" == "1" ]]; then
    REFERENCE_DPATH="$THIS_DPATH/tpl/sm64-ref"

    if ! test -d "$REFERENCE_DPATH" ; then
        git clone "$THIS_DPATH"/tpl/sm64/.git "$REFERENCE_DPATH"

        # Dont do this unless we have a proper copy, which we cannot provide here.
        # The correct baserom should have a sha256sum of
        # 17ce077343c6133f8c9f2d6d6d9a4ab62c8cd2aa57c40aea1f490b4c8bb21d91
        if type load_secrets; then
            load_secrets
            SM64_CID=$(load_secret_var sm64_cid)
            echo "SM64_CID = $SM64_CID"
            ipfs get "$SM64_CID" -o "$REFERENCE_DPATH/baserom.us.z64"
        fi
    fi

    if ! test -f "$REFERENCE_DPATH"/build/us/sm64.us.z64 ; then

        if test -f "$REFERENCE_DPATH/baserom.us.z64" ; then
            (cd "$REFERENCE_DPATH" && make "-j$NUM_CPUS")
        else
            echo "Reference ROM does not exist, cannot make reference build"
        fi
    fi
else
    REFERENCE_DPATH=None
fi


python3 -m sm64_random_assets --dst "$THIS_DPATH/tpl/sm64" \
    --reference "$REFERENCE_DPATH" \
    --hybrid_mode=$HYBRID_MODE \
    --compare=$HYBRID_MODE \
    --reference-config "
        png: generate
        aiff: reference
        m64: generate
        bin: generate
    "



# Compile
NUM_CPUS=$(nproc --all)

# Move into the ROM-only sm64 directory
( cd "$THIS_DPATH/tpl/sm64" && NOEXTRACT=1 COMPARE=0 NON_MATCHING=0 VERSION=us make -j"$NUM_CPUS" )

# The compiled ROM is: tpl/sm64/build/us/sm64.us.z64

EVERDRIVE_DPATH=/media/joncrall/9DC3-BFF3

if test -d $EVERDRIVE_DPATH ; then
    cp tpl/sm64/build/us/sm64.us.z64 "$EVERDRIVE_DPATH"/Custom/sm64.us.z64
fi
