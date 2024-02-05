#!/bin/bash
ROM_FPATH=${ROM_FPATH:=${1:="baserom.us.z64"}}
if type -P secret_loader.sh; then
    # Developer testing with known secret path to a personal copy of the ROM
    # shellcheck disable=SC1090
    source "$(secret_loader.sh)"
    SM64_CID=$(load_secret_var sm64_us_cid)
    echo "SM64_CID = $SM64_CID"
    ipfs get "$SM64_CID" -o "$ROM_FPATH"
    echo "Grabbed $ROM_FPATH"
else
    echo "
    !!!!!!!
    ERROR: This script is intended for internal development!
    It is a placeholder for some method to obtain a copy of a ROM.
    "
fi
