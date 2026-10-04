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


To compile assets that are already present in the selected SM64 variant:

.. code:: bash

    export ASSET_MODE=reuse
    ./build.sh


To build directly from original baserom assets without running the random
asset generator:

.. code:: bash

    export BASEROM_FPATH=baserom.us.z64
    ./build.sh


To build natively for Steam Frame without compiling on the headset:

.. code:: bash

    export PRESET=steamframe
    ./build.sh

The additional build dimensions are independent:

    VARIANT     Which SM64 codebase to build (sm64-port, sm64ex, ...)
    TARGET      Which execution/runtime target to build for
    PRESET      Human-friendly target preset (steamframe, steamdeck, ...)
    ASSET_MODE  generate, reuse, or baserom

Legacy TARGET=pc / TARGET=rom / TARGET=<variant> spellings remain accepted.
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

# Keep the original build.sh as the authority for orchestration and presentation.
# The helper only resolves the newly separated build dimensions.
# shellcheck source=dev/build_config.sh
source "$THIS_DPATH/dev/build_config.sh"
sm64ra_resolve_build_config
sm64ra_resolve_asset_config

NUM_CPUS=${NUM_CPUS:=}
BUILD=${BUILD:=1}

BUILD_REFERENCE=${BUILD_REFERENCE:=0}

EXTERNAL_ROM_FPATH=${EXTERNAL_ROM_FPATH:=""}
BASEROM_FPATH=${BASEROM_FPATH:=""}

TEST_LOCALLY=${TEST_LOCALLY:=0}

COMPARE=${COMPARE:=0}
TARGET_QUALITY=${TARGET_QUALITY:=1}
INCLUDE_AUTHORS=${INCLUDE_AUTHORS:='*'}
EXCLUDE_AUTHORS=${EXCLUDE_AUTHORS:=''}

SM64RA_TARGET_CONTAINER=${SM64RA_TARGET_CONTAINER:=0}
SM64RA_PYTHON=${SM64RA_PYTHON:-python3}

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

# Steam Runtime targets are built in their target-architecture SDK containers.
# Keep the host script thin: the same build.sh is re-entered in the container.
if sm64ra_is_container_target "$TARGET" && [[ "$BUILD" == "1" && "$SM64RA_TARGET_CONTAINER" != "1" ]]; then
    exec "$THIS_DPATH/dev/build_steamrt_target.sh"
fi

if sm64ra_is_container_target "$TARGET" && [[ "$SM64RA_TARGET_CONTAINER" == "1" ]]; then
    EXPECTED_ARCH=$(sm64ra_target_arch "$TARGET")
    HOST_ARCH=$(sm64ra_host_arch)
    if [[ "$EXPECTED_ARCH" != "$HOST_ARCH" ]]; then
        echo "ERROR: $TARGET requires $EXPECTED_ARCH, but the build container reports $HOST_ARCH" >&2
        exit 2
    fi
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

SM64_REPO_REL_DPATH=$(sm64ra_variant_repo_relpath "$VARIANT")
SM64_REPO_DPATH="$THIS_DPATH/$SM64_REPO_REL_DPATH"
BINARY_REL_FPATH=$(sm64ra_variant_binary_relpath "$VARIANT")
BINARY_TYPE=$(sm64ra_variant_binary_type "$VARIANT")
BINARY_FPATH="$SM64_REPO_DPATH/$BINARY_REL_FPATH"
REFERENCE_DPATH="${SM64_REPO_DPATH}-ref"
REFERENCE_BASEROM_FPATH="$REFERENCE_DPATH/baserom.us.z64"
REFERENCE_BINARY_FPATH="$REFERENCE_DPATH/$BINARY_REL_FPATH"

if [[ "$TARGET" == "n64" ]]; then
    EXECUTE_INVOCATION="$EMULATOR $BINARY_FPATH"
else
    EXECUTE_INVOCATION="$BINARY_FPATH"
fi

"$SM64RA_PYTHON" -c "if 1:
    import ubelt as ub

    print(ub.color_text(ub.codeblock('''
    CONFIGURATION
    =============
    '''), 'green'))

    print(ub.highlight_code(ub.codeblock('''

    THIS_DPATH=$THIS_DPATH
    NUM_CPUS=$NUM_CPUS

    PRESET=${PRESET:-}
    VARIANT=$VARIANT
    TARGET=$TARGET
    ASSET_MODE=$ASSET_MODE

    BUILD=$BUILD

    TEST_LOCALLY=$TEST_LOCALLY

    BUILD_REFERENCE=$BUILD_REFERENCE
    EXTERNAL_ROM_FPATH=$EXTERNAL_ROM_FPATH
    BASEROM_FPATH=$BASEROM_FPATH
    COMPARE=$COMPARE
    ASSET_CONFIG=\"$ASSET_CONFIG
    \"

    '''), lexer_name='bash'))

    if '$TARGET' == 'n64':
        print(ub.highlight_code(ub.codeblock('''

        EVERDRIVE_DPATH=$EVERDRIVE_DPATH
        EMULATOR=$EMULATOR

        '''), lexer_name='bash'))
"

# ROM-only dependencies
#sudo apt install -y binutils-mips-linux-gnu build-essential git libcapstone-dev pkgconf python3


if [[ "$BASEROM_FPATH" != "" ]]; then
    echo "User specified a baserom with original assets"
    echo "Checking baserom hash"
    echo "$BASEROM_FPATH"
    echo "17ce077343c6133f8c9f2d6d6d9a4ab62c8cd2aa57c40aea1f490b4c8bb21d91 $BASEROM_FPATH" | sha256sum --check --status
    _RESULT=$?
    if [[ "$_RESULT" == "0" ]]; then
        echo "Externally specified ROM has the expected hash"
    else
        echo "WARNING: Externally specified ROM has an UNEXPECTED hash!"
        sha256sum "$BASEROM_FPATH"
    fi
fi

# Initialize the specific sm64 submodule variant you want to build against
echo "Ensure the sm64 variant ($VARIANT) submodule exists"
git -C "$THIS_DPATH" submodule update --init "$SM64_REPO_REL_DPATH"

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
            echo "ERROR: Specify BASEROM_FPATH or EXTERNAL_ROM_FPATH"
        fi
    else
        echo "Reference repo already had a baserom"
    fi

    if ! test -f "$REFERENCE_BINARY_FPATH" ; then

        if test -f "$REFERENCE_BASEROM_FPATH" ; then
            echo "Building the reference binary"
            (cd "$REFERENCE_DPATH" && make "-j$NUM_CPUS" PYTHON="$SM64RA_PYTHON")
        else
            echo "Reference ROM does not exist, cannot make reference build"
            exit 1
        fi
    fi
fi

if ! test -d "$REFERENCE_DPATH" ; then
    REFERENCE_DPATH=None
fi

SM64RA_TOOLS_PREPARED=0
sm64ra_prepare_native_tools() {
    if [[ "$SM64RA_TOOLS_PREPARED" == "1" ]]; then
        return
    fi
    SM64RA_TOOLS_PREPARED=1

    local tools_dpath="$SM64_REPO_DPATH/tools"
    if [[ ! -f "$tools_dpath/Makefile" ]]; then
        return
    fi

    local clean_tools=0
    if sm64ra_is_container_target "$TARGET"; then
        # SteamRT bind-mounts the source tree, so a helper built for a previous
        # host/target can be the wrong ISA even when make considers it current.
        clean_tools=1
    else
        local helper helper_desc host_arch
        host_arch=$(sm64ra_host_arch)
        for helper in textconv mio0 n64graphics skyconv; do
            if [[ -x "$tools_dpath/$helper" ]]; then
                helper_desc=$(file -b "$tools_dpath/$helper" 2>/dev/null || true)
                case "$host_arch:$helper_desc" in
                    x86_64:*x86-64*|x86_64:*x86_64*|aarch64:*ARM\ aarch64*|aarch64:*ARM64*) ;;
                    *) clean_tools=1 ;;
                esac
                break
            fi
        done
    fi

    if [[ "$clean_tools" == "1" ]]; then
        echo "Cleaning native SM64 helper tools for target environment"
        make -s -C "$tools_dpath" clean
    fi
}

SM64RA_STAGED_BASEROM=0
sm64ra_unstage_baserom() {
    if [[ "$SM64RA_STAGED_BASEROM" == "1" ]]; then
        rm -f "$SM64_REPO_DPATH/baserom.us.z64"
        SM64RA_STAGED_BASEROM=0
    fi
}
sm64ra_stage_baserom() {
    local dst="$SM64_REPO_DPATH/baserom.us.z64"
    local src
    src=$(readlink -f "$BASEROM_FPATH")

    if [[ -e "$dst" || -L "$dst" ]]; then
        local current
        current=$(readlink -f "$dst" 2>/dev/null || true)
        if [[ "$current" != "$src" ]]; then
            echo "ERROR: refusing to replace existing $dst with BASEROM_FPATH=$src" >&2
            exit 2
        fi
        return
    fi

    ln -s "$src" "$dst"
    SM64RA_STAGED_BASEROM=1
    trap sm64ra_unstage_baserom EXIT
}

# Prepare the requested asset source. Only ASSET_MODE=generate runs the random
# asset generator. BASEROM_FPATH always selects ASSET_MODE=baserom; use
# EXTERNAL_ROM_FPATH when a ROM is only being supplied for a reference build.
if [[ "$ASSET_MODE" == "generate" ]]; then
    # Run the asset generator
    "$SM64RA_PYTHON" -c "if 1:
        import ubelt as ub
        print(ub.color_text(ub.codeblock('''

        Run Asset Generator
        ===================
        '''), 'green'))
    "

    "$SM64RA_PYTHON" -m sm64_random_assets generate \
        --dst "$SM64_REPO_DPATH" \
        --reference "$REFERENCE_DPATH" \
        --hybrid_mode="0" \
        --compare="$COMPARE" \
        --target_quality="$TARGET_QUALITY" \
        --include_authors "$INCLUDE_AUTHORS" \
        --exclude_authors "$EXCLUDE_AUTHORS" \
        --asset_config "$ASSET_CONFIG"

elif [[ "$ASSET_MODE" == "reuse" ]]; then
    "$SM64RA_PYTHON" -c "if 1:
        import ubelt as ub
        print(ub.color_text(ub.codeblock('''

        Reuse Existing Assets
        =====================
        '''), 'green'))
    "
    echo "Skipping asset generation/extraction; using assets already present in $SM64_REPO_DPATH"

elif [[ "$ASSET_MODE" == "baserom" ]]; then
    if [[ "$BASEROM_FPATH" == "" ]]; then
        if test -f "$SM64_REPO_DPATH/baserom.us.z64" ; then
            BASEROM_FPATH="$SM64_REPO_DPATH/baserom.us.z64"
        else
            echo "ERROR: ASSET_MODE=baserom requires BASEROM_FPATH or an existing $SM64_REPO_DPATH/baserom.us.z64" >&2
            exit 2
        fi
    fi

    "$SM64RA_PYTHON" -c "if 1:
        import ubelt as ub
        print(ub.color_text(ub.codeblock('''

        Use Base ROM Assets
        ===================
        '''), 'green'))
    "

    echo "Skipping the random asset generator; cleaning any previously generated assets and extracting originals from:"
    echo "$BASEROM_FPATH"
    sm64ra_prepare_native_tools
    sm64ra_stage_baserom
    (
        cd "$SM64_REPO_DPATH"
        "$SM64RA_PYTHON" extract_assets.py --clean
        "$SM64RA_PYTHON" extract_assets.py us
    )
    # The prepared source tree no longer needs the ROM for compilation because
    # the compile step always uses NOEXTRACT=1.
    sm64ra_unstage_baserom
    trap - EXIT
fi


# Compile
if [[ "$BUILD" == "1" ]]; then
    "$SM64RA_PYTHON" -c "if 1:
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
    sm64ra_prepare_native_tools

    # Keep the original compile semantics: assets are prepared before make and
    # native builds compile that prepared tree with extraction disabled. Frame
    # sm64ex builds additionally pin a conservative ARMv8 target and make the
    # SDL2 frontend explicit rather than relying on GLX or QEMU's -march=native.
    SM64RA_MAKE_ARGS=(
        NOEXTRACT=1
        COMPARE=0
        NON_MATCHING=0
        VERSION=us
        "PYTHON=$SM64RA_PYTHON"
    )
    if [[ "$VARIANT" == "sm64ex" && "$TARGET" == "steamrt3-aarch64" ]]; then
        SM64RA_MAKE_ARGS+=(
            TARGET_ARCH=armv8-a
            RENDER_API=GL
            WINDOW_API=SDL2
            AUDIO_API=SDL2
            CONTROLLER_API=SDL2
        )
    fi
    ( cd "$SM64_REPO_DPATH" && make clean && make -j"$NUM_CPUS" "${SM64RA_MAKE_ARGS[@]}" )
    #( cd "$SM64_REPO_DPATH" && NOEXTRACT=1 COMPARE=0 NON_MATCHING=0 VERSION=us make -j"$NUM_CPUS" )

    if ! test -e "$BINARY_FPATH" ; then
        echo "ERROR: build completed but expected output is missing: $BINARY_FPATH" >&2
        exit 2
    fi

    if sm64ra_is_container_target "$TARGET"; then
        BINARY_DESCRIPTION=$(file -b "$BINARY_FPATH")
        case "$TARGET" in
            steamrt3-aarch64)
                if [[ "$BINARY_DESCRIPTION" != *"ARM aarch64"* && "$BINARY_DESCRIPTION" != *"ARM64"* ]]; then
                    echo "ERROR: expected an ARM64 executable, got: $BINARY_DESCRIPTION" >&2
                    exit 2
                fi
                ;;
            steamrt3-x86_64)
                if [[ "$BINARY_DESCRIPTION" != *"x86-64"* && "$BINARY_DESCRIPTION" != *"x86_64"* ]]; then
                    echo "ERROR: expected an x86_64 executable, got: $BINARY_DESCRIPTION" >&2
                    exit 2
                fi
                ;;
        esac
        echo "Verified target executable: $BINARY_DESCRIPTION"
    fi
fi

# Remove only a temporary baserom symlink that this script staged. Existing
# baserom files in the variant checkout are left untouched.
sm64ra_unstage_baserom
trap - EXIT

# Run the asset generator
"$SM64RA_PYTHON" -c "if 1:
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

    if '$TARGET' == 'n64':
        print(ub.highlight_code(ub.codeblock('''

        EVERDRIVE_DPATH=$EVERDRIVE_DPATH
        EMULATOR=$EMULATOR

        '''), lexer_name='bash'))

"

if [[ "$TARGET" == "n64" ]]; then
    if test -d "$EVERDRIVE_DPATH" ; then
        echo "Copying ROM to EverDrive directory"
        cp "$BINARY_FPATH" "$EVERDRIVE_DPATH"/Custom/sm64.us.z64
        echo "EVERDRIVE_DPATH = $EVERDRIVE_DPATH"
        ls -al "$EVERDRIVE_DPATH"/Custom/
    else
        echo "No EverDrive detected."
    fi
fi

if [[ "$TARGET" == "host" || "$TARGET" == "n64" ]]; then
    echo "To execute locally use: "
    echo "$EXECUTE_INVOCATION"
else
    echo "Built for $TARGET; deploy this artifact to the target runtime:"
    echo "$BINARY_FPATH"
fi

if [[ "$TEST_LOCALLY" == "1" ]]; then
    if [[ "$TARGET" != "host" && "$TARGET" != "n64" ]]; then
        echo "ERROR: TEST_LOCALLY=1 is only valid for TARGET=host or TARGET=n64" >&2
        exit 2
    fi
    echo "Testing locally"
    $EXECUTE_INVOCATION
fi
