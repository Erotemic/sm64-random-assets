#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
"""
Generates non-copyrighted assets for SM64

Ignore:
    make VERSION=us -j16
    build/us_pc/sm64.us

Usage:
    In this repo run:

    python generate_assets.py --dst <PATH-TO-SM64-PORT-CHECKOUT>


Example:

    # Make a temporary directory
    rm -rf $HOME/tmp/test_assets
    mkdir -p $HOME/tmp/test_assets

    # Clone the sm64 port repo
    git clone https://github.com/sm64-port/sm64-port $HOME/tmp/test_assets/sm64-port-test

    # Clone this repo
    git clone https://github.com/Erotemic/sm64-random-assets.git $HOME/tmp/test_assets/sm64-random-assets

    # Run the asset generator
    python $HOME/tmp/test_assets/sm64-random-assets/generate_assets.py --dst $HOME/tmp/test_assets/sm64-port-test

    # Move into the port directory
    cd $HOME/tmp/test_assets/sm64-port-test

    # Compile
    make VERSION=us -j16

    # Run the executable
    build/us_pc/sm64.us


Ignore:

    # Internal Test

    # Make a temporary directory
    rm -rf $HOME/tmp/test_assets
    mkdir -p $HOME/tmp/test_assets

    # Clone the sm64 port repo
    git clone https://github.com/sm64-port/sm64-port $HOME/tmp/test_assets/sm64-port-test

    # Move into the port directory
    cd $HOME/tmp/test_assets/sm64-port-test

    # Run the asset generator
    python $HOME/code/sm64-random-assets/generate_assets.py \
        --dst $HOME/tmp/test_assets/sm64-port-test \
        --reference $HOME/code/sm64-port \
        --compare
    #--hybrid_mode

    # Compile
    make clean && make VERSION=us -j9

    # Run the executable
    build/us_pc/sm64.us


SeeAlso:
    https://github.com/TechieAndroid/sm64redrawn
"""
import ubelt as ub
import json
import scriptconfig as scfg
import rich


class GenerateAssetsConfig(scfg.DataConfig):
    """
    Generates non-copyrighted assets for SM64
    """
    dst = scfg.Value(None, help=ub.paragraph(
            '''
            Path to the sm64-port repo to generate assets for.
            '''))
    reference = scfg.Value(None, help=ub.paragraph(
            '''
            A reference to a directory with a different set of assets to
            compare against for debugging.
            '''))
    manifest_fpath = scfg.Value('auto', help=ub.paragraph(
            '''
            Path to the asset manifest to use. If "auto", attempts
            to use the one in this module directory.
            '''))
    hybrid_mode = scfg.Value(None, isflag=True, help='hybrid_mode')
    compare = scfg.Value(None, isflag=True, help='run the compare debug tool')

    reference_config = scfg.Value(None, help=ub.paragraph(
        '''
        A YAML config that allow for fine grained control over which which
        assets should use references and which should be generated. The
        following keys can be set to 1, "ref", or "reference" to specify they
        should use the reference, or "0, "gen", or "generate" to specify they
        should be generated.
        '''))


def main(cmdline=1, **kwargs):
    args = GenerateAssetsConfig.cli(cmdline=cmdline, data=kwargs)
    rich.print('args = {}'.format(ub.urepr(args, nl=1)))

    # Path to the clone of sm64-port we will generate assets for.
    output_dpath = ub.Path(args.dst).expand()

    # Find the path to the asset mainfest, which contains a list of what data
    # to be generated.
    if args.manifest_fpath == "auto":
        mod_dpath = ub.Path(__file__).parent
        asset_metadata_fpath = mod_dpath / 'asset_metadata.json'
    else:
        asset_metadata_fpath = ub.Path(args.manifest_fpath).expand()

    output_dpath = output_dpath.absolute()
    asset_metadata_fpath = asset_metadata_fpath.absolute()

    print('output_dpath = {}'.format(ub.urepr(output_dpath, nl=1)))
    print('asset_metadata_fpath = {}'.format(ub.urepr(asset_metadata_fpath, nl=1)))

    assert asset_metadata_fpath.exists()

    # Load the assets that need to be generated.
    asset_metadata = json.loads(asset_metadata_fpath.read_text())

    # Generate randomized / custom versions for each asset
    ext_to_info = ub.group_items(asset_metadata, lambda x: ub.Path(x['fname']).suffix)

    use_reference = 1
    if use_reference and args.reference is not None:
        ref_dpath = ub.Path(args.reference)
        ref_dpath = ref_dpath.absolute()

    def copy_reference(output_dpath, info, ref_dpath):
        ref_fpath = ref_dpath / info['fname']
        out_fpath = output_dpath / info['fname']
        if ref_fpath.exists():
            try:
                out_fpath.parent.ensuredir()
                ref_fpath.copy(out_fpath, overwrite=True)
            except Exception:
                print('\n\n')
                rich.print(f'[red]ERROR: copying {ref_fpath=} to {out_fpath=}')
                raise
        else:
            # A reference path might not exist because a baserom will only have
            # assets for the specific version, and the manifest lists all
            # assets from all versions.
            ...

    """
    Note: on my older processor machine, the game freezes after the startup
    splash screen fade to black and never gets to the mario head.

    Table of when this behavior happened

        png | aiff | m64 | bin | result
        ----+------+-----+-----+-------
        REF | REF  | REF | REF | worked
        gen | gen  | REF | REF | worked
        REF | REF  | gen | gen | worked
        gen | REF  | gen | gen | worked
        REF | gen  | gen | gen | worked
        gen | gen  | REF | gen | freeze
        gen | gen  | gen | REF | freeze
        gen | gen  | gen | gen | freeze

    Ah, it does freeze later in the game on whomps with,
    gen, ref, gen, gen, but is ok with ref, ref, gen, gen.
    Also ok with ref, gen, gen, gen.

    Seems to be due to the i8 textures, probably overwrote important data in
    resulting binary
    """

    from kwutil.util_yaml import Yaml
    from sm64_random_assets import image_generator
    from sm64_random_assets import audio_generator
    from sm64_random_assets import binary_generator

    reference_config = Yaml.coerce(args.reference_config)
    if reference_config is None:
        reference_config = {}

    def _refconfig_value(k):
        v = reference_config.get(k, 0)
        if str(v) in {"0", "ref", "reference"}:
            return 0
        elif str(v) in {"1", "gen", "generate"}:
            return 1
        else:
            raise Exception(f'Unknown value {v=} for {k=}')

    png_use_reference = _refconfig_value('png')
    aiff_use_reference = _refconfig_value('aiff')
    m64_use_reference = _refconfig_value('m64')
    bin_use_reference = _refconfig_value('bin')
    print(f'png_use_reference={png_use_reference}')
    print(f'aiff_use_reference={aiff_use_reference}')
    print(f'm64_use_reference={m64_use_reference}')
    print(f'bin_use_reference={bin_use_reference}')

    for info in ub.ProgIter(ext_to_info['.png'], desc='.png'):
        if not png_use_reference:
            out = image_generator.generate_image(output_dpath, info)
        if png_use_reference or (args.hybrid_mode and out['status'] != 'generated'):
            copy_reference(output_dpath, info, ref_dpath)

    for info in ub.ProgIter(ext_to_info['.aiff'], desc='.aiff'):
        if not aiff_use_reference:
            out = audio_generator.generate_audio(output_dpath, info)
        if aiff_use_reference or (args.hybrid_mode and out['status'] != 'generated'):
            copy_reference(output_dpath, info, ref_dpath)

    for info in ub.ProgIter(ext_to_info['.m64'], desc='.m64'):
        if not m64_use_reference:
            out = binary_generator.generate_binary(output_dpath, info)
        if m64_use_reference or (args.hybrid_mode and out['status'] != 'generated'):
            copy_reference(output_dpath, info, ref_dpath)

    for info in ub.ProgIter(ext_to_info['.bin'], desc='.bin'):
        if not bin_use_reference:
            out = binary_generator.generate_binary(output_dpath, info)
        if bin_use_reference or (args.hybrid_mode and out['status'] != 'generated'):
            copy_reference(output_dpath, info, ref_dpath)

    # Write a dummy .assets-local.txt to trick sm64-port into thinking assets
    # were extracted.
    header = ub.codeblock(
        '''
        # This file tracks the assets currently extracted by extract_assets.py.
        7
        ''')
    body = '\n'.join(item['fname'] for item in asset_metadata)
    text = header + '\n' + body
    assets_fpath = output_dpath / '.assets-local.txt'
    assets_fpath.write_text(text)

    if args.compare:
        from sm64_random_assets.comparison import compare
        compare(ref_dpath, output_dpath, asset_metadata_fpath)


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/sm64-random-assets/generate_assets.py --dst ~/code/sm64-port-safe
        cd ~/code/sm64-port-safe
        make VERSION=us -j16
        build/us_pc/sm64.us
    """
    main()
