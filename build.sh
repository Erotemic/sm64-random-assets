#!/bin/bash
__doc__="
Generate randomized assets and build the ROM.
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

NUM_CPUS=${NUM_CPUS:=$(nproc --all)}
BUILD=${BUILD:=1}

BUILD_REFERENCE=${BUILD_REFERENCE:=0}

# TARGET can be rom or pc
TARGET=${TARGET:="rom"}
#TARGET=${TARGET:="pc"}

TEST_LOCALLY=${TEST_LOCALLY:=0}

COMPARE=${COMPARE:=0}

EMULATOR=${EMULATOR:=m64py}

EVERDRIVE_DPATH=${EVERDRIVE_DPATH:=/media/$USER/9DC3-BFF3}

REFERENCE_CONFIG="
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
    COMPARE=$COMPARE
    REFERENCE_CONFIG=\"$REFERENCE_CONFIG
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

# Initialize the sm64 submodule, which clones the official ROM-only sm64 repo.

if [[ "$TARGET" == "rom" ]]; then
    SM64_REPO_DPATH="$THIS_DPATH"/tpl/sm64
    BINARY_TYPE="ROM"
    BINARY_FPATH="$SM64_REPO_DPATH"/build/us/sm64.us.z64
    REFERENCE_BINARY_FPATH="$REFERENCE_DPATH"/build/us/sm64.us.z64
elif [[ "$TARGET" == "pc" ]]; then
    SM64_REPO_DPATH="$THIS_DPATH"/tpl/sm64-port
    BINARY_TYPE="executable"
    BINARY_FPATH="$SM64_REPO_DPATH"/build/us_pc/sm64.us
    REFERENCE_BINARY_FPATH="$REFERENCE_DPATH"/build/us_pc/sm64.us
fi

echo "Ensure sm64 submodule exists"
git submodule update --init "$SM64_REPO_DPATH"

REFERENCE_DPATH="${SM64_REPO_DPATH}-ref"
REFERENCE_BASEROM_FPATH="$REFERENCE_DPATH/baserom.us.z64"
echo "REFERENCE_BASEROM_FPATH = $REFERENCE_BASEROM_FPATH"

if [[ "$BUILD_REFERENCE" == "1" ]]; then

    echo "Handle building the reference"

    if ! test -d "$REFERENCE_DPATH" ; then
        git clone "$SM64_REPO_DPATH"/.git "$REFERENCE_DPATH"
    fi

    if ! test -f "$REFERENCE_BASEROM_FPATH" ; then
        # Dont do this unless we have a proper copy, which we cannot provide here.
        # The correct us baserom should have a sha256sum of
        # 17ce077343c6133f8c9f2d6d6d9a4ab62c8cd2aa57c40aea1f490b4c8bb21d91
        if type -P secret_loader.sh; then
            # shellcheck disable=SC1090
            source "$(secret_loader.sh)"
            SM64_CID=$(load_secret_var sm64_us_cid)
            echo "SM64_CID = $SM64_CID"
            ipfs get "$SM64_CID" -o "$REFERENCE_BASEROM_FPATH"
        fi
    fi

    if ! test -f "$REFERENCE_BINARY_FPATH" ; then

        if test -f "$REFERENCE_BASEROM_FPATH" ; then
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

python3 -m sm64_random_assets \
    --dst "$SM64_REPO_DPATH" \
    --reference "$REFERENCE_DPATH" \
    --hybrid_mode="0" \
    --compare="$COMPARE" \
    --reference_config "$REFERENCE_CONFIG"


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
if [[ "$TARGET" == "rom" ]]; then
    echo "$EMULATOR" "$BINARY_FPATH"
elif [[ "$TARGET" == "pc" ]]; then
    echo "$BINARY_FPATH"
fi

if [[ "$TEST_LOCALLY" == "1" ]]; then
    if [[ "$TARGET" == "rom" ]]; then
        echo "Testing on emulator"
        "$EMULATOR" "$BINARY_FPATH"
    elif [[ "$TARGET" == "pc" ]]; then
        echo "Testing PC port"
        "$BINARY_FPATH"
    fi
fi
