#!/bin/bash
__doc__="
Generate randomized assets and build the ROM.


To build an end-to-end randomized executable:

.. code:: bash

    ./build.sh


To build a PC port with original assets
(requires personal copy of the original ROM):

.. code:: bash

    # Replace this with some method to ensure a reference baserom exists if you
    # manually place the baserom in the cwd with this path then you can remove
    # this line.
    ./dev/grab_reference_baserom.sh ./baserom.us.z64

    export EXTERNAL_ROM_FPATH=baserom.us.z64
    export TARGET=pc
    export BUILD_REFERENCE=1
    export COMPARE=1
    export NUM_CPUS=all
    export ASSET_CONFIG='
        png: generate
        aiff: generate
        m64: generate
        bin: generate
    '
    ./build.sh

"

echo '
____ _  _  _   _ _    ____ ____ _  _ ___  ____ _  _    ____ ____ ____ ____ ___ ____
[__  |\/|  |_  |_|    |__/ |__| |\ | |  \ |  | |\/|    |__| [__  [__  |___  |  [__
___] |  |  |_|   |    |  \ |  | | \| |__/ |__| |  |    |  | ___] ___] |___  |  ___]

'

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
    # Use bash magic to get the path to this file if running as a script
    THIS_DPATH=$(python3 -c "import pathlib; print(pathlib.Path('${BASH_SOURCE[0]}').parent.absolute())")
	set -eo pipefail
else
    # Assume CWD
    THIS_DPATH=$(python3 -c "import pathlib; print(pathlib.Path('.').parent.absolute())")
fi

NUM_CPUS=${NUM_CPUS:=}
BUILD=${BUILD:=1}

BUILD_REFERENCE=${BUILD_REFERENCE:=0}

EXTERNAL_ROM_FPATH=${EXTERNAL_ROM_FPATH:=""}

# TARGET can be rom or pc
#TARGET=${TARGET:="rom"}
TARGET=${TARGET:="pc"}

TEST_LOCALLY=${TEST_LOCALLY:=0}

COMPARE=${COMPARE:=0}

# Default to an existing emulator if possible
if command -v mupen64plus &>/dev/null; then
    # requires: sudo apt install mupen64plus-qt
    EMULATOR=${EMULATOR:=mupen64plus}
else
    EMULATOR=${EMULATOR:=m64py}
fi

EVERDRIVE_DPATH=${EVERDRIVE_DPATH:=/media/$USER/9DC3-BFF3}

if [[ "$NUM_CPUS" == "all" ]]; then
    NUM_CPUS=$(nproc --all)
fi


# This config is passed to sm64_random_assets/main.py
# and controls how assets will be generated
DEFAULT_ASSET_CONFIG="
    png: generate
    aiff: generate
    m64: generate
    bin: generate

    #aiff: reference
    #m64: reference
    #bin: reference

    #never_generate:
    #  - '*bowser_flame*png'
    #  #- '*bowser*png'
"
ASSET_CONFIG=${ASSET_CONFIG:=$DEFAULT_ASSET_CONFIG}

python3 -c "if 1:
    import ubelt as ub

    print(ub.color_text(ub.codeblock('''
    CONFIGURATION
    =============
    '''), 'green'))

    print(ub.highlight_code(ub.codeblock('''

    THIS_DPATH=$THIS_DPATH
    NUM_CPUS=$NUM_CPUS

    TARGET=$TARGET

    BUILD=$BUILD

    TEST_LOCALLY=$TEST_LOCALLY

    BUILD_REFERENCE=$BUILD_REFERENCE
    EXTERNAL_ROM_FPATH=$EXTERNAL_ROM_FPATH
    COMPARE=$COMPARE
    ASSET_CONFIG=\"$ASSET_CONFIG
    \"

    '''), lexer_name='bash'))

    if '$TARGET' == 'rom':
        print(ub.highlight_code(ub.codeblock('''

        EVERDRIVE_DPATH=$EVERDRIVE_DPATH
        EMULATOR=$EMULATOR

        '''), lexer_name='bash'))
"

# ROM-only dependencies
#sudo apt install -y binutils-mips-linux-gnu build-essential git libcapstone-dev pkgconf python3


if [[ "$EXTERNAL_ROM_FPATH" != "" ]]; then
    echo "User specified an external ROM with original assets"
    echo "Checking external ROM hash"
    echo "$EXTERNAL_ROM_FPATH"
    echo "17ce077343c6133f8c9f2d6d6d9a4ab62c8cd2aa57c40aea1f490b4c8bb21d91 $EXTERNAL_ROM_FPATH" | sha256sum --check --status
    _RESULT=$?
    if [[ "$_RESULT" == "0" ]]; then
        echo "Externally specified ROM has the expected hash"
    else
        echo "WARNING: Externally specified ROM has an UNEXPECTED hash!"
        sha256sum "$EXTERNAL_ROM_FPATH"
    fi
fi


if [[ "$TARGET" == "rom" || "$TARGET" == "sm64" ]]; then
    SM64_REPO_DPATH="$THIS_DPATH"/tpl/sm64
    BINARY_TYPE="ROM"
    BINARY_FPATH="$SM64_REPO_DPATH"/build/us/sm64.us.z64
    REFERENCE_BINARY_FPATH="$REFERENCE_DPATH"/build/us/sm64.us.z64
    EXECUTE_INVOCATION="$EMULATOR $BINARY_FPATH"
elif [[ "$TARGET" == "pc" || "$TARGET" == "sm64-port" ]]; then
    SM64_REPO_DPATH="$THIS_DPATH"/tpl/sm64-port
    BINARY_TYPE="executable"
    BINARY_FPATH="$SM64_REPO_DPATH"/build/us_pc/sm64.us
    REFERENCE_BINARY_FPATH="$REFERENCE_DPATH"/build/us_pc/sm64.us
    EXECUTE_INVOCATION="$BINARY_FPATH"
elif [[ "$TARGET" == "sm64ex" ]]; then
    SM64_REPO_DPATH="$THIS_DPATH"/tpl/sm64ex
    BINARY_TYPE="executable"
    BINARY_FPATH="$SM64_REPO_DPATH"/build/us_pcsm64.us.f3dex2e
    REFERENCE_BINARY_FPATH="$REFERENCE_DPATH"/build/us_pc/sm64.us.f3dex2e
    EXECUTE_INVOCATION="$BINARY_FPATH"
elif [[ "$TARGET" == "Render96ex" ]]; then
    SM64_REPO_DPATH="$THIS_DPATH"/tpl/Render96ex
    BINARY_TYPE="executable"
    BINARY_FPATH="$SM64_REPO_DPATH"/build/us_pc/sm64.us.f3dex2e
    REFERENCE_BINARY_FPATH="$REFERENCE_DPATH"/build/us_pc/sm64.us.f3dex2e
    EXECUTE_INVOCATION="$BINARY_FPATH"
elif [[ "$TARGET" == "SM64CoopDX" ]]; then
    SM64_REPO_DPATH="$THIS_DPATH"/tpl/sm64coopdx
    BINARY_TYPE="executable"
    BINARY_FPATH="$SM64_REPO_DPATH"/build/us_pc/sm64.us
    REFERENCE_BINARY_FPATH="$REFERENCE_DPATH"/build/us_pc/sm64.us
    EXECUTE_INVOCATION="$BINARY_FPATH"
fi

# Initialize the specific sm64 submodule variant you want to build against
echo "Ensure the sm64 variant ($TARGET) submodule exists"
git submodule update --init "$SM64_REPO_DPATH"

REFERENCE_DPATH="${SM64_REPO_DPATH}-ref"
REFERENCE_BASEROM_FPATH="$REFERENCE_DPATH/baserom.us.z64"
echo "REFERENCE_BASEROM_FPATH = $REFERENCE_BASEROM_FPATH"

if [[ "$BUILD_REFERENCE" == "1" ]]; then

    echo "Handle building the reference"

    if ! test -d "$REFERENCE_DPATH" ; then
        echo "Need to clone the reference repo"
        git clone "$SM64_REPO_DPATH"/.git "$REFERENCE_DPATH"
    else
        echo "Reference repo is already cloned"
    fi

    if ! test -f "$REFERENCE_BASEROM_FPATH" ; then
        echo "Reference repo does not have the baserom, need to copy it"
        # Dont do this unless we have a proper copy, which we cannot provide here.
        # The correct us baserom should have a sha256sum of
        # 17ce077343c6133f8c9f2d6d6d9a4ab62c8cd2aa57c40aea1f490b4c8bb21d91

        if [[ "$EXTERNAL_ROM_FPATH" != "" ]]; then
            # Externally supplied path to personal copy of the ROM
            echo "Copying personal copy of the ROM to the reference path"
            cp "$EXTERNAL_ROM_FPATH" "$REFERENCE_BASEROM_FPATH"
        else
            echo "ERROR: Specify EXTERNAL_ROM_FPATH"
        fi
    else
        echo "Reference repo already had a baserom"
    fi

    if ! test -f "$REFERENCE_BINARY_FPATH" ; then

        if test -f "$REFERENCE_BASEROM_FPATH" ; then
            echo "Building the reference binary"
            (cd "$REFERENCE_DPATH" && make "-j$NUM_CPUS")
        else
            echo "Reference ROM does not exist, cannot make reference build"
            exit 1
        fi
    fi
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

python3 -m sm64_random_assets generate \
    --dst "$SM64_REPO_DPATH" \
    --reference "$REFERENCE_DPATH" \
    --hybrid_mode="0" \
    --compare="$COMPARE" \
    --asset_config "$ASSET_CONFIG"


# Compile
if [[ "$BUILD" == "1" ]]; then
    python3 -c "if 1:
        import ubelt as ub
        print(ub.color_text(ub.codeblock('''

        Compile the ROM
        ===============
        '''), 'green'))
    "
    # Move into the ROM-only sm64 directory
    # FIXME: Annoying that we need a "make clean" here otherwise the sm64 build
    # wont realize the assets have changed. There might be a faster way to make
    # the makefiles aware of this without needing to start from scratch each
    # time.
    ( cd "$SM64_REPO_DPATH" && make clean && NOEXTRACT=1 COMPARE=0 NON_MATCHING=0 VERSION=us make -j"$NUM_CPUS" )
    #( cd "$SM64_REPO_DPATH" && NOEXTRACT=1 COMPARE=0 NON_MATCHING=0 VERSION=us make -j"$NUM_CPUS" )
fi

# Run the asset generator
python3 -c "if 1:
    import ubelt as ub
    print(ub.color_text(ub.codeblock('''

    Finalize
    ========
    '''), 'green'))
    print(ub.highlight_code(ub.codeblock('''

    BINARY_TYPE=$BINARY_TYPE
    BINARY_FPATH=$BINARY_FPATH

    TEST_LOCALLY=$TEST_LOCALLY
    '''), lexer_name='bash'))

    if '$TARGET' == 'rom':
        print(ub.highlight_code(ub.codeblock('''

        EVERDRIVE_DPATH=$EVERDRIVE_DPATH
        EMULATOR=$EMULATOR

        '''), lexer_name='bash'))

"

if [[ "$TARGET" == "rom" ]]; then
    if test -d "$EVERDRIVE_DPATH" ; then
        echo "Copying ROM to EverDrive directory"
        cp "$BINARY_FPATH" "$EVERDRIVE_DPATH"/Custom/sm64.us.z64
        echo "EVERDRIVE_DPATH = $EVERDRIVE_DPATH"
        ls -al "$EVERDRIVE_DPATH"/Custom/
    else
        echo "No EverDrive detected."
    fi
fi

echo "To execute locally use: "
echo "$EXECUTE_INVOCATION"

if [[ "$TEST_LOCALLY" == "1" ]]; then
    echo "Testing locally"
    $EXECUTE_INVOCATION
fi
