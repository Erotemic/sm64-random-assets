SteamDeck Instructions
----------------------

These instructions outlines the steps to compile a SM64 PCPort on a steam deck
(or more generally arch linux).

Install Prereq
==============

These instructions are written to use system packages, which may not be the
best idea.  It requires us to disable readonly mode, which may not be safe,
then we can install system packages.

.. code:: bash

    sudo steamos-readonly disable

    sudo pacman-key --init
    sudo pacman-key --populate archlinux
    sudo pacman-key --populate holo

    sudo pacman -Sy base-devel
    sudo pacman -Sy gcc
    sudo pacman -Sy python
    sudo pacman -Sy python-pip
    sudo pacman -Sy sdl2 sdl2_gfx sdl2_image sdl2_mixer sdl2_ttf
    sudo pacman -Sy glibc linux-api-headers

    # Ref: https://gist.github.com/tomshen/c7ae6f99429316eab4097f657cfb2185
    sudo pacman -S sdl2 glew glibc linux-api-headers libusb libglvnd
    sudo pacman -Rs sdl2_gfx sdl2_image sdl2_mixer sdl2_ttf

    # https://github.com/MorsGames/sm64plus/wiki/Manual-Building-Guide
    #sudo pacman -S git make python3 #mingw-w64-x86_64-gcc mingw-w64-x86_64-SDL2 mingw-w64-x86_64-glew
    sudo pacman -S base-devel python sdl2 glew

    # Setup a venv
    python -m venv $HOME/.venv/py311

    source $HOME/.venv/py311/bin/activate

    python -m pip install kwimage opencv-python-headless ubelt numpy ruamel.yaml PyYAML scriptconfig rich parse matplotlib


Setup the Repo
==============

.. code:: bash

    CODE_DPATH=$HOME/code
    mkdir -p "$CODE_DPATH"
    git clone https://github.com/Erotemic/sm64-random-assets.git $CODE_DPATH/sm64-random-assets
    cd "$CODE_DPATH"/sm64-random-assets

    cd "$CODE_DPATH"/sm64-random-assets
    git submodule update --init tpl/sm64-port

    # Move into the PC port directory and build
    cd $CODE_DPATH/sm64-random-assets
    ./build.sh
