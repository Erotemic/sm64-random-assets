#!/usr/bin/env bash
set -euo pipefail

THIS_DPATH=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck source=dev/build_config.sh
source "$THIS_DPATH/dev/build_config.sh"
sm64ra_resolve_build_config
sm64ra_resolve_asset_config

# Resolve an explicit baserom on the host before doing any expensive Docker
# work. BASEROM_FPATH is user-facing and may be relative to the caller's cwd.
# Convert it to a concrete host file now, then map that file to a deterministic
# container path. The independent marker makes the inner build fail closed if
# the path or mount is ever lost instead of falling back to asset generation.
SM64RA_EXPECT_BASEROM=0
CONTAINER_BASEROM_FPATH=""
BASEROM_MOUNT_ARGS=()
if [[ -n ${BASEROM_FPATH:-} ]]; then
    if ! BASEROM_ABS=$(realpath -e -- "$BASEROM_FPATH" 2>/dev/null); then
        echo "ERROR: BASEROM_FPATH does not exist: $BASEROM_FPATH" >&2
        exit 2
    fi
    if [[ ! -f "$BASEROM_ABS" ]]; then
        echo "ERROR: BASEROM_FPATH is not a regular file: $BASEROM_ABS" >&2
        exit 2
    fi

    SM64RA_EXPECT_BASEROM=1
    ASSET_MODE=baserom

    # The whole repository is already mounted at /work. Keep the common
    # BASEROM_FPATH=baserom.us.z64 case inside that mount instead of creating a
    # second bind mount for the same file. Files outside the repo get a small
    # dedicated read-only mount under /inputs.
    case "$BASEROM_ABS" in
        "$THIS_DPATH"/*)
            BASEROM_REL=${BASEROM_ABS#"$THIS_DPATH"/}
            CONTAINER_BASEROM_FPATH="/work/$BASEROM_REL"
            ;;
        *)
            CONTAINER_BASEROM_FPATH=/inputs/baserom.us.z64
            BASEROM_MOUNT_ARGS=(
                --mount "type=bind,src=$BASEROM_ABS,dst=$CONTAINER_BASEROM_FPATH,readonly"
            )
            ;;
    esac
fi

if ! sm64ra_is_container_target "$TARGET"; then
    echo "ERROR: dev/build_steamrt_target.sh only handles Steam Runtime targets; got TARGET=$TARGET" >&2
    exit 2
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker is required to build $TARGET off-device." >&2
    exit 2
fi
if ! docker buildx version >/dev/null 2>&1; then
    echo "ERROR: Docker buildx is required for multi-architecture Steam Runtime builds." >&2
    exit 2
fi

case "$TARGET" in
    steamrt3-x86_64)
        DOCKER_PLATFORM=linux/amd64
        STEAMRT_SDK_IMAGE=registry.gitlab.steamos.cloud/steamrt/sniper/sdk:latest
        ;;
    steamrt3-aarch64)
        DOCKER_PLATFORM=linux/arm64
        STEAMRT_SDK_IMAGE=registry.gitlab.steamos.cloud/steamrt/sniper/sdk/arm64:latest
        ;;
esac

HOST_ARCH=$(sm64ra_host_arch)
TARGET_ARCH=$(sm64ra_target_arch "$TARGET")

if [[ $HOST_ARCH != "$TARGET_ARCH" ]]; then
    BUILDER_INFO=$(docker buildx inspect --bootstrap 2>&1) || {
        printf '%s\n' "$BUILDER_INFO" >&2
        echo "ERROR: docker buildx could not initialize the current builder." >&2
        exit 2
    }
    if ! grep -Fq "$DOCKER_PLATFORM" <<< "$BUILDER_INFO"; then
        cat >&2 <<EOF
ERROR: Docker cannot currently execute $DOCKER_PLATFORM containers on this $HOST_ARCH host.

The Steam Frame target uses an ARM64 Steam Runtime image. Docker needs a
binfmt/QEMU handler so its ARM64 /bin/sh and compiler can run on an x86_64 host.

Enable it once with:

    ./dev/setup_docker_binfmt.sh arm64

Equivalent Docker command:

    docker run --privileged --rm tonistiigi/binfmt --install arm64

Then rerun:

    PRESET=${PRESET:-steamframe} VARIANT=$VARIANT ./build.sh
EOF
        exit 2
    fi
fi

IMAGE_TAG="sm64ra-${TARGET}:local"
DEBIAN_SECURITY_SNAPSHOT=${STEAMRT_DEBIAN_SECURITY_SNAPSHOT:-20260903T220410Z}
STEAMRT_PYTHON_VERSION=${STEAMRT_PYTHON_VERSION:-3.12}

echo "Build target environment"
echo "========================"
echo "PRESET=${PRESET:-<none>}"
echo "VARIANT=$VARIANT"
echo "TARGET=$TARGET"
echo "ASSET_MODE=$ASSET_MODE"
echo "DOCKER_PLATFORM=$DOCKER_PLATFORM"
echo "STEAMRT_SDK_IMAGE=$STEAMRT_SDK_IMAGE"
echo "DEBIAN_SECURITY_SNAPSHOT=$DEBIAN_SECURITY_SNAPSHOT"
echo "STEAMRT_PYTHON_VERSION=$STEAMRT_PYTHON_VERSION"
if [[ "$SM64RA_EXPECT_BASEROM" == "1" ]]; then
    echo "BASEROM_HOST_FPATH=$BASEROM_ABS"
    echo "BASEROM_CONTAINER_FPATH=$CONTAINER_BASEROM_FPATH"
fi
echo

docker buildx build \
    --platform "$DOCKER_PLATFORM" \
    --load \
    --build-arg "STEAMRT_SDK_IMAGE=$STEAMRT_SDK_IMAGE" \
    --build-arg "DEBIAN_SECURITY_SNAPSHOT=$DEBIAN_SECURITY_SNAPSHOT" \
    --build-arg "PYTHON_VERSION=$STEAMRT_PYTHON_VERSION" \
    --tag "$IMAGE_TAG" \
    --file "$THIS_DPATH/dockerfiles/steamrt_sm64_random_assets.Dockerfile" \
    "$THIS_DPATH"

DOCKER_ARGS=(
    run --rm
    --platform "$DOCKER_PLATFORM"
    --user "$(id -u):$(id -g)"
    --mount "type=bind,src=$THIS_DPATH,dst=/work"
    --workdir /work
    --env HOME=/tmp/sm64ra-home
    --env XDG_CACHE_HOME=/tmp/sm64ra-cache
    --env MPLCONFIGDIR=/tmp/sm64ra-matplotlib
    --env SM64RA_TARGET_CONTAINER=1
    --env "VARIANT=$VARIANT"
    --env "TARGET=$TARGET"
    --env "PRESET=${PRESET:-}"
    --env "BUILD=${BUILD:-1}"
    --env "BUILD_REFERENCE=${BUILD_REFERENCE:-0}"
    --env "ASSET_MODE=$ASSET_MODE"
    --env "SM64RA_EXPECT_BASEROM=$SM64RA_EXPECT_BASEROM"
    --env "COMPARE=${COMPARE:-0}"
    --env "TARGET_QUALITY=${TARGET_QUALITY:-1}"
    --env "INCLUDE_AUTHORS=${INCLUDE_AUTHORS:-*}"
    --env "EXCLUDE_AUTHORS=${EXCLUDE_AUTHORS:-}"
    --env "NUM_CPUS=${NUM_CPUS:-all}"
    --env TEST_LOCALLY=0
)

if [[ -n ${ASSET_CONFIG+x} ]]; then
    export ASSET_CONFIG
    DOCKER_ARGS+=(--env ASSET_CONFIG)
fi

if [[ "$SM64RA_EXPECT_BASEROM" == "1" ]]; then
    DOCKER_ARGS+=("${BASEROM_MOUNT_ARGS[@]}")
    DOCKER_ARGS+=(--env "BASEROM_FPATH=$CONTAINER_BASEROM_FPATH")
fi

if [[ ${TEST_LOCALLY:-0} == 1 ]]; then
    echo "NOTE: TEST_LOCALLY=1 is ignored for an off-device target build. Deploy and run the result on the target device." >&2
fi

docker "${DOCKER_ARGS[@]}" "$IMAGE_TAG" \
    bash -c 'mkdir -p "$HOME" "$XDG_CACHE_HOME" "$MPLCONFIGDIR"; git config --global --add safe.directory /work; exec ./build.sh'
