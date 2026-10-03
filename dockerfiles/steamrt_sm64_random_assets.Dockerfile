# syntax=docker/dockerfile:1.5
ARG STEAMRT_SDK_IMAGE
FROM ${STEAMRT_SDK_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        file \
        git \
        libasound2-dev \
        libglew-dev \
        libpulse-dev \
        libsdl2-dev \
        libusb-1.0-0-dev \
        libx11-dev \
        libxrandr-dev \
        pkg-config \
        python3 \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/runtime.txt /tmp/sm64ra-requirements/runtime.txt
COPY requirements/headless.txt /tmp/sm64ra-requirements/headless.txt

RUN python3 -m venv /opt/sm64ra-venv \
    && /opt/sm64ra-venv/bin/python -m pip install --upgrade pip setuptools wheel \
    && /opt/sm64ra-venv/bin/python -m pip install \
        -r /tmp/sm64ra-requirements/runtime.txt \
        -r /tmp/sm64ra-requirements/headless.txt

ENV PATH=/opt/sm64ra-venv/bin:${PATH}
