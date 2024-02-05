# syntax=docker/dockerfile:1.5.0
FROM linuxserver/steamos:latest

RUN <<EOF
#!/bin/bash
pacman -Syu --noconfirm
pacman -S --noconfirm git base-devel python libusb sdl2 glew
EOF

RUN <<EOF
#!/bin/bash
git clone https://github.com/TechieAndroid/sm64redrawn.git
git clone https://github.com/sm64pc/sm64ex.git
EOF

WORKDIR /sm64ex

COPY ./"sm64.us.z64" ./baserom.us.z64

RUN <<EOF

#patch -p1 < "enhancements/60fps_ex.patch"
make VERSION=us BETTERCAMERA=0 TEXTURE_FIX=0 EXTERNAL_DATA=0 NODRAWINGDISTANCE=1 -j4
#cp /sm64redrawn/gfx /sm64ex/build/us_pc/res -r

EOF


RUN <<EOF
__doc__='

This file encapsulates and updates instructions from [Sm64ExBuild]_.
It is NOT the sm64-random-asset docker image. It requires that the ROM
exists, and is in the cwd with the name "sm64.us.z64"

 References:
 .. [Sm64ExBuild] https://www.reddit.com/r/SteamDeck/comments/xs30xa/building_super_mario_64_ex_for_steamdeck/
'

echo "

    # On podman: podman run -it docker.io/linuxserver/steamos:latest bash

    cd ~/code/sm64-random-assets

    # This docker images requires an existing copy of the ROM
    # in the cwd with the name "sm64.us.z64"
    EXTERNAL_ROM_FPATH=sm64.us.z64
    echo "17ce077343c6133f8c9f2d6d6d9a4ab62c8cd2aa57c40aea1f490b4c8bb21d91 $EXTERNAL_ROM_FPATH" | sha256sum --check --status
    _RESULT=$?
    if [[ "$_RESULT" == "0" ]]; then
        echo "Externally specified ROM has the expected hash"
    else
        echo "WARNING: Externally specified ROM has an UNEXPECTED hash!"
        sha256sum "$EXTERNAL_ROM_FPATH"
    fi

    # Build the sm64ex image
    DOCKER_BUILDKIT=1 docker build --progress=plain \
        -t "steamdeck_sm64ex" \
        -f ./dockerfiles/steamdeck_sm64ex.Dockerfile .

    # Start the image as a container
    docker run --rm -td --name sm64ex_container steamdeck_sm64ex 

    # Copy the build out of the container
    docker cp sm64ex_container:/sm64ex/build/us_pc ./sm64ex_us_pc_steamdeck

    # Copy the build to the steamdeck (if built on a different PC)
    # Note: dont copy directly into the home folder, otherwise
    # rsync might mess up home directory permissions and lock you out of ssh
    rsync -avprPR ./sm64ex_us_pc_steamdeck steamdeck:data/games

    # Stop and remove container
    docker stop sm64ex_container
"
EOF
