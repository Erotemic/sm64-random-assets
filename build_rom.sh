#!/bin/bash
__doc__="
Generate randomized assets and build the ROM.
"

echo '
____ _  _  _   _ _    ____ ____ _  _ ___  ____ _  _    ____ ____ ____ ____ ___ ____
[__  |\/|  |_  |_|    |__/ |__| |\ | |  \ |  | |\/|    |__| [__  [__  |___  |  [__
___] |  |  |_|   |    |  \ |  | | \| |__/ |__| |  |    |  | ___] ___] |___  |  ___]

'

HYBRID_MODE=${HYBRID_MODE:=0}
NUM_CPUS=${NUM_CPUS:=$(nproc --all)}
BUILD_ROM=${BUILD_ROM:=1}
TEST_ON_EMULATOR=${TEST_ON_EMULATOR:=0}
REFERENCE_CONFIG="
    png: generate
    aiff: reference
    m64: reference
    bin: reference
"


if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
    # Use bash magic to get the path to this file if running as a script
    THIS_DPATH=$(python3 -c "import pathlib; print(pathlib.Path('${BASH_SOURCE[0]}').parent.absolute())")
	set -eo pipefail
else
    # Assume CWD
    THIS_DPATH=$(python3 -c "import pathlib; print(pathlib.Path('.').parent.absolute())")
fi

python3 -c "
import ubelt as ub

print(ub.color_text('''
BUILD ROM CONFIGURATION
=======================
''', 'green'))

print(ub.highlight_code('''

THIS_DPATH=$THIS_DPATH
NUM_CPUS=$NUM_CPUS

HYBRID_MODE=$HYBRID_MODE
REFERENCE_CONFIG=\"$REFERENCE_CONFIG\"

BUILD_ROM=$BUILD_ROM

''', lexer_name='bash'))
"

# ROM-only dependencies
#sudo apt install -y binutils-mips-linux-gnu build-essential git libcapstone-dev pkgconf python3

# Initialize the sm64 submodule, which clones the official ROM-only sm64 repo.
echo "Ensure sm64 submodule exists"
git submodule update --init tpl/sm64


if [[ "$HYBRID_MODE" == "1" ]]; then
    echo "Handling hybrid mode"
    REFERENCE_DPATH="$THIS_DPATH/tpl/sm64-ref"

    if ! test -d "$REFERENCE_DPATH" ; then
        git clone "$THIS_DPATH"/tpl/sm64/.git "$REFERENCE_DPATH"

        # Dont do this unless we have a proper copy, which we cannot provide here.
        # The correct baserom should have a sha256sum of
        # 17ce077343c6133f8c9f2d6d6d9a4ab62c8cd2aa57c40aea1f490b4c8bb21d91
        if type load_secrets; then
            load_secrets
            SM64_CID=$(load_secret_var sm64_us_cid)
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
    REFERENCE_DPATH="$THIS_DPATH/tpl/sm64-ref"
fi

if ! test -d "$REFERENCE_DPATH" ; then
    REFERENCE_DPATH=None
fi


# Run the asset generator
python3 -c "if 1:
    import ubelt as ub
    print(ub.color_text(ub.codeblock('''

    Run Asset Generator
    ===================
    '''), 'green'))
"

python3 -m sm64_random_assets --dst "$THIS_DPATH/tpl/sm64" \
    --reference "$REFERENCE_DPATH" \
    --hybrid_mode="$HYBRID_MODE" \
    --compare="$HYBRID_MODE" \
    --reference_config "$REFERENCE_CONFIG"


# Compile
if [[ "$BUILD_ROM" == "1" ]]; then
    python3 -c "if 1:
        import ubelt as ub
        print(ub.color_text(ub.codeblock('''

        Compile the ROM
        ===============
        '''), 'green'))
    "
    # Move into the ROM-only sm64 directory
    ( cd "$THIS_DPATH/tpl/sm64" && make clean && NOEXTRACT=1 COMPARE=0 NON_MATCHING=0 VERSION=us make -j"$NUM_CPUS" )
fi

# The compiled ROM is: tpl/sm64/build/us/sm64.us.z64

# Run the asset generator
python3 -c "if 1:
    import ubelt as ub
    print(ub.color_text(ub.codeblock('''

    Finalize
    ========
    '''), 'green'))
"
echo "Finalizing, the path to the ROM is:"
echo "$THIS_DPATH/tpl/sm64/build/us/sm64.us.z64"

EVERDRIVE_DPATH=/media/$USER/9DC3-BFF3

if test -d "$EVERDRIVE_DPATH" ; then
    echo "Copying ROM to EverDrive directory"
    cp "$THIS_DPATH"/tpl/sm64/build/us/sm64.us.z64 "$EVERDRIVE_DPATH"/Custom/sm64.us.z64
    echo "EVERDRIVE_DPATH = $EVERDRIVE_DPATH"
    ls -al "$EVERDRIVE_DPATH"/Custom/
else
    echo "No EverDrive detected."
fi

if [[ "$TEST_ON_EMULATOR" == "1" ]]; then
    echo "Testing on emulator"
    mupen64plus-qt "$THIS_DPATH"/tpl/sm64/build/us/sm64.us.z64
fi
