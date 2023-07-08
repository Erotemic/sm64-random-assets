__doc__="
Notes as I hack on the assets to make sure they don't crash things.
"

# Make a temporary directory
ROOT_DPATH=$HOME/tmp/tmp-code2
mkdir -p "$ROOT_DPATH"

# Clone this repo
git clone https://github.com/Erotemic/sm64-random-assets.git "$HOME"/code/sm64-random-assets

# Clone the ROM-only sm64 repo
git clone https://github.com/n64decomp/sm64.git "$ROOT_DPATH"/code/sm64

# Run the asset generator
python "$HOME/code/sm64-random-assets/generate_assets.py" --dst "$ROOT_DPATH"/code/sm64

# Move into the sm64 directory
cd "$ROOT_DPATH"/code/sm64

# Compile
NUM_CPUS=$(nproc --all)
COMPARE=0 NON_MATCHING=1 make VERSION=us -j"$NUM_CPUS"

# The compiled ROM is:
build/us/sm64.us.z64
