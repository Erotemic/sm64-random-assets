# syntax=docker/dockerfile:1.5.0
FROM linuxserver/steamos:latest


ENV HOME=/root
ENV CODE_DPATH=/root/code

# ----------------------------
# Install System Prerequisites
# ----------------------------
RUN <<EOF
#!/bin/bash
pacman -Syu --noconfirm
pacman -S --noconfirm git base-devel python libusb sdl2 glew
EOF


# -------------------------
# Setup a Python virtualenv
# -------------------------
RUN <<EOF
#!/bin/bash
python -m venv $HOME/.venv/py311
source $HOME/.venv/py311/bin/activate
python -m pip install kwimage opencv-python-headless ubelt numpy ruamel.yaml PyYAML scriptconfig rich parse matplotlib
EOF


# -----------
# Clone Repos
# -----------
#RUN <<EOF
##!/bin/bash
#mkdir -p "$CODE_DPATH"
#git clone https://github.com/Erotemic/sm64-random-assets.git $CODE_DPATH/sm64-random-assets
#cd "$CODE_DPATH"/sm64-random-assets
#git submodule update --init tpl/sm64-port
#EOF

# --------------------------------
# Copy local git repo to the image
# --------------------------------
RUN mkdir -p /root/code/sm64-random-assets
COPY .git /root/code/sm64-random-assets/.git


# -----------
# Setup Repos
# -----------
RUN <<EOF
#!/bin/bash
cd "$CODE_DPATH"/sm64-random-assets
git checkout *
#git clone https://github.com/Erotemic/sm64-random-assets.git $CODE_DPATH/sm64-random-assets
git submodule update --init tpl/sm64-port
EOF

# Copy over reference

WORKDIR /root/code/sm64-random-assets
COPY ./sm64.us.z64 /root/code/sm64-random-assets/baserom.us.z64


# --------------------------
# Generate Assets and Build 
# --------------------------
RUN <<EOF
#!/bin/bash

cd "$CODE_DPATH"/sm64-random-assets

source $HOME/.venv/py311/bin/activate
echo "Activated VENV"
pwd
ls -al

export BUILD_REFERENCE=1
export EXTERNAL_ROM_FPATH=baserom.us.z64
export ASSET_CONFIG='
    png: reference
    aiff: reference
    m64: reference
    bin: reference
'
echo "Call Build"
./build.sh

EOF

RUN <<EOF
__doc__='
This docker file builds an sm64 executable suitable for a steam deck using the
random asset generator.
'
echo "

    cd ~/code/sm64-random-assets

    ./dev/grab_reference_baserom.sh sm64.us.z64

    # Build the sm64-random-assets image
    DOCKER_BUILDKIT=1 docker build --progress=plain \
        -t "steamdeck_sm64_refassets" \
        -f ./dockerfiles/steamdeck_sm64_referenced_assets.Dockerfile .

    # Start the image as a container
    docker run --rm -td --name steamdeck_sm64_refassets_container steamdeck_sm64_refassets 

    # Copy the build out of the container
    docker cp steamdeck_sm64_refassets_container:/root/code/sm64-random-assets/tpl/sm64-port/build/us_pc ./sm64refassets_us_pc_steamdeck

    # Copy the build to the steamdeck (if built on a different PC)
    # Note: dont copy directly into the home folder, otherwise
    # rsync might mess up home directory permissions and lock you out of ssh
    rsync -avrPR ./sm64refassets_us_pc_steamdeck steamdeck:data/games

    # Stop and remove container
    docker stop steamdeck_sm64_refassets_container
"
EOF
