# syntax=docker/dockerfile:1.5.0
FROM linuxserver/steamos:latest


ARG BUILD_REFERENCE=0


RUN <<EOF
#!/bin/bash
pacman -Syu --noconfirm
pacman -S --noconfirm git base-devel python libusb sdl2 glew

if [[ "$HOME" == "" ]]; then
    HOME=/root
fi

python -m venv $HOME/.venv/py311
source $HOME/.venv/py311/bin/activate
python -m pip install kwimage opencv-python-headless ubelt numpy ruamel.yaml PyYAML scriptconfig rich parse matplotlib


EOF

RUN <<EOF
#!/bin/bash

CODE_DPATH=$HOME/code
mkdir -p "$CODE_DPATH"
git clone https://github.com/Erotemic/sm64-random-assets.git $CODE_DPATH/sm64-random-assets
cd "$CODE_DPATH"/sm64-random-assets
git submodule update --init tpl/sm64-port

./build.sh

EOF



RUN <<EOF
__doc__='
This docker file builds an sm64 executable suitable for a steam deck using the
random asset generator.
'
echo "

    cd ~/code/sm64-random-assets

    if type -P secret_loader.sh; then
        # shellcheck disable=SC1090
        source "$(secret_loader.sh)"
        SM64_CID=$(load_secret_var sm64_us_cid)
        echo "SM64_CID = $SM64_CID"
        ipfs get "$SM64_CID" -o sm64.us.z64
    else
        echo "Need to manually get the baserom"
    fi

    # Build the sm64-random-assets image
    DOCKER_BUILDKIT=1 docker build --progress=plain \
        -t "steamdeck_sm64ra" \
        -f ./dockerfiles/steamdeck_sm64_random_assets.Dockerfile .

    # Start the image as a container
    docker run --rm -td --name steamdeck_sm64_ra_container steamdeck_sm64ra 

    # Copy the build out of the container
    docker cp steamdeck_sm64ra:/root/code/sm64-random-assets/tpl/sm64-port/build/us_pc ./sm64ra_us_pc_steamdeck

    # Stop and remove container
    docker stop steamdeck_sm64ra

    # Copy the build to the steamdeck (if built on a different PC)
    # Note: dont copy directly into the home folder, otherwise
    # rsync might mess up home directory permissions and lock you out of ssh
    rsync -avrPR ./sm64ra_us_pc_steamdeck steamdeck:data/games
"
EOF
