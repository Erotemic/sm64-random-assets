import numpy as np
import parse
import kwimage


def generate_image(output_dpath, info):
    """
    Args:
        output_dpath (Path): where to write the generated image file
        info (dict): a dictionary from asset_metadata.json

    Returns:
        dict: containing keys: status, out_fpath

    Notes:
        Different texture types
        ia1
        ia4
        ia8
        ia16
        rgba16

    Example:
        >>> from sm64_random_assets.image_generator import generate_image
        >>> import ubelt as ub
        >>> dpath = ub.Path.appdir('sm64-random-assets/tests')
        >>> output_dpath = dpath / 'test-output'
        >>> info = {
        >>>     "fname": "actors/blue_coin_switch/blue_coin_switch_side.rgba16.png",
        >>>     "shape": [16, 32, 4]
        >>> }
        >>> out = generate_image(output_dpath, info)
        >>> assert out['status'] == 'generated'
        >>> assert out['out_fpath'].exists()
    """
    if info.get('shape', None) is None:
        return {'status': 'value-error: image has no shape'}
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

        # Reduce the size of textures
        smaller = kwimage.imresize(new_data, scale=0.5, interpolation='nearest')
        new_data = kwimage.imresize(smaller, dsize=shape[0:2][::-1], interpolation='nearest')

        # new_data[..., 0:3] = 0
        # new_data[..., 3] = 0
        out = {'status': 'randomized'}
    else:
        out = {'status': 'generated'}

    # kwimage.imwrite(out_fpath, new_data, backend='gdal')
    # kwimage.imwrite(out_fpath, new_data, backend='pil')
    kwimage.imwrite(out_fpath, new_data, backend='pil')
    out['out_fpath'] = out_fpath
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


# class AssetGenerator:
#     def match(self, fname):
#         import xdev
#         xdev.Pattern.coerce('actors/power_meter').match(fname)

class PowerMeter:
    """
    Helper to draw something useful for the power/health meter
    """

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
    """
    Can programatically generate nicer-than-random textures for some assets.
    """
    import numpy as np
    fname = str(fname)

    generators = [PowerMeter()]
    for gen in generators:
        if gen.match(fname):
            # print(f'try to generate fname={fname}')
            generated = gen.generate(fname)
            if generated is not None:
                generated = kwimage.imresize(generated, dsize=shape[0:2][::-1])
                generated = kwimage.ensure_uint255(generated.clip(0, 1))
                # print(f'generated fname={fname}')
                return generated

    generated = None
    import ubelt as ub
    if fname == 'levels/intro/2_copyright.rgba16.png':
        generated = kwimage.draw_text_on_image(
            None, ub.codeblock(
                '''
                For Educational Use Only.
                Mario is owned by Nintendo.
                Please support the official release.
                '''), color='skyblue', halign='center')

    if fname == 'levels/intro/3_tm.rgba16.png':
        generated = kwimage.draw_text_on_image(
            None, 'TM', color='white')
    if 'actors/blue_fish' in fname:
        generated = kwimage.draw_text_on_image(
            None, 'blue\nfish', color='blue')

    if 'flame' in fname:
        generated = kwimage.draw_text_on_image(
            img={'color': (0, 0, 0, 0)},
            text='flame', color='yellow')

    if 'unused' in fname:
        generated = kwimage.draw_text_on_image(
            None, 'unused', color='red')
    elif 'eyebrow' in fname:
        generated = kwimage.draw_text_on_image(
            None, 'eyebrow', color='brown')
    elif 'mips_eyes' in fname:
        generated = kwimage.draw_text_on_image(
            None, 'QQ', color='gray')
    elif 'eyes_center' in fname:
        generated = kwimage.draw_text_on_image(
            None, 'O O', color='gray')
    elif 'eyes_closed' in fname:
        generated = kwimage.draw_text_on_image(
            None, '_ _', color='gray')
    elif 'eyes_dead' in fname:
        generated = kwimage.draw_text_on_image(
            None, 'X X', color='gray')
    elif 'eye_mostly_open' in fname or 'iris_mostly_open' in fname:
        generated = kwimage.draw_text_on_image(
            None, '_ye', color='gray')
    elif 'goomba_face_blink' in fname:
        generated = kwimage.draw_text_on_image(
            {'color': 'brown'}, '- -', color='black')
    elif 'goomba_face' in fname:
        generated = kwimage.draw_text_on_image(
            {'color': 'brown'}, 'O O', color='black')
    elif 'eye_mostly_closed' in fname or 'iris_mostly_closed' in fname:
        generated = kwimage.draw_text_on_image(
            None, '_y_', color='gray')
    elif 'eye_closed' in fname or 'iris_closed' in fname:
        generated = kwimage.draw_text_on_image(
            None, '___', color='gray')
    elif 'eye_angry' in fname:
        generated = kwimage.draw_text_on_image(
            None, ' < ', color='gray')
    elif 'eye_half_closed' in fname:
        generated = kwimage.draw_text_on_image(
            None, '_y_', color='gray')
    elif 'eyes' in fname:
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

    if generated is None:
        needs_nbytes_reduction = {
            'textures/skyboxes',
            'levels/bowser',
            'bowser_shell_edge',
            'bowser_nostrils',
            'bowser_hair',
        }
        for cand in needs_nbytes_reduction:
            if cand in fname:
                # Still randomize, but reduce the compressed PNG size
                new_data = (np.random.rand(*shape) * 255).astype(np.uint8)
                generated = kwimage.imresize(new_data[::4, ::4, :],
                                             dsize=shape[0:2][::-1],
                                             interpolation='nearest')
                generated[:, :, 3] = 255

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
