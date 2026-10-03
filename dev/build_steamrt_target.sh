#!/usr/bin/env bash
set -euo pipefail

THIS_DPATH=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck source=dev/build_config.sh
source "$THIS_DPATH/dev/build_config.sh"
sm64ra_resolve_build_config

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

echo "Build target environment"
echo "========================"
echo "PRESET=${PRESET:-<none>}"
echo "VARIANT=$VARIANT"
echo "TARGET=$TARGET"
echo "DOCKER_PLATFORM=$DOCKER_PLATFORM"
echo "STEAMRT_SDK_IMAGE=$STEAMRT_SDK_IMAGE"
echo

docker buildx build \
    --platform "$DOCKER_PLATFORM" \
    --load \
    --build-arg "STEAMRT_SDK_IMAGE=$STEAMRT_SDK_IMAGE" \
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

if [[ -n ${EXTERNAL_ROM_FPATH:-} ]]; then
    EXTERNAL_ROM_ABS=$(readlink -f "$EXTERNAL_ROM_FPATH")
    if [[ ! -f $EXTERNAL_ROM_ABS ]]; then
        echo "ERROR: EXTERNAL_ROM_FPATH does not exist: $EXTERNAL_ROM_ABS" >&2
        exit 2
    fi
    DOCKER_ARGS+=(
        --mount "type=bind,src=$EXTERNAL_ROM_ABS,dst=/inputs/baserom.us.z64,readonly"
        --env EXTERNAL_ROM_FPATH=/inputs/baserom.us.z64
    )
fi

if [[ ${TEST_LOCALLY:-0} == 1 ]]; then
    echo "NOTE: TEST_LOCALLY=1 is ignored for an off-device target build. Deploy and run the result on the target device." >&2
fi

docker "${DOCKER_ARGS[@]}" "$IMAGE_TAG" \
    bash -lc 'mkdir -p "$HOME" "$XDG_CACHE_HOME" "$MPLCONFIGDIR"; git config --global --add safe.directory /work; exec ./build.sh'
