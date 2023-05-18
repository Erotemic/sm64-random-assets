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
import numpy as np
import ubelt as ub
import parse
import aifc
import kwimage
import json
import os


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dst', default=None, help=(
        'Path to the sm64-port repo to generate assets for.'))
    parser.add_argument('--reference', default=None, help=(
        'A reference to a directory with a different set of assets to '
        'compare against for debugging.'
    ))
    parser.add_argument('--manifest_fpath', default=None, help=(
        'Path to the asset manifest to use. If unspecified, attempts '
        'to use the one in this repo'))
    parser.add_argument('--hybrid_mode', default=None, action='store_true', help=(
        'hybrid_mode'))
    parser.add_argument('--compare', default=None, action='store_true', help=(
        'hybrid_mode'))
    args = parser.parse_args()
    print('args.__dict__ = {}'.format(ub.repr2(args.__dict__, nl=1)))

    # Path to the clone of sm64-port we will generate assets for.
    if args.dst is None:
        output_dpath = ub.Path('~/code/sm64-port-safe').expand()
    else:
        output_dpath = ub.Path(args.dst).expand()

    # Find the path to the asset mainfest, which contains a list of what data
    # to be generated.
    if args.manifest_fpath is None:
        repo_dpath = ub.Path(__file__).parent
        asset_metadata_fpath = repo_dpath / 'asset_metadata.json'
    else:
        asset_metadata_fpath = ub.Path(args.manifest_fpath).expand()
    print('output_dpath = {}'.format(ub.urepr(output_dpath, nl=1)))
    print('asset_metadata_fpath = {}'.format(ub.urepr(asset_metadata_fpath, nl=1)))

    # Load the assets that need to be generated.
    asset_metadata = json.loads(asset_metadata_fpath.read_text())

    # Generate randomized / custom versions for each asset
    ext_to_info = ub.group_items(asset_metadata, lambda x: ub.Path(x['fname']).suffix)

    use_reference = 1
    if use_reference and args.reference is not None:
        ref_dpath = ub.Path(args.reference)

    def copy_reference(output_dpath, info, ref_dpath):
        ref_fpath = ref_dpath / info['fname']
        out_fpath = output_dpath / info['fname']
        if ref_fpath.exists():
            ref_fpath.copy(out_fpath, overwrite=True)

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

    use_reference = 0

    for info in ub.ProgIter(ext_to_info['.png'], desc='.png'):
        if not use_reference:
            out = generate_image(output_dpath, info)
        if use_reference or (args.hybrid_mode and out['status'] != 'generated'):
            copy_reference(output_dpath, info, ref_dpath)

    use_reference = 0

    for info in ub.ProgIter(ext_to_info['.aiff'], desc='.aiff'):
        if not use_reference:
            out = generate_audio(output_dpath, info)
        if use_reference or (args.hybrid_mode and out['status'] != 'generated'):
            copy_reference(output_dpath, info, ref_dpath)

    use_reference = 0

    for info in ub.ProgIter(ext_to_info['.m64'], desc='.m64'):
        if not use_reference:
            out = generate_binary(output_dpath, info)
        if use_reference or (args.hybrid_mode and out['status'] != 'generated'):
            copy_reference(output_dpath, info, ref_dpath)
    use_reference = 0

    for info in ub.ProgIter(ext_to_info['.bin'], desc='.bin'):
        if not use_reference:
            out = generate_binary(output_dpath, info)
        if use_reference or (args.hybrid_mode and out['status'] != 'generated'):
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
        _compare(ref_dpath, output_dpath, asset_metadata_fpath)


def generate_audio(output_dpath, info):
    if info.get('params', None) is None:
        return {'status': 'value-error'}
    params_dict = info['params'].copy()
    params_dict['comptype'] = params_dict['comptype'].encode()
    params_dict['compname'] = params_dict['compname'].encode()
    params = aifc._aifc_params(**params_dict)

    # Random new sound (this works surprisingly well)
    new_data = os.urandom(info['size'])

    # Zero out all sounds
    # new_data = b'\x00' * len(data)

    out_fpath = output_dpath / info['fname']
    out_fpath.parent.ensuredir()

    with open(out_fpath, 'wb') as file:
        new_file = aifc.open(file, 'wb')
        new_file.setparams(params)
        new_file.writeframes(new_data)

    # out = {'status': 'zeroed'}
    out = {'status': 'randomized'}
    return out


def generate_image(output_dpath, info):
    """
    Differnt texture types

    ia1
    ia4
    ia8
    ia16
    rgba16
    """
    if info.get('shape', None) is None:
        return {'status': 'value-error'}
    shape = info['shape']

    # Hack so we can use cv2 imwrite. Should not be needed when pil backend
    # lands in kwimage.
    if len(shape) == 3 and shape[2] == 2:
        shape = list(shape)
        # shape[2] = 4

    out_fpath = output_dpath / info['fname']
    out_fpath.parent.ensuredir()

    new_data = handle_special_texture(info['fname'], shape)
    if new_data is None:
        if out_fpath.name.endswith('.ia1.png'):
            new_data = (np.random.rand(*shape) * 255).astype(np.uint8)
            # new_data[new_data < 127] = 0
            # new_data[new_data >= 127] = 255
            # new_data[:] = 0
        elif out_fpath.name.endswith('.ia4.png'):
            new_data = (np.random.rand(*shape) * 255).astype(np.uint8)
            # new_data[new_data < 127] = 0
            # new_data[new_data >= 127] = 255
            # new_data[:] = 0
        elif out_fpath.name.endswith('.ia8.png'):
            # Its just these ones that cause the game to freeze
            # on my older CPU when there is too much variation in the data
            new_data = (np.random.rand(*shape) * 255).astype(np.uint8)
            new_data[new_data < 127] = 0
            new_data[new_data >= 127] = 255
            new_data[:] = 0
        elif out_fpath.name.endswith('.ia16.png'):
            new_data = (np.random.rand(*shape) * 255).astype(np.uint8)
            # new_data[new_data < 127] = 0
            # new_data[new_data >= 127] = 255
        elif out_fpath.name.endswith('.rgba16.png'):
            new_data = (np.random.rand(*shape) * 255).astype(np.uint8)
        else:
            new_data = (np.random.rand(*shape) * 255).astype(np.uint8)
        # new_data[..., 0:3] = 0
        # new_data[..., 3] = 0
        out = {'status': 'randomized'}
    else:
        out = {'status': 'generated'}

    # kwimage.imwrite(out_fpath, new_data, backend='gdal')
    # kwimage.imwrite(out_fpath, new_data, backend='pil')
    kwimage.imwrite(out_fpath, new_data, backend='pil')
    return out


def generate_binary(output_dpath, info):
    if info.get('size', None) is None:
        return {'status': 'value-error'}
    out_fpath = output_dpath / info['fname']
    out_fpath.parent.ensuredir()
    # Not sure what these bin/m64 file are. Zeroing them seems to work fine.
    new = b'\x00' * info['size']
    out_fpath.write_bytes(new)
    out = {'status': 'zeroed'}
    return out


def build_char_name_map():
    """
    Create a manual mapping from texture names to the glyph we want them to
    represent. This is only partially complete.

    # Font Notes:

    textures
    ipl3_font_00.ia1.png = A
    ipl3_font_25.ia1.png = Z
    ipl3_font_26.ia1.png = 0
    ipl3_font_35.ia1.png = 9

    36-49
    !"#'*+,-./;=?@


    import kwplot
    kwplot.autompl()
    kwplot.imshow(img)


    # In textures/segment2/

    Looks like rotated numbers and letters.

    segment2.00000.rgba16.png - Big 0
    segment2.00200.rgba16.png - Big 1
    segment2.00400.rgba16.png - Big 2
    """
    ipl_chars = []
    for i in range(26):
        ipl_chars.append(chr(ord('A') + i))
    for i in range(10):
        ipl_chars.append(chr(ord('0') + i))
    ipl_chars.extend('!"#\'*+,-./;=?@')

    name_to_text_lut = {}
    for i, c in enumerate(ipl_chars):
        n = 'textures/ipl3_raw/ipl3_font_{:02d}.ia1.png'.format(i)
        name_to_text_lut[n] = {
            'text': c,
            'color': 'white',
            'scale': 0.8,
        }

    # Big fancy letters
    segment_fmt = 'textures/segment2/segment2.{:03X}00.rgba16.png'
    for i in range(10):
        n = segment_fmt.format(i * 2)
        c = str(i)
        name_to_text_lut[n] = {
            'text': c,
            'color': 'orange',
        }
    for i in range(26):
        n = segment_fmt.format(20 + i * 2)
        c = chr(ord('A') + i)
        name_to_text_lut[n] = {
            'text': c,
            'color': 'orange',
        }

    segment2_rgba16_data = [
        {'index': 0x04800, 'text': "'"},
        {'index': 0x04A00, 'text': '"'},
        {'index': 0x05000, 'text': '?'},
        {'index': 0x05600, 'text': 'x', 'comment': 'times'},
    ]
    for item in segment2_rgba16_data:
        n = 'textures/segment2/segment2.{index:05X}.rgba16.png'.format(**item)
        item.setdefault('color', 'orange')
        name_to_text_lut[n] = item

    segment2_rgba16_data = [
        {'index': 0x05800, 'text': '$', 'comment': 'coin', 'color': 'yellow'},
        {'index': 0x05A00, 'text': 'O', 'comment': 'mario head', 'color': 'red'},
        {'index': 0x05C00, 'text': '*', 'comment': 'star', 'color': 'yellow'},
        {'index': 0x06200, 'text': '3', 'color': 'green', 'scale': 0.5, 'background': 'black'},
        {'index': 0x06280, 'text': '3', 'color': 'green', 'scale': 0.5, 'background': 'black'},
        {'index': 0x06300, 'text': '6', 'color': 'green', 'scale': 0.5, 'background': 'black'},
        {'index': 0x07080, 'text': '.', 'color': 'yellow'},
        {'index': 0x07B50, 'text': '8', 'color': 'gray', 'comment': 'camera'},
        {'index': 0x07D50, 'text': 'O', 'color': 'yellow', 'comment': 'lakitu head'},
        {'index': 0x07F50, 'text': 'X', 'color': 'red', 'comment': 'locked X', 'background': 'darkred'},
        {'index': 0x08150, 'text': '^', 'color': 'yellow', 'comment': 'c-up'},
        {'index': 0x081D0, 'text': 'V', 'color': 'yellow', 'comment': 'c-down'},
    ]
    for item in segment2_rgba16_data:
        n = 'textures/segment2/segment2.{index:05X}.rgba16.png'.format(**item)
        name_to_text_lut[n] = item

    main_menu_texts = [
        {'index': 0x0AC40, 'text': '0', 'color': 'white', 'scale': 0.5, 'binary': True},
    ]
    # Numbers
    for i in range(1, 10):
        new = main_menu_texts[0].copy()
        new['text'] = str(i)
        new['index'] = new['index'] + (64 * i)
        main_menu_texts.append(new)
    # Letters
    for i in range(0, 26):
        new = main_menu_texts[0].copy()
        new['text'] = chr(i + 65)
        new['index'] = new['index'] + (64 * (i + 10))
        main_menu_texts.append(new)
    for item in main_menu_texts:
        n = 'levels/menu/main_menu_seg7_us.{index:05X}.ia8.png'.format(**item)
        name_to_text_lut[n] = item
    mmia8 = {'color': 'white', 'scale': 0.5, 'binary': True}
    main_menu_texts2 = [
        {'index': 0x0B540 + 64 * 0, 'text': 'O', 'comment': 'coin', **mmia8},
        {'index': 0x0B540 + 64 * 1, 'text': 'x', 'comment': 'times', **mmia8},
        {'index': 0x0B540 + 64 * 2, 'text': '*', 'comment': 'star', **mmia8},
        {'index': 0x0B540 + 64 * 3, 'text': '-', 'comment': '', **mmia8},
        {'index': 0x0B540 + 64 * 4, 'text': ',', 'comment': '', **mmia8},
        {'index': 0x0B540 + 64 * 5, 'text': "'", 'comment': '', **mmia8},
        {'index': 0x0B540 + 64 * 6, 'text': '!', 'comment': '', **mmia8},
        {'index': 0x0B540 + 64 * 7, 'text': '?', 'comment': '', **mmia8},
        {'index': 0x0B540 + 64 * 8, 'text': '@', 'comment': 'face', **mmia8},
        {'index': 0x0B540 + 64 * 9, 'text': '%', 'comment': 'not sure', **mmia8},
        {'index': 0x0B540 + 64 * 10, 'text': '.', 'comment': '', **mmia8},
        {'index': 0x0B540 + 64 * 11, 'text': '&', 'comment': '', **mmia8},
    ]
    for item in main_menu_texts2:
        n = 'levels/menu/main_menu_seg7_us.{index:05X}.ia8.png'.format(**item)
        name_to_text_lut[n] = item

    # Sideways numbers
    # font_graphics.05900.ia4
    offset = 0x05900
    fmt = 'textures/segment2/font_graphics.{:05X}.ia4.png'
    inc = 64
    for i in range(0, 10):
        n = fmt.format(offset + i * inc)
        c = chr(ord('0') + i)
        name_to_text_lut[n] = {
            'text': c,
            'color': 'white',
            'rot': 1,
            'scale': 0.5
        }

    # Sideways italic capital letters
    'font_graphics.05B80.ia4.png'
    'font_graphics.05BC0.ia4.png'
    fmt = 'textures/segment2/font_graphics.{:05X}.ia4.png'
    offset = 0x05B80
    inc = 0x05BC0 - offset
    for i in range(26):
        n = fmt.format(offset + i * inc)
        c = chr(ord('A') + i)
        name_to_text_lut[n] = {
            'text': c,
            'color': 'white',
            'rot': 1,
            'scale': 0.5
        }

    # Sideways italic lowercase letters
    # font_graphics.06200.ia4.png
    fmt = 'textures/segment2/font_graphics.{:05X}.ia4.png'
    offset = 0x06200
    inc = 64
    for i in range(26):
        n = fmt.format(offset + i * inc)
        c = chr(ord('a') + i)
        name_to_text_lut[n] = {
            'text': c,
            'color': 'white',
            'rot': 1,
            'scale': 0.5
        }

    # Green letters with black background
    fmt = 'textures/segment2/segment2.{:05X}.rgba16.png'
    offset = 0x06380
    inc = 0x06400 - 0x06380
    for i in range(26):
        n = fmt.format(offset + i * inc)
        c = chr(ord('A') + i)
        name_to_text_lut[n] = {
            'text': c,
            'color': 'green',
            'scale': 0.5,
            'background': 'black',
        }

    n = 'textures/segment2/font_graphics.06410.ia4.png'
    name_to_text_lut[n] = {'text': ':', 'color': 'white', 'rot': 1, 'scale': 0.5}

    n = 'textures/segment2/font_graphics.06420.ia4.png'
    name_to_text_lut[n] = {'text': '-', 'color': 'white', 'rot': 1, 'scale': 0.5}

    # Not entirely sure about some of these
    ia4_font_graphics_data = [
        {'index': 0x06880, 'text': 'I', 'comment': 'updown arrow', 'utf': '⬍'},
        {'index': 0x068C0, 'text': '!'},
        {'index': 0x06900, 'text': 'O', 'comment': 'coin symbol', 'utf': '🪙'},
        {'index':    None, 'text': 'x', 'comment': 'times symbol', 'utf': None},
        {'index':    None, 'text': '('},
        {'index':    None, 'text': 'H', 'comment': 'double paren'},
        {'index':    None, 'text': ')'},
        {'index':    None, 'text': '~'},
        {'index':    None, 'text': '.', 'comment': 'cdot?'},
        {'index':    None, 'text': '%'},
        {'index':    None, 'text': '.'},
        {'index':    None, 'text': ','},
        {'index':    None, 'text': "'"},
        {'index':    None, 'text': '?'},
        {'index':    None, 'text': '*', 'comment': 'filled star'},
        {'index':    None, 'text': '*', 'comment': 'unfilled star'},
        {'index':    None, 'text': '"', 'comment': ''},
        {'index':    None, 'text': '"', 'comment': ''},
        {'index':    None, 'text': ':', 'comment': ''},
        {'index':    None, 'text': '-', 'comment': ''},
        {'index':    None, 'text': '&', 'comment': ''},
        # Sideways bold captial letters
        # Only 5 of these corresponding to buttons.
        {'index': 0x06DC0, 'text': 'A'},
        {'index':    None, 'text': 'B'},
        {'index':    None, 'text': 'C'},
        {'index':    None, 'text': 'Z'},
        {'index':    None, 'text': 'R'},
        {'index':    None, 'text': '^', 'comment': 'direction arrow'},
        {'index':    None, 'text': 'V', 'comment': 'direction arrow'},
        {'index':    None, 'text': '<', 'comment': 'direction arrow'},
        {'index': 0x06FC0, 'text': '>', 'comment': 'direction arrow'},
    ]
    base = 0x06880
    for inc, item in enumerate(ia4_font_graphics_data):
        index = base + (0x40 * inc)
        if item.get('index', None) is not None:
            assert item['index'] == index
        item['index'] = index

    for item in ia4_font_graphics_data:
        n = 'textures/segment2/font_graphics.{index:05X}.ia4.png'.format(**item)
        name_to_text_lut[n] = {'text': item['text'], 'color': 'white', 'rot': 1, 'scale': 0.5}

    ia1_segment_data = [
        {'index':    0x06410, 'text': ':', 'base': 'font_graphics'},
        {'index':    0x06420, 'text': '-', 'base': 'font_graphics'},
        {'index':    0x07340, 'text': '|', 'base': 'segment2'},
    ]
    for item in ia1_segment_data:
        n = 'textures/segment2/{base}.{index:05X}.ia1.png'.format(**item)
        name_to_text_lut[n] = {'text': item['text'], 'color': 'white', 'rot': 1, 'scale': 0.5}

    name_to_text_lut['levels/castle_grounds/5.ia8.png'] = {
        # fixme
        'text': 'Peach',
        'color': 'white',
    }
    # 'levels/menu/main_menu_seg7_us.0AC40.ia8.png': 0
    return name_to_text_lut

name_to_text_lut = build_char_name_map()


def _compare(ref_dpath, output_dpath, asset_metadata_fpath):
    """
    Developer scratchpad
    """
    dst = output_dpath
    ref = ref_dpath
    # dst = ub.Path('$HOME/tmp/test_assets/sm64-port-test').expand()
    # ref = ub.Path('$HOME/code/sm64-port').expand()
    # asset_metadata_fpath = ub.Path('$HOME/code/sm64-random-assets/asset_metadata.json').expand()

    # Load the assets that need to be generated.
    asset_metadata = json.loads(asset_metadata_fpath.read_text())
    # Remove non-existing data
    asset_metadata = [info for info in asset_metadata if (ref / info['fname']).exists() ]

    # Enrich the metadata
    import parse
    # Extract the hex index
    pat = parse.Parser('{base}.{hex}.{imgtype}.png')
    for item in asset_metadata:
        name = ub.Path(item['fname']).name
        result = pat.parse(name)
        if result is not None:
            item['index'] = int(result['hex'], base=16)
            item['base'] = result['base']
            item['imgtype'] = result['imgtype']

    # Generate randomized / custom versions for each asset
    ext_to_info = ub.group_items(asset_metadata, lambda x: ub.Path(x['fname']).suffix)
    subinfos = ub.group_items(ext_to_info['.png'], lambda x: str(ub.Path(x['fname']).parent))

    # relevant = [x for x in ext_to_info['.png'] if x['fname'].endswith('.ia8.png')]

    compare_dpath = (dst / 'asset_compare').ensuredir()
    import xdev
    xdev.view_directory(compare_dpath)
    for key, subinfo in ub.ProgIter(subinfos.items(), desc='compare'):

        compare_fpath = compare_dpath / key.replace('/', '_') + '.png'

        group = subinfo

        # subinfo = subinfos['textures/segment2']
        # subinfo = subinfos['textures/ipl3_raw']
        # subinfo = subinfos['actors/mario']
        # relevant = subinfo
        # # relevant = [info for info in subinfo if 'index' in info]
        # # relevant = sorted(relevant, key=lambda x: (x['base'], x['index']))

        # group = relevant

        # groups = ub.group_items(relevant, lambda x: x['imgtype'])
        # for g, group in list(groups.items()):
        #     # g = 'rgba16.png'
        #     group = groups[g]
        #     if group:
        #         break

        # group = groups['ia4']
        # group = groups['ia1']
        # group = groups['rgba16']
        # group = groups['ia8']
        # group = groups['ia16']

        cells = []
        for info in group:
            fpath1 = ref / info['fname']
            fpath2 = dst / info['fname']
            # Remove alpha channel
            img1 = kwimage.imread(fpath1, backend='pil')
            img2 = kwimage.imread(fpath2, backend='pil')

            if img1.shape[2] == 2:
                img1 = np.dstack([kwimage.atleast_3channels(img1[..., 0]), img1[..., 1]])
            if img2.shape[2] == 2:
                img2 = np.dstack([kwimage.atleast_3channels(img2[..., 0]), img2[..., 1]])

            bg1 = kwimage.checkerboard(dsize=img1.shape[0:2][::-1],
                                       off_value=32, on_value=64, dtype=np.uint8)
            bg2 = kwimage.checkerboard(dsize=img2.shape[0:2][::-1],
                                       off_value=32, on_value=64, dtype=np.uint8)

            img1 = kwimage.overlay_alpha_images(img1, bg1, keepalpha=0)
            img2 = kwimage.overlay_alpha_images(img2, bg2, keepalpha=0)

            # alpha1 = img1[..., 3]
            # alpha2 = img2[..., 3]
            img1 = kwimage.ensure_float01(img1[..., 0:3])
            img2 = kwimage.ensure_float01(img2[..., 0:3])
            # img1 = np.dstack([img1, alpha1 / 255])
            # img2 = np.dstack([img2, alpha1 / 255])

            img1 = kwimage.imresize(img1, max_dim=128, interpolation='nearest')
            img2 = kwimage.imresize(img2, max_dim=128, interpolation='nearest')

            cell = kwimage.stack_images([img1, img2], axis=1, pad=4, bg_value='purple')
            text = str(str(fpath2.name).split('.')[0:2])
            cell = kwimage.draw_header_text(cell, text, fit=True)
            cells.append(cell)

        canvas = kwimage.stack_images_grid(cells, pad=16, bg_value='green', chunksize=8)
        canvas = kwimage.normalize(canvas)

        canvas = kwimage.ensure_uint255(canvas)
        canvas = kwimage.draw_header_text(canvas, key)
        kwimage.imwrite(compare_fpath, canvas)

        # import kwplot
        # kwplot.autompl()
        # kwplot.imshow(canvas)

    # fname = 'levels/castle_grounds/5.ia8.png'
    # shape = (32, 64, 4)
    # info = name_to_text_lut[fname]


# class AssetGenerator:
#     def match(self, fname):
#         import xdev
#         xdev.Pattern.coerce('actors/power_meter').match(fname)

class PowerMeter:

    def match(self, fname):
        return 'actors/power_meter/power_meter_' in fname

    def generate(self, fname):
        pat = parse.Parser('actors/power_meter/power_meter_{type}.rgba16.png')
        result = pat.parse(fname)

        mapping = {
            'full': 8,
            'seven_segments': 7,
            'six_segments': 6,
            'five_segments': 5,
            'four_segments': 4,
            'three_segments': 3,
            'two_segments': 2,
            'one_segment': 1,
        }
        power = mapping.get(result.named['type'], None)
        if power is None:
            return None
        else:
            power_to_color = {
                8: kwimage.Color.coerce('lightblue'),
                6: kwimage.Color.coerce('lightgreen'),
                4: kwimage.Color.coerce('yellow'),
                2: kwimage.Color.coerce('red'),
                1: kwimage.Color.coerce('brown'),
            }
            if power in power_to_color:
                color = power_to_color[power]
            else:
                color1 = power_to_color[power + 1]
                color2 = power_to_color[power - 1]
                color = color1.interpolate(color2, alpha=0.5)

            canvas = np.zeros((64, 64, 4), dtype=np.float32)
            circle = kwimage.Polygon.circle((32, 32), 32)
            canvas = circle.draw_on(canvas, color=color)
            canvas = canvas.clip(0, 1)
            return canvas
            # kwplot.imshow(canvas)


def handle_special_texture(fname, shape):
    import numpy as np
    fname = str(fname)

    generators = [PowerMeter()]
    for gen in generators:
        if gen.match(fname):
            print(f'try to generate fname={fname}')
            generated = gen.generate(fname)
            if generated is not None:
                generated = kwimage.imresize(generated, dsize=shape[0:2][::-1])
                generated = kwimage.ensure_uint255(generated.clip(0, 1))
                print(f'generated fname={fname}')
                return generated

    generated = None
    if fname == 'levels/intro/2_copyright.rgba16.png':
        generated = kwimage.draw_text_on_image(
            None, 'For Educational Use Only', color='skyblue')
    if fname == 'levels/intro/3_tm.rgba16.png':
        generated = kwimage.draw_text_on_image(
            None, 'TM', color='white')
    if 'actors/blue_fish' in fname:
        generated = kwimage.draw_text_on_image(
            None, 'blue\nfish', color='blue')
    if 'eyes' in fname:
        generated = kwimage.draw_text_on_image(
            None, 'eyes', color='gray')
    elif 'eye' in fname:
        generated = kwimage.draw_text_on_image(
            None, 'eye', color='gray')
    elif 'bubble' in fname:
        generated = kwimage.draw_text_on_image(
            None, 'bubble', color='lightblue')
    elif 'coin' in fname:
        generated = kwimage.draw_text_on_image(
            None, '$', color='yellow')
        # TODO: fix when background color has alpha
        # generated = kwimage.draw_text_on_image(
        #     {'color': (0.0, 0.0, 0.0, 0.0)}, '$', color='yellow')
    elif 'thwomp_face' in fname:
        generated = kwimage.draw_text_on_image(
            {'color': 'lightblue'}, ':(', color='black')

    if generated is not None:
        generated = kwimage.imresize(generated, dsize=shape[0:2][::-1])
        if generated.dtype.kind == 'f':
            generated = generated.clip(0, 1)
        generated = kwimage.ensure_uint255(generated)
        return generated

    if fname in name_to_text_lut:
        info = name_to_text_lut[fname]
        text = info['text']
        color = info['color']
        rot = info.get('rot', 0)
        scale = info.get('scale', 1)
        binary = info.get('binary', 0)
        bg = np.zeros(shape, dtype=np.uint8)
        h, w = shape[0:2]
        if rot:
            bg = np.rot90(bg, k=1)
            bg = np.ascontiguousarray(bg)
            h, w = w, h
        org = (w // 2, h // 2)
        img, info = kwimage.draw_text_on_image(
            bg,
            # {'width': w, 'height': h}
            text, fontScale=0.6 * scale, thickness=1, org=org, halign='center',
            valign='center', color=color, return_info=True)

        if rot:
            img = np.fliplr(img)
            img = np.rot90(img, k=-1)
            img = np.ascontiguousarray(img)

        if binary:
            thresh = 160
            img[img >= thresh] = 255
            img[img < thresh] = 0
        return img


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/sm64-random-assets/generate_assets.py --dst ~/code/sm64-port-safe
        cd ~/code/sm64-port-safe
        make VERSION=us -j16
        build/us_pc/sm64.us
    """
    main()
