#!/usr/bin/env bash
set -eo pipefail

__doc__='Generate randomized assets and build an SM64 variant.

The build model has three independent concepts:

    VARIANT  Which SM64 codebase to build.
    TARGET   Which execution/runtime target to build for.
    PRESET   A human-friendly configuration shortcut.

Examples:

    # Default: sm64-port for the current host
    ./build.sh

    # Native ARM64 Steam Runtime build for Steam Frame, built off-device
    PRESET=steamframe ./build.sh

    # Same target, different codebase
    PRESET=steamframe VARIANT=sm64ex ./build.sh

    # Native x86_64 Steam Runtime build for Steam Deck
    PRESET=steamdeck ./build.sh

    # N64 ROM
    PRESET=n64 ./build.sh

Legacy TARGET=pc / TARGET=rom / TARGET=<variant> spellings remain accepted.
'

THIS_DPATH=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=dev/build_config.sh
source "$THIS_DPATH/dev/build_config.sh"
sm64ra_resolve_build_config

NUM_CPUS=${NUM_CPUS:-all}
BUILD=${BUILD:-1}
BUILD_REFERENCE=${BUILD_REFERENCE:-0}
EXTERNAL_ROM_FPATH=${EXTERNAL_ROM_FPATH:-}
TEST_LOCALLY=${TEST_LOCALLY:-0}
COMPARE=${COMPARE:-0}
TARGET_QUALITY=${TARGET_QUALITY:-1}
INCLUDE_AUTHORS=${INCLUDE_AUTHORS:-*}
EXCLUDE_AUTHORS=${EXCLUDE_AUTHORS:-}
SM64RA_TARGET_CONTAINER=${SM64RA_TARGET_CONTAINER:-0}
SM64RA_PYTHON=${SM64RA_PYTHON:-python3}

if [[ $NUM_CPUS == all ]]; then
    NUM_CPUS=$(nproc --all)
fi

if sm64ra_is_container_target "$TARGET" && [[ $BUILD == 1 && $SM64RA_TARGET_CONTAINER != 1 ]]; then
    exec "$THIS_DPATH/dev/build_steamrt_target.sh"
fi

if sm64ra_is_container_target "$TARGET" && [[ $SM64RA_TARGET_CONTAINER == 1 ]]; then
    EXPECTED_ARCH=$(sm64ra_target_arch "$TARGET")
    HOST_ARCH=$(sm64ra_host_arch)
    if [[ $EXPECTED_ARCH != "$HOST_ARCH" ]]; then
        echo "ERROR: $TARGET requires $EXPECTED_ARCH, but the build container reports $HOST_ARCH" >&2
        exit 2
    fi
fi

if command -v mupen64plus >/dev/null 2>&1; then
    EMULATOR=${EMULATOR:-mupen64plus}
else
    EMULATOR=${EMULATOR:-m64py}
fi
EVERDRIVE_DPATH=${EVERDRIVE_DPATH:-/media/$USER/9DC3-BFF3}

DEFAULT_ASSET_CONFIG='
    png: generate
    aiff: generate
    m64: generate
    bin: generate
'
ASSET_CONFIG=${ASSET_CONFIG:-$DEFAULT_ASSET_CONFIG}

SM64_REPO_REL_DPATH=$(sm64ra_variant_repo_relpath "$VARIANT")
SM64_REPO_DPATH="$THIS_DPATH/$SM64_REPO_REL_DPATH"
BINARY_REL_FPATH=$(sm64ra_variant_binary_relpath "$VARIANT")
BINARY_TYPE=$(sm64ra_variant_binary_type "$VARIANT")
BINARY_FPATH="$SM64_REPO_DPATH/$BINARY_REL_FPATH"
REFERENCE_DPATH="${SM64_REPO_DPATH}-ref"
REFERENCE_BASEROM_FPATH="$REFERENCE_DPATH/baserom.us.z64"
REFERENCE_BINARY_FPATH="$REFERENCE_DPATH/$BINARY_REL_FPATH"

if [[ $TARGET == n64 ]]; then
    EXECUTE_INVOCATION="$EMULATOR $BINARY_FPATH"
else
    EXECUTE_INVOCATION="$BINARY_FPATH"
fi

cat <<EOF_CONFIG

CONFIGURATION
=============
THIS_DPATH=$THIS_DPATH
PRESET=${PRESET:-<none>}
VARIANT=$VARIANT
TARGET=$TARGET
NUM_CPUS=${NUM_CPUS:-<make default>}
BUILD=$BUILD
BUILD_REFERENCE=$BUILD_REFERENCE
EXTERNAL_ROM_FPATH=$EXTERNAL_ROM_FPATH
COMPARE=$COMPARE
TARGET_QUALITY=$TARGET_QUALITY
TEST_LOCALLY=$TEST_LOCALLY
SM64_REPO_DPATH=$SM64_REPO_DPATH
BINARY_FPATH=$BINARY_FPATH
SM64RA_PYTHON=$SM64RA_PYTHON
EOF_CONFIG

if [[ ! -d $SM64_REPO_DPATH ]] || [[ -z $(find "$SM64_REPO_DPATH" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null) ]]; then
    echo "Initialize SM64 variant submodule: $SM64_REPO_REL_DPATH"
    git -C "$THIS_DPATH" submodule update --init "$SM64_REPO_REL_DPATH"
else
    echo "SM64 variant already present: $SM64_REPO_REL_DPATH"
fi

if [[ -n $EXTERNAL_ROM_FPATH ]]; then
    echo "Checking external ROM hash: $EXTERNAL_ROM_FPATH"
    EXPECTED_ROM_SHA256=17ce077343c6133f8c9f2d6d6d9a4ab62c8cd2aa57c40aea1f490b4c8bb21d91
    if echo "$EXPECTED_ROM_SHA256 $EXTERNAL_ROM_FPATH" | sha256sum --check --status; then
        echo "External ROM has the expected hash"
    else
        echo "WARNING: external ROM has an unexpected hash" >&2
        sha256sum "$EXTERNAL_ROM_FPATH"
    fi
fi

make_parallel_args=()
if [[ -n $NUM_CPUS ]]; then
    make_parallel_args+=("-j$NUM_CPUS")
fi

if [[ $BUILD_REFERENCE == 1 ]]; then
    echo
    echo "Build reference"
    echo "==============="

    if [[ ! -d $REFERENCE_DPATH ]]; then
        git clone "$SM64_REPO_DPATH" "$REFERENCE_DPATH"
    fi

    if [[ ! -f $REFERENCE_BASEROM_FPATH ]]; then
        if [[ -n $EXTERNAL_ROM_FPATH ]]; then
            cp "$EXTERNAL_ROM_FPATH" "$REFERENCE_BASEROM_FPATH"
        else
            echo "ERROR: BUILD_REFERENCE=1 requires EXTERNAL_ROM_FPATH" >&2
            exit 2
        fi
    fi

    if [[ ! -f $REFERENCE_BINARY_FPATH ]]; then
        (
            cd "$REFERENCE_DPATH"
            make "${make_parallel_args[@]}" PYTHON="$SM64RA_PYTHON"
        )
    fi
fi

REFERENCE_ARG=$REFERENCE_DPATH
if [[ ! -d $REFERENCE_DPATH ]]; then
    REFERENCE_ARG=None
fi

echo
echo "Run asset generator"
echo "==================="
"$SM64RA_PYTHON" -m sm64_random_assets generate \
    --dst "$SM64_REPO_DPATH" \
    --reference "$REFERENCE_ARG" \
    --hybrid_mode=0 \
    --compare="$COMPARE" \
    --target_quality="$TARGET_QUALITY" \
    --include_authors "$INCLUDE_AUTHORS" \
    --exclude_authors "$EXCLUDE_AUTHORS" \
    --asset_config "$ASSET_CONFIG"

if [[ $BUILD == 1 ]]; then
    echo
    echo "Compile"
    echo "======="
    (
        cd "$SM64_REPO_DPATH"
        make clean
        NOEXTRACT=1 COMPARE=0 NON_MATCHING=0 VERSION=us make "${make_parallel_args[@]}" PYTHON="$SM64RA_PYTHON"
    )

    if [[ ! -e $BINARY_FPATH ]]; then
        echo "ERROR: build completed but expected output is missing: $BINARY_FPATH" >&2
        exit 2
    fi

    if sm64ra_is_container_target "$TARGET"; then
        BINARY_DESCRIPTION=$(file -b "$BINARY_FPATH")
        case "$TARGET" in
            steamrt3-aarch64)
                if [[ $BINARY_DESCRIPTION != *"ARM aarch64"* && $BINARY_DESCRIPTION != *"ARM64"* ]]; then
                    echo "ERROR: expected an ARM64 executable, got: $BINARY_DESCRIPTION" >&2
                    exit 2
                fi
                ;;
            steamrt3-x86_64)
                if [[ $BINARY_DESCRIPTION != *"x86-64"* && $BINARY_DESCRIPTION != *"x86_64"* ]]; then
                    echo "ERROR: expected an x86_64 executable, got: $BINARY_DESCRIPTION" >&2
                    exit 2
                fi
                ;;
        esac
        echo "Verified target executable: $BINARY_DESCRIPTION"
    fi
fi

echo
echo "Finalize"
echo "========"
echo "BINARY_TYPE=$BINARY_TYPE"
echo "BINARY_FPATH=$BINARY_FPATH"

if [[ $TARGET == n64 && $BUILD == 1 ]]; then
    if [[ -d $EVERDRIVE_DPATH ]]; then
        echo "Copying ROM to EverDrive directory"
        cp "$BINARY_FPATH" "$EVERDRIVE_DPATH/Custom/sm64.us.z64"
    else
        echo "No EverDrive detected."
    fi
fi

if [[ $TARGET == host || $TARGET == n64 ]]; then
    echo "To execute locally: $EXECUTE_INVOCATION"
else
    echo "Built for $TARGET; deploy the artifact to the target runtime before executing it."
fi

if [[ $TEST_LOCALLY == 1 ]]; then
    if [[ $TARGET != host && $TARGET != n64 ]]; then
        echo "ERROR: TEST_LOCALLY=1 is only valid for TARGET=host or TARGET=n64" >&2
        exit 2
    fi
    echo "Testing locally"
    if [[ $TARGET == n64 ]]; then
        "$EMULATOR" "$BINARY_FPATH"
    else
        "$BINARY_FPATH"
    fi
fi
