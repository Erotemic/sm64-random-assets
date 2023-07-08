"""
Helpers to compare generated assets versus a reference
"""
import json
import ubelt as ub
import numpy as np
import kwimage


def is_headless():
    """
    Hueristic to see if the user likely has a display or not.
    Not comprehensive.

    References:
        https://stackoverflow.com/questions/52964022/how-to-detect-if-the-current-go-process-is-running-in-a-headless-non-gui-envir
    """
    import sys
    import os
    if sys.platfrom.startswith('win32'):
        return True
    else:
        DISPLAY = os.environ.get('DISPLAY', '')
        return bool(DISPLAY)


def compare(ref_dpath, output_dpath, asset_metadata_fpath):
    """
    Developer scratchpad
    """
    import parse
    import xdev
    print(f'asset_metadata_fpath={asset_metadata_fpath}')
    print(f'output_dpath={output_dpath}')
    print(f'ref_dpath={ref_dpath}')
    dst = output_dpath.absolute()
    ref = ref_dpath.absolute()
    print(f'dst={dst}')
    print(f'ref={ref}')
    # dst = ub.Path('$HOME/tmp/test_assets/sm64-port-test').expand()
    # ref = ub.Path('$HOME/code/sm64-port').expand()
    # asset_metadata_fpath = ub.Path('$HOME/code/sm64-random-assets/asset_metadata.json').expand()

    # Load the assets that need to be generated.
    asset_metadata = json.loads(asset_metadata_fpath.read_text())
    # Remove non-existing data
    asset_metadata = [info for info in asset_metadata if (ref / info['fname']).exists() ]

    # Enrich the metadata
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

    if not is_headless():
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
