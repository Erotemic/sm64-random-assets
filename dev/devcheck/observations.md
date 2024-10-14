See `https://github.com/mkst/sm64-port/issues/63`

# Observations:

I'm looking for any difference in the systems.


### NewLines

When running: 

```
tools/aiff_extract_codebook sound/samples/bowser_organ/00_organ_1.aiff >build/us_pc/sound/samples/bowser_organ/00_organ_1.table
python3 -c "from pathlib import Path; print(repr(Path('build/us_pc/sound/samples/bowser_organ/00_organ_1.table').read_bytes()))"
```

We see that we have `\r\n` new lines in the windows file, but `\n` in linux. I'm not sure if this could matter.

We can "fix" the newline issue with (if it is an issue): 

```
sed -i -e 's/\r//g' build/us_pc/sound/samples/bowser_organ/00_organ_1.table
```

### In tools/aiff_extract_codebook

When I "generate zeros" for the audio signals windows fails on 


```
tools/aiff_extract_codebook sound/samples/instruments/14_strings_5.aiff
```

Windows: fails

```
tabledesign: input AIFC file [sound/samples/instruments/14_strings_5.aiff] could not be opened.
```

Linux: seems to work correctly:
```
2
2
    0     0     0     0     0     0     0     0 
    0     0     0     0     0     0     0     0 
    0     0     0     0     0     0     0     0 
    0     0     0     0     0     0     0     0 
```


Note, on windows some zeroed files like
`sound/samples/bowser_organ/00_organ_1.aiff` work fine (up to newline
difference):

```
tools/aiff_extract_codebook sound/samples/bowser_organ/00_organ_1.aiff 
```

The output is the same as it is for `sound/samples/instruments/14_strings_5.aiff`, which is shown above.


 

Test

```
tools/aiff_extract_codebook sound/samples/bowser_organ/00_organ_1.aiff >build/us_pc/sound/samples/bowser_organ/00_organ_1.table
tools/vadpcm_enc -c build/us_pc/sound/samples/bowser_organ/00_organ_1.table sound/samples/bowser_organ/00_organ_1.aiff build/us_pc/sound/samples/bowser_organ/00_organ_1.aifc


sha1sum sound/samples/bowser_organ/00_organ_1.aiff           
sha1sum build/us_pc/sound/samples/bowser_organ/00_organ_1.table           
sha1sum build/us_pc/sound/samples/bowser_organ/00_organ_1.aifc
```

Even though the newlines are different the hash of the aifc files are the same.



```
sha1sum sound/samples/bowser_organ/00_organ_1.aiff
sha1sum sound/samples/instruments/14_strings_5.aiff

tools/aiff_extract_codebook sound/samples/bowser_organ/00_organ_1.aiff >build/us_pc/sound/samples/bowser_organ/00_organ_1.table
xxd build/us_pc/sound/samples/bowser_organ/00_organ_1.table
```

It looks like for the original assets, it never even calls tabledesign, but for
custom assets it does. This is because the original assets have VADPCMCODES and
hit the version1 check to call readaifccodebook, which seems to build the
coefTable fine on win32. So it is likely there is some windows bug in
tabledesign.



### With Random Deterministic Assets

```bash
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


tools/aiff_extract_codebook sound/samples/bowser_organ/00_organ_1.aiff 

>build/us_pc/sound/samples/bowser_organ/00_organ_1.table

sha1sum sound/samples/bowser_organ/00_organ_1.aiff
sha1sum build/us_pc/sound/samples/bowser_organ/00_organ_1.table   
```

Expected:
```
69d9a23dd28edf7ba2a262342baf7c8bce6e2f8c  sound/samples/bowser_organ/00_organ_1.aiff
1e297ada8211678a1c429f4c132049d1c5d75456  build/us_pc/sound/samples/bowser_organ/00_organ_1.table
```

Windows gets:
```
$ Assertion failed: !canSeek() || (tell() == m_track->fpos_next_frame), file audiofile.cpp, line 6170
```

It runs many instances of runPull before hitting this error though.


I wrote a script to help with more rapid testing and made a branch
Erotemic/sm64-port@explore-win32-audio-issues with extra debug output.

```

./debug_audio_make.sh

# Test on the generated asset
tools/aiff_extract_codebook sound/samples/bowser_organ/00_organ_1.aiff 

# Test on the original asset
tools/aiff_extract_codebook ../sm64-port-ref/sound/samples/bowser_organ/00_organ_1.aiff 
```

It looks like for the original assets, it never even calls tabledesign, but for
custom assets it does. This is because the original assets have VADPCMCODES and
hit the version1 check to call readaifccodebook, which seems to build the
coefTable fine on win32. So it is likely there is some windows bug in
tabledesign.
