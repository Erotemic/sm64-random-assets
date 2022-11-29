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
    build/us_pc/sm64.us


SeeAlso:
    https://github.com/TechieAndroid/sm64redrawn
"""
import numpy as np
import ubelt as ub
import aifc
import kwimage
import json
import os


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dst', default=None, help='Path to the sm64-port repo to generate assets for.')
    parser.add_argument('--repo', default=None, help='Path to this repo. Should not need to specify.')
    args = parser.parse_args()

    # Path to the clone of sm64-port we will generate assets for.
    if args.dst is None:
        output_dpath = ub.Path('~/code/sm64-port-safe').expand()
    else:
        output_dpath = ub.Path(args.dst).expand()

    # This path
    if args.repo is None:
        # repo_dpath = ub.Path('~/code/sm64-random-assets').expand()
        repo_dpath = ub.Path(__file__).parent
    else:
        repo_dpath = ub.Path(args.repo).expand()
    print('output_dpath = {}'.format(ub.repr2(output_dpath, nl=1)))
    print('repo_dpath = {}'.format(ub.repr2(repo_dpath, nl=1)))

    # Load the assets that need to be generated.
    asset_metadata_fpath = repo_dpath / 'asset_metadata.json'
    asset_metadata = json.loads(asset_metadata_fpath.read_text())

    # Generate randomized / custom versions for each asset
    ext_to_info = ub.group_items(asset_metadata, lambda x: x['type'])

    for info in ub.ProgIter(ext_to_info['.aiff'], desc='.aiff'):
        generate_audio(output_dpath, info)

    for info in ub.ProgIter(ext_to_info['.png'], desc='.png'):
        generate_image(output_dpath, info)

    for info in ub.ProgIter(ext_to_info['.m64'], desc='.m64'):
        generate_binary(output_dpath, info)

    for info in ub.ProgIter(ext_to_info['.bin'], desc='.bin'):
        generate_binary(output_dpath, info)

    # Write a dummy .assets-local.txt to trick sm64-port into thinking assets
    # were extracted.
    header = ub.codeblock(
        '''
        # This file tracks the assets currently extracted by extract_assets.py.
        7
        ''')
    body = '\n'.join(item['fname'] for item in asset_metadata)
    text = header + body
    assets_fpath = output_dpath / '.assets-local.txt'
    assets_fpath.write_text(text)


def generate_audio(output_dpath, info):
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
    return params


def generate_image(output_dpath, info):
    shape = info['shape']

    out_fpath = output_dpath / info['fname']
    out_fpath.parent.ensuredir()

    new_data = handle_special_texture(out_fpath.name, shape)
    if new_data is None:
        new_data = (np.random.rand(*shape) * 255).astype(np.uint8)

    kwimage.imwrite(out_fpath, new_data, backend='gdal')
    # kwimage.imwrite(out_fpath, new_data, backend='pil')
    return shape


def generate_binary(output_dpath, info):
    out_fpath = output_dpath / info['fname']
    out_fpath.parent.ensuredir()
    # Not sure what these bin/m64 file are. Zeroing them seems to work fine.
    new = b'\x00' * info['size']
    out_fpath.write_bytes(new)


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

    # Sideways italic letters
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

    name_to_text_lut['levels/castle_grounds/5.ia8.png'] = {
        # fixme
        'text': 'Peach',
        'color': 'white',
    }
    # 'levels/menu/main_menu_seg7_us.0AC40.ia8.png': 0
    return name_to_text_lut

name_to_text_lut = build_char_name_map()


def handle_special_texture(fname, shape):
    import numpy as np
    fname = str(fname)
    if fname in name_to_text_lut:
        info = name_to_text_lut[fname]
        c = info['text']
        color = info['color']
        rot = info.get('rot', 0)
        scale = info.get('scale', 1)
        bg = np.zeros(shape, dtype=np.uint8)
        h, w = shape[1], shape[0]
        if rot:
            h, w = w, h
        org = (w // 2, h // 2)
        img = kwimage.draw_text_on_image(
            bg, c, fontScale=0.6 * scale, thickness=1, org=org, halign='center',
            valign='center', color=color)
        if rot:
            img = np.rot90(img, k=3)
            img = np.flipud(img)
        return img


if __name__ == '__main__':
    """
    CommandLine:
        cd ~/code/sm64-random-assets/
        python generate_assets.py --dst ~/code/sm64-port-safe
    """
    main()
