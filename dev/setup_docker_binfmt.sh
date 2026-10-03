#!/usr/bin/env bash
set -euo pipefail

ARCH=${1:-arm64}

case "$ARCH" in
    arm64|amd64|arm|riscv64|ppc64le|s390x|386) ;;
    *)
        echo "ERROR: unsupported binfmt architecture: $ARCH" >&2
        exit 2
        ;;
esac

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker is required." >&2
    exit 2
fi
if ! docker buildx version >/dev/null 2>&1; then
    echo "ERROR: Docker buildx is required." >&2
    exit 2
fi

echo "Registering Docker/QEMU binfmt support for $ARCH..."
docker run --privileged --rm tonistiigi/binfmt --install "$ARCH"

echo "Refreshing buildx platform detection..."
BUILDER_INFO=$(docker buildx inspect --bootstrap 2>&1) || {
    printf '%s\n' "$BUILDER_INFO" >&2
    echo "ERROR: docker buildx inspect --bootstrap failed." >&2
    exit 2
}
printf '%s\n' "$BUILDER_INFO"

if ! grep -Fq "linux/$ARCH" <<< "$BUILDER_INFO"; then
    echo "ERROR: buildx still does not report linux/$ARCH support." >&2
    echo "       Check your Docker daemon, binfmt_misc support, and builder configuration." >&2
    exit 2
fi

echo
echo "Docker can now build/run linux/$ARCH containers through binfmt/QEMU."
