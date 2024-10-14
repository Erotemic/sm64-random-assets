"""

https://github.com/mkst/sm64-port/issues/63

"""
import ubelt as ub
from sm64_random_assets.vendor import aifc
import io
path = ub.Path('~/code/sm64-random-assets/tpl/sm64-port-ref/build/us_pc/sound/samples/bowser_organ/00_organ_1.aifc').expand()
data = path.read_bytes()
new_file = aifc.open(io.BytesIO(data), 'rb')
file = open(path, 'rb')
new_file = aifc.open(file, 'wb')
# new_file.setparams(params)
# new_file.writeframes(new_data)


"""

On Windows Machine:

    cd ~/code/sm64-random-assets/tpl/sm64-port
    # git remote add Erotemic https://github.com/Erotemic/sm64-port

    cd ~/code/sm64-random-assets
    export TARGET=pc
    export BUILD_REFERENCE=0
    export COMPARE=0
    export NUM_CPUS=1
    export ASSET_CONFIG='
        png: skip
        aiff: generate
        m64: skip
        bin: skip
    '
    export BUILD=0
    ./build.sh

"""


"""

BUILD COMMANDS:

    export EXTERNAL_ROM_FPATH=baserom.us.z64
    export TARGET=pc
    export BUILD_REFERENCE=0
    export COMPARE=0
    export NUM_CPUS=all
    export ASSET_CONFIG='
        png: generate
        aiff: zero
        m64: generate
        bin: generate
    '
    ./build.sh

"""

r"""

git fetch Erotemic
git checkout explore-win32-audio-issues


sha1sum sound/samples/instruments/14_strings_5.aiff
xxd sound/samples/instruments/14_strings_5.aiff
tools/aiff_extract_codebook sound/samples/instruments/14_strings_5.aiff



cd ~/code/sm64-random-assets/tpl/sm64-port
sha1sum sound/samples/bowser_organ/00_organ_1.aiff

sed -i -e 's/\r//g' build/us_pc/sound/samples/bowser_organ/00_organ_1.table
sha1sum build/us_pc/sound/samples/bowser_organ/00_organ_1.table

cat build/us_pc/sound/samples/bowser_organ/00_organ_1.table

python3 -c "if 1:
    import pathlib
    text = pathlib.Path('build/us_pc/sound/samples/bowser_organ/00_organ_1.table').read_bytes()
    print(repr(text))
"


tools/aiff_extract_codebook sound/samples/bowser_organ/00_organ_1.aiff >build/us_pc/sound/samples/bowser_organ/00_organ_1.table
# sed -i -e 's/\r//g' build/us_pc/sound/samples/bowser_organ/00_organ_1.table
sha1sum build/us_pc/sound/samples/bowser_organ/00_organ_1.table
tools/vadpcm_enc -c build/us_pc/sound/samples/bowser_organ/00_organ_1.table sound/samples/bowser_organ/00_organ_1.aiff build/us_pc/sound/samples/bowser_organ/00_organ_1.aifc

cat build/us_pc/sound/samples/bowser_organ/00_organ_1.aifc | sha1sum


Extracting codebook: sound/samples/bowser_organ/00_organ_1.aiff -> build/us_pc/sound/samples/bowser_organ/00_organ_1.table
tools/aiff_extract_codebook sound/samples/bowser_organ/00_organ_1.aiff >build/us_pc/sound/samples/bowser_organ/00_organ_1.table
Encoding ADPCM: sound/samples/bowser_organ/00_organ_1.aiff -> build/us_pc/sound/samples/bowser_organ/00_organ_1.aifc
tools/vadpcm_enc -c build/us_pc/sound/samples/bowser_organ/00_organ_1.table sound/samples/bowser_organ/00_organ_1.aiff build/us_pc/sound/samples/bowser_organ/00_organ_1.aifc
Extracting codebook: sound/samples/bowser_organ/01_organ_1_lq.aiff -> build/us_pc/sound/samples/bowser_organ/01_organ_1_lq.table
tools/aiff_extract_codebook sound/samples/bowser_organ/01_organ_1_lq.aiff >build/us_pc/sound/samples/bowser_organ/01_organ_1_lq.table
Encoding ADPCM: sound/samples/bowser_organ/01_organ_1_lq.aiff -> build/us_pc/sound/samples/bowser_organ/01_organ_1_lq.aifc
tools/vadpcm_enc -c build/us_pc/sound/samples/bowser_organ/01_organ_1_lq.table sound/samples/bowser_organ/01_organ_1_lq.aiff build/us_pc/sound/samples/bowser_organ/01_organ_1_lq.aifc
Extracting codebook: sound/samples/bowser_organ/02_boys_choir.aiff -> build/us_pc/sound/samples/bowser_organ/02_boys_choir.table
tools/aiff_extract_codebook sound/samples/bowser_organ/02_boys_choir.aiff >build/us_pc/sound/samples/bowser_organ/02_boys_choir.table
Encoding ADPCM: sound/samples/bowser_organ/02_boys_choir.aiff -> build/us_pc/sound/samples/bowser_organ/02_boys_choir.aifc
tools/vadpcm_enc -c build/us_pc/sound/samples/bowser_organ/02_boys_choir.table sound/samples/bowser_organ/02_boys_choir.aiff build/us_pc/sound/samples/bowser_organ/02_boys_choir.aifc

"""




