#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
r"""
Generates non-copyrighted assets for SM64

Ignore:
    make VERSION=us -j16
    build/us_pc/sm64.us

Usage:
    In this repo run:

    python generate_assets.py --dst <PATH-TO-SM64-PORT-CHECKOUT>


CommandLine:

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
    compare = scfg.Value(None, isflag=True, help='run the compare debug tool. Can also be a YAML configuration')

    reference_config = scfg.Value(None, help=ub.paragraph(
        '''
        A YAML config that allow for fine grained control over which which
        assets should use references and which should be generated. The
        following keys can be set to 1, "ref", or "reference" to specify they
        should use the reference, or "0, "gen", or "generate" to specify they
        should be generated. Can also be "hybrid" to force hybrid mode for
        a particular key.

        Available keys are: png, aiff, bin, m64. Can also specify a key
        never_generate as a list of glob patterns to always use the reference
        for.
        '''))

    def __post_init__(self):
        from sm64_random_assets.util.util_yaml import Yaml
        reference_config = Yaml.coerce(self.reference_config)
        if reference_config is None:
            reference_config = {}
        default_reference_config = ub.udict({
            'png': 'generate',
            'aiff': 'generate',
            'm64': 'generate',
            'bin': 'generate',
            'never_generate': [],
        })
        reference_config = default_reference_config | reference_config

        for k, v in reference_config.items():
            if k == 'never_generate':
                continue
            if str(v) in {"0", "ref", "reference"}:
                reference_config[k] = 'reference'
            elif str(v) in {"1", "gen", "generate"}:
                reference_config[k] = 'generate'
            elif str(v) in {"hybrid"}:
                reference_config[k] = 'hybrid'
            else:
                raise Exception(f'Unknown value {v=} for {k=}')
        self.reference_config = reference_config

        compare = Yaml.coerce(self.compare)
        if compare is False:
            compare = None
        if isinstance(compare, int):
            compare = {} if compare > 0 else None
        if compare is not None:
            default_compare = ub.udict({
                'include': '*',
            })
            compare = default_compare | compare
        self.compare = compare


def main(cmdline=1, **kwargs):
    args = GenerateAssetsConfig.cli(cmdline=cmdline, data=kwargs)
    rich.print('args = {}'.format(ub.urepr(args, nl=2)))

    from sm64_random_assets import image_generator
    from sm64_random_assets import audio_generator
    from sm64_random_assets import binary_generator
    from sm64_random_assets.util.util_pattern import MultiPattern

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

    # Enrich the asset metadata by parsing information out of the filenames
    for info in asset_metadata:
        fname_rel = ub.Path(info['fname'])
        info['ext'] = fname_rel.suffix
        # Determine if the asset is region/version specific
        parts = [s for p in fname_rel.parts for ss in p.split('.') for s in
                 ss.split('_')]
        if 'us' in parts:
            region = 'us'
        elif 'eu' in parts:
            region = 'eu'
        elif 'jp' in parts:
            region = 'jp'
        elif 'sh' in parts:
            region = 'sh'
        else:
            region = 'any'
        info['region'] = region

    ext_to_info = ub.group_items(asset_metadata, lambda info: info['ext'])

    if args.reference is not None:
        ref_dpath = ub.Path(args.reference)
        ref_dpath = ref_dpath.absolute()
    else:
        ref_dpath = None

    if ref_dpath is None:
        # If we don't have a refernce make sure that we didn't set any flags
        # that require it.
        for k, v in args.reference_config.items():
            if k == 'never_generate':
                if v:
                    raise Exception(
                        'Reference config might want a reference asset, '
                        'but the path to the reference directory was not set.')
            else:
                if v in {'reference', 'hybrid'}:
                    raise Exception(
                        'Reference config might want a reference asset, '
                        'but the path to the reference directory was not set.')

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

    nevergen_pat = MultiPattern.coerce(args.reference_config['never_generate'])

    def check_ref_config(key, info):
        use_ref = args.reference_config[key]
        if nevergen_pat.match(info['fname']):
            use_ref = 'reference'
        is_hybrid = (args.hybrid_mode or use_ref == 'hybrid')
        return use_ref, is_hybrid

    # List to keep track of what we did
    results = []

    # Generate randomized / custom versions for each asset
    key_to_asset_generator = {
        'png': image_generator.generate_image,
        'aiff': audio_generator.generate_audio,
        'm64': binary_generator.generate_binary,
        'bin': binary_generator.generate_binary,
    }

    async def delete(fpath):
        ub.Path(fpath).delete()

    for key, generate_asset in key_to_asset_generator.items():
        for info in ub.ProgIter(ext_to_info['.' + key], desc=key):
            use_ref, is_hybrid = check_ref_config('png', info)
            out = ub.udict({'status': None}) | info
            if use_ref != "reference":
                out |= generate_asset(output_dpath, info)
            if use_ref == 'reference' or (is_hybrid and out['status'] != 'generated'):
                copied = copy_reference(output_dpath, info, ref_dpath)
                if copied:
                    out['status'] = 'copied_reference'
                else:
                    out['status'] = 'no-reference'

            out_fpath = output_dpath / info['fname']
            out['out_fpath'] = out_fpath

            ub.Executor()

            if 1:
                # Delete the associate build file
                # to speedup make?
                build_dpath = output_dpath / 'build/us'
                if not build_dpath.exists():
                    build_dpath = output_dpath / 'build/us_pc'
                if build_dpath.exists():
                    build_rel_fname = ub.Path(info['fname']).augment(ext='.inc.c', multidot=False)
                    build_fpath = build_dpath / build_rel_fname

                    if build_fpath.exists():
                        build_fpath.delete()

            results.append(out)

    # Print out some statistics about what we did
    ext_status_hist = ub.dict_hist([(r['ext'], r['region'], r['status']) for r in results])
    rich.print('Asset status histogram:')
    rich.print('{}'.format(ub.urepr(ext_status_hist, nl=1)))

    if 0:
        # Debug missing assets
        stat_to_groups = ub.group_items(results, key=lambda r: (r['ext'], r['region'], r['status']))
        print(stat_to_groups[('.png', 'any', 'value-error: image has no shape')])
        print(stat_to_groups[('.aiff', 'any', 'no-reference')])
        import xdev
        xdev.embed()

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

    if args.compare is not None:
        from sm64_random_assets.comparison import compare
        compare(ref_dpath, output_dpath, asset_metadata_fpath)


def copy_reference(output_dpath, info, ref_dpath):
    if ref_dpath is None:
        raise Exception('No reference dpath')
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
            copied = True
    else:
        # A reference path might not exist because a baserom will only have
        # assets for the specific version, and the manifest lists all
        # assets from all versions.
        copied = False
    return copied


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/sm64-random-assets/generate_assets.py --dst ~/code/sm64-port-safe
        cd ~/code/sm64-port-safe
        make VERSION=us -j16
        build/us_pc/sm64.us
    """
    main()
