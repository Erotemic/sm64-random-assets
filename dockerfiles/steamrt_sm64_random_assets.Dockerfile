# syntax=docker/dockerfile:1.5
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.12.22
ARG STEAMRT_SDK_IMAGE
FROM ${UV_IMAGE} AS uv
FROM ${STEAMRT_SDK_IMAGE}

ARG DEBIAN_SECURITY_SNAPSHOT=20260903T220410Z
ARG PYTHON_VERSION=3.12
ENV DEBIAN_FRONTEND=noninteractive

# Keep the Python toolchain independent of Sniper's system Python.  The Steam
# Runtime 3 SDK is based on Bullseye and currently carries Python 3.9, while
# sm64-random-assets dependencies such as kwconf require Python >= 3.10.
# uv is a standalone multi-architecture binary and provisions a managed
# CPython for the target architecture, so the entire build remains hermetic
# inside the target SDK container.
COPY --from=uv /uv /uvx /bin/
ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python
ENV UV_PYTHON_BIN_DIR=/opt/uv-python-bin
ENV UV_LINK_MODE=copy

# Sniper is based on Debian 11 (Bullseye). Bullseye LTS ended on 2026-08-31,
# and during Debian's security-archive transition the live bullseye-security
# indexes have referenced package files that have already disappeared. Pin the
# security repositories to the final snapshot instead of depending on that
# moving EOL mirror. Keep signature verification enabled; only expiry checking
# is disabled because a snapshot is intentionally immutable and historical.
RUN set -eux; \
    snapshot_base="https://snapshot.debian.org/archive"; \
    security_url="$snapshot_base/debian-security/$DEBIAN_SECURITY_SNAPSHOT"; \
    security_debug_url="$snapshot_base/debian-security-debug/$DEBIAN_SECURITY_SNAPSHOT"; \
    find /etc/apt -type f \( -name '*.list' -o -name '*.sources' \) -print0 \
        | xargs -0 -r sed -i \
            -e "s#https\?://deb\.debian\.org/debian-security-debug#$security_debug_url#g" \
            -e "s#https\?://security\.debian\.org/debian-security-debug#$security_debug_url#g" \
            -e "s#https\?://deb\.debian\.org/debian-security#$security_url#g" \
            -e "s#https\?://security\.debian\.org/debian-security#$security_url#g"; \
    printf '%s\n' 'Acquire::Check-Valid-Until "false";' \
        > /etc/apt/apt.conf.d/99-sm64ra-debian-snapshot; \
    grep -R -n -E 'snapshot\.debian\.org|debian-security' \
        /etc/apt/sources.list /etc/apt/sources.list.d 2>/dev/null || true

# The Steam Runtime SDK already carries its own SDL stack. In current Sniper
# ARM64 images that stack can be sdl2-compat, whose shim intentionally
# conflicts with Debian Bullseye's classic libsdl2-2.0-0. Do not explicitly
# install libsdl2-dev here: doing so asks apt to replace the SDK's SDL ABI and
# fails with libsdl2-compat-shim vs libsdl2-2.0-0 conflicts.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        file \
        git \
        libasound2-dev \
        libglew-dev \
        libpulse-dev \
        libusb-1.0-0-dev \
        libx11-dev \
        libxrandr-dev \
        pkg-config; \
    if ! command -v sdl2-config >/dev/null 2>&1; then \
        if apt-cache show libsdl2-compat-dev >/dev/null 2>&1; then \
            apt-get install -y --no-install-recommends libsdl2-compat-dev; \
        else \
            echo 'ERROR: Steam Runtime SDK has no sdl2-config and no libsdl2-compat-dev package.' >&2; \
            echo 'Installed SDL packages:' >&2; \
            dpkg-query -W 'libsdl*' 2>/dev/null >&2 || true; \
            exit 1; \
        fi; \
    fi; \
    sdl2-config --version; \
    sdl2-config --cflags; \
    sdl2-config --libs; \
    rm -rf /var/lib/apt/lists/*

COPY requirements/runtime.txt /tmp/sm64ra-requirements/runtime.txt
COPY requirements/headless.txt /tmp/sm64ra-requirements/headless.txt

RUN --mount=type=cache,target=/root/.cache/uv \
    set -eux; \
    uv python install "$PYTHON_VERSION"; \
    uv venv --python "$PYTHON_VERSION" /opt/sm64ra-venv; \
    uv pip install \
        --python /opt/sm64ra-venv/bin/python \
        -r /tmp/sm64ra-requirements/runtime.txt \
        -r /tmp/sm64ra-requirements/headless.txt; \
    /opt/sm64ra-venv/bin/python --version; \
    uv --version

ENV SM64RA_PYTHON=/opt/sm64ra-venv/bin/python
ENV PATH=/opt/sm64ra-venv/bin:${PATH}
