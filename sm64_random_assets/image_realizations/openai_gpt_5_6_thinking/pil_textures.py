from __future__ import annotations

import fnmatch
import hashlib
import math
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw


# ---------------------------------
# Deterministic helpers
# ---------------------------------


def _stable_seed(text: str) -> int:
    return int(hashlib.sha256(text.encode('utf8')).hexdigest()[:16], 16) & 0x7FFFFFFF


def _to_rng(rng, fname: str):
    if rng is None:
        return np.random.RandomState(_stable_seed(fname))
    seed = int(rng.randint(0, 2 ** 31 - 1)) ^ _stable_seed(fname)
    return np.random.RandomState(seed)


def _clip_color(color):
    return tuple(int(max(0, min(255, c))) for c in color)


def _mix(a, b, t):
    return tuple(int(round((1 - t) * x + t * y)) for x, y in zip(a, b))


def _jitter(color, delta, rng):
    arr = np.array(color, dtype=float)
    arr = arr + rng.randint(-delta, delta + 1, size=len(color))
    return _clip_color(arr)


def _soft_noise_points(draw, w, h, colors, rng, density=0.06):
    count = max(4, int(w * h * density))
    for _ in range(count):
        draw.point((rng.randint(0, w), rng.randint(0, h)), fill=_mix(colors[0], colors[2], rng.rand()))


# ---------------------------------
# Intent analysis
# ---------------------------------


@dataclass(frozen=True)
class TextureIntent:
    fname: str
    subject: str
    role: str
    motif: str
    family: str
    notes: str = ''


_PATTERN_RULES = [
    # sprite / VFX
    ('actors/*/sparkle*',          dict(subject='sparkle', role='sprite', motif='sparkle')),
    ('actors/*/explosion*',        dict(subject='lava', role='sprite', motif='explosion')),
    ('actors/*/flame*',            dict(subject='lava', role='sprite', motif='flame')),
    ('actors/*/*smoke*',           dict(subject='smoke', role='sprite', motif='smoke')),
    ('actors/*/water_bubble*',     dict(subject='water', role='sprite', motif='bubble')),
    ('actors/water_wave/*',         dict(subject='water', role='sprite', motif='wave')),
    ('actors/*/water_ring*',       dict(subject='water', role='sprite', motif='ring')),
    ('actors/*/water_splash*',     dict(subject='water', role='sprite', motif='splash')),
    ('actors/*/*particle*',        dict(role='sprite', motif='particle')),
    ('actors/*/bubble*',           dict(subject='water', role='sprite', motif='bubble')),
    ('actors/tree/*',              dict(subject='foliage', role='sprite', motif='tree')),
    # eyes / faces
    ('actors/*/*eye*',             dict(subject='eye', role='face', motif='eye')),
    ('actors/*/*iris*',            dict(subject='eye', role='face', motif='eye')),
    ('actors/*/*pupil*',           dict(subject='eye', role='face', motif='eye')),
    ('actors/*/*mouth*',           dict(subject='mouth', role='face', motif='mouth')),
    ('actors/*/*face*',            dict(role='face')),
    # common actor parts
    ('actors/*/*shell*',           dict(subject='shell', motif='shell')),
    ('actors/coin/*',               dict(subject='coin', motif='coin')),
    ('actors/bobomb/*left_side*',   dict(subject='bobomb_body', motif='bomb_body')),
    ('actors/bobomb/*right_side*',  dict(subject='bobomb_body', motif='bomb_body')),
    ('actors/king_bobomb/*left_side*',  dict(subject='bobomb_body', motif='bomb_body')),
    ('actors/king_bobomb/*right_side*', dict(subject='bobomb_body', motif='bomb_body')),
    ('actors/king_bobomb/*body*',   dict(subject='bobomb_body', motif='bomb_body')),
    ('actors/*/*scales*',          dict(subject='scales', motif='scales')),
    ('actors/*/*skin*',            dict(subject='skin', motif='skin')),
    ('actors/*/*dress*',           dict(subject='fabric', motif='dress')),
    ('actors/*/*cap*',             dict(subject='fabric', motif='cap')),
    ('actors/*/*jewel*',           dict(subject='jewel', motif='jewel')),
    ('actors/*/*beak*',            dict(subject='beak', motif='beak')),
    ('actors/*/*horn*',            dict(subject='ivory', motif='horn')),
    ('actors/*/*claw*',            dict(subject='ivory', motif='claw')),
    ('actors/*/*tooth*',           dict(subject='ivory', motif='tooth')),
    ('actors/*/*spike*',           dict(subject='ivory', motif='spike')),
    ('actors/*/*leaf*',            dict(subject='foliage', motif='leaf')),
    ('actors/*/*flower*',          dict(subject='flower', motif='flower')),
    ('actors/*/*petal*',           dict(subject='flower', motif='flower')),
    ('actors/*/*stem*',            dict(subject='foliage', motif='stem')),
    ('actors/*/*pages*',           dict(subject='pages', motif='pages')),
    ('actors/*/*cover*',           dict(subject='book_cover', motif='cover')),
    ('actors/*/*keys*',            dict(subject='piano_keys', motif='keys')),
    ('actors/*/*lens*',            dict(subject='lens', motif='lens')),
    ('actors/*/*logo*',            dict(subject='emblem', role='overlay', motif='logo')),
    ('actors/*/*wing*',            dict(subject='feather', motif='wing')),
    ('actors/*/*fins*',            dict(subject='feather', motif='fins')),
    ('actors/*/*hair*',            dict(subject='fur', motif='hair')),
    ('actors/*/*fur*',             dict(subject='fur', motif='fur')),
    ('actors/*/*feather*',         dict(subject='feather', motif='feather')),
    ('actors/*/*cloud*',           dict(subject='cloud', motif='cloud')),
    ('actors/*/*egg*',             dict(subject='egg', motif='egg')),
    ('actors/*/*bars*',            dict(subject='metal', motif='bars')),
    ('actors/*/*sign*',            dict(subject='sign', role='sign', motif='sign')),
    ('actors/*/*door*',            dict(role='door')),
    ('actors/door/*overlay*',      dict(role='overlay', motif='door-overlay')),
    ('actors/door/*lock*',         dict(subject='metal', role='overlay', motif='lock')),
    ('actors/exclamation_box/*',   dict(role='box')),
    ('actors/capswitch/*',         dict(role='box')),
    # level / texture groups
    ('textures/skyboxes/*',        dict(role='skybox')),
    ('textures/sky/*',             dict(subject='sky')),
    ('textures/water/jrb_textures.*', dict(subject='water', motif='sea_water')),
    ('textures/water/*',           dict(subject='water')),
    ('textures/fire/*',            dict(subject='lava')),
    ('textures/grass/wf_textures.*', dict(subject='grass', motif='wildflower_grass')),
    ('textures/grass/*',           dict(subject='grass')),
    ('textures/snow/*',            dict(subject='snow')),
    ('textures/cave/*',            dict(subject='stone', motif='cave')),
    ('textures/mountain/*',        dict(subject='stone', motif='mountain')),
    ('textures/machine/*',         dict(subject='metal', motif='machine')),
    ('textures/spooky/*',          dict(subject='fabric', motif='spooky')),
    ('textures/inside/*',          dict(subject='wood', motif='inside')),
    ('textures/outside/*',         dict(subject='brick', motif='outside')),
    ('textures/generic/bob_textures.*', dict(subject='grass', motif='battlefield_grass')),
    ('textures/generic/*',         dict(subject='stone', motif='generic')),
    ('levels/bob/*',               dict(subject='grass', motif='battlefield_grass')),
    ('levels/bob/*.rgba16.png',    dict(subject='portrait', role='portrait', motif='bobomb_battlefield_portrait')),
    ('textures/effect/lava_bubble*', dict(subject='lava', role='sprite', motif='bubble')),
    ('textures/effect/flower*',    dict(subject='flower', motif='flower')),
    # level-local fallbacks
    ('levels/*/*wall*',            dict(subject='brick', role='wall')),
    ('levels/*/*floor*',           dict(subject='stone', role='floor')),
]


_FAMILY_DEFAULTS = {
    'bowser':        dict(subject='shell', motif='reptile'),
    'koopa':         dict(subject='shell', motif='turtle'),
    'koopa_shell':   dict(subject='shell', motif='turtle'),
    'lakitu_enemy':  dict(subject='cloud', motif='cloud'),
    'lakitu_cameraman': dict(subject='cloud', motif='cloud'),
    'boo':           dict(subject='ghost', motif='ghost'),
    'boo_castle':    dict(subject='ghost', motif='ghost'),
    'penguin':       dict(subject='feather', motif='penguin'),
    'klepto':        dict(subject='feather', motif='bird'),
    'hoot':          dict(subject='feather', motif='bird'),
    'bub':           dict(subject='scales', motif='fish'),
    'bubba':         dict(subject='scales', motif='fish'),
    'unagi':         dict(subject='scales', motif='eel'),
    'piranha_plant': dict(subject='foliage', motif='plant'),
    'snowman':       dict(subject='snow', motif='snowman'),
    'book':          dict(subject='book_cover', motif='book'),
    'coin':          dict(subject='coin', motif='coin'),
    'bookend':       dict(subject='book_cover', motif='book'),
    'mad_piano':     dict(subject='wood', motif='piano'),
    'yoshi_egg':     dict(subject='egg', motif='egg'),
    'haunted_cage':  dict(subject='metal', motif='cage'),
    'bomb':          dict(subject='metal', motif='bomb'),
    'bobomb':        dict(subject='metal', motif='bomb'),
    'king_bobomb':   dict(subject='metal', motif='bomb'),
    'chain_chomp':   dict(subject='metal', motif='iron'),
    'mario':         dict(subject='fabric', motif='hero'),
    'water_wave':    dict(subject='water', motif='wave'),
    'mario_cap':     dict(subject='fabric', motif='hero'),
    'peach':         dict(subject='fabric', motif='princess'),
}


def _match_rule(low: str):
    out = {}
    for pat, updates in _PATTERN_RULES:
        if fnmatch.fnmatch(low, pat):
            out.update(updates)
    return out


def analyze_texture_intent(fname: str):
    low = fname.lower()
    parts = low.split('/')
    family = parts[1] if len(parts) > 1 and parts[0] == 'actors' else parts[1] if len(parts) > 1 else ''
    rule_updates = _match_rule(low)
    defaults = {
        'subject': 'generic',
        'role': 'tile',
        'motif': 'generic',
        'family': family,
    }
    if family in _FAMILY_DEFAULTS:
        defaults.update(_FAMILY_DEFAULTS[family])
    defaults.update(rule_updates)

    # substring backstops
    if 'overlay' in low and defaults['role'] == 'tile':
        defaults['role'] = 'overlay'
    if defaults['role'] == 'face' and defaults['subject'] == 'generic':
        defaults['subject'] = 'eye' if 'eye' in low or 'iris' in low or 'pupil' in low else 'mouth'
    if 'metal' in low and defaults['subject'] == 'generic':
        defaults['subject'] = 'metal'
    if 'wood' in low and defaults['subject'] == 'generic':
        defaults['subject'] = 'wood'
    if 'snow' in low and defaults['subject'] == 'generic':
        defaults['subject'] = 'snow'
    if 'water' in low and defaults['subject'] == 'generic':
        defaults['subject'] = 'water'
    if 'lava' in low and defaults['subject'] == 'generic':
        defaults['subject'] = 'lava'
    if (low.startswith('levels/bob/') or low.startswith('textures/generic/bob_textures.')) and defaults['subject'] in {'generic', 'stone'} and defaults['role'] != 'portrait':
        defaults['subject'] = 'grass'
        defaults['motif'] = 'battlefield_grass'
    if family == 'coin' and defaults['subject'] == 'generic':
        defaults['subject'] = 'coin'
        defaults['motif'] = 'coin'
    if family == 'mario' and 'eyes' in low:
        defaults['subject'] = 'eye'
        defaults['role'] = 'face'
        defaults['motif'] = 'mario_eye'
    if family in {'bobomb', 'king_bobomb'} and any(tok in low for tok in ['left_side', 'right_side', 'body']):
        defaults['subject'] = 'bobomb_body'
        defaults['motif'] = 'bomb_body'
    return TextureIntent(fname=fname, **defaults)


def classify_texture_subject(fname: str) -> str:
    return analyze_texture_intent(fname).subject


def classify_texture_role(fname: str) -> str:
    return analyze_texture_intent(fname).role


# ---------------------------------
# Palettes
# ---------------------------------


def _palette(subject: str, motif: str, family: str, rng):
    palettes = {
        'grass':      ((73, 112, 51), (110, 158, 77), (162, 198, 108), (48, 77, 35)),
        'foliage':    ((52, 95, 50), (86, 137, 74), (147, 181, 96), (29, 56, 25)),
        'water':      ((24, 94, 156), (68, 152, 205), (164, 223, 244), (16, 51, 108)),
        'lava':       ((114, 22, 10), (201, 64, 22), (249, 165, 59), (52, 5, 4)),
        'stone':      ((98, 99, 105), (136, 137, 143), (182, 177, 166), (61, 62, 67)),
        'brick':      ((130, 70, 55), (163, 92, 72), (206, 156, 124), (89, 43, 36)),
        'wood':       ((101, 65, 33), (140, 96, 55), (181, 137, 90), (64, 39, 20)),
        'metal':      ((88, 106, 121), (136, 155, 171), (191, 209, 220), (56, 67, 77)),
        'sand':       ((187, 165, 109), (220, 198, 138), (244, 229, 186), (128, 106, 66)),
        'snow':       ((191, 210, 225), (227, 237, 245), (251, 253, 255), (137, 155, 175)),
        'sky':        ((78, 135, 214), (128, 180, 233), (199, 227, 250), (52, 91, 176)),
        'cloud':      ((148, 184, 213), (201, 224, 238), (252, 253, 255), (105, 138, 165)),
        'fabric':     ((105, 73, 128), (145, 111, 172), (204, 176, 228), (71, 43, 92)),
        'sign':       ((132, 97, 58), (190, 158, 97), (241, 227, 183), (70, 45, 22)),
        'eye':        ((242, 240, 234), (255, 255, 255), (74, 115, 166), (11, 17, 24)),
        'mouth':      ((226, 128, 136), (250, 192, 196), (255, 230, 235), (92, 18, 27)),
        'skin':       ((191, 164, 127), (222, 194, 158), (241, 221, 190), (124, 90, 57)),
        'shell':      ((61, 132, 73), (117, 174, 90), (213, 228, 132), (39, 76, 37)),
        'coin':       ((178, 129, 24), (220, 172, 48), (255, 226, 118), (106, 72, 12)),
        'bobomb_body': ((18, 22, 29), (55, 61, 72), (145, 160, 176), (7, 9, 12)),
        'scales':     ((57, 131, 144), (95, 168, 173), (162, 210, 194), (30, 76, 85)),
        'fur':        ((122, 91, 61), (164, 129, 88), (219, 191, 143), (81, 55, 34)),
        'feather':    ((93, 127, 170), (133, 166, 201), (238, 239, 232), (53, 70, 101)),
        'beak':       ((209, 149, 52), (242, 189, 74), (255, 224, 124), (120, 72, 20)),
        'ivory':      ((204, 191, 160), (225, 216, 189), (245, 239, 220), (122, 103, 74)),
        'flower':     ((179, 95, 151), (237, 171, 210), (255, 236, 98), (99, 42, 88)),
        'jewel':      ((56, 124, 191), (89, 175, 230), (212, 244, 255), (17, 65, 110)),
        'pages':      ((219, 208, 177), (239, 230, 206), (250, 246, 232), (134, 110, 70)),
        'book_cover': ((102, 34, 39), (149, 65, 71), (207, 130, 102), (62, 18, 24)),
        'piano_keys': ((21, 23, 29), (57, 62, 76), (248, 248, 245), (9, 10, 12)),
        'egg':        ((229, 232, 220), (243, 246, 237), (124, 199, 122), (103, 122, 95)),
        'lens':       ((53, 73, 104), (75, 118, 175), (183, 230, 255), (10, 18, 31)),
        'emblem':     ((168, 124, 42), (216, 180, 82), (254, 235, 169), (89, 58, 13)),
        'ghost':      ((213, 223, 236), (240, 246, 252), (255, 255, 255), (91, 109, 135)),
        'smoke':      ((110, 114, 125), (164, 168, 179), (216, 219, 228), (71, 74, 84)),
        'sparkle':    ((201, 213, 233), (244, 248, 254), (255, 247, 168), (110, 118, 144)),
        'generic':    ((96, 108, 120), (139, 153, 172), (195, 209, 222), (59, 68, 80)),
    }
    colors = list(palettes.get(subject, palettes['generic']))

    if family in {'mario', 'mario_cap'} and subject == 'fabric':
        colors = [(160, 28, 36), (201, 55, 65), (247, 171, 103), (79, 18, 24)]
    elif family == 'peach' and subject == 'fabric':
        colors = [(204, 105, 157), (230, 150, 194), (255, 219, 232), (122, 58, 92)]
    elif family in {'penguin'} and subject == 'feather':
        colors = [(61, 87, 132), (99, 132, 171), (240, 243, 246), (28, 39, 64)]
    elif family in {'boo', 'boo_castle'}:
        colors = [(213, 223, 236), (240, 246, 252), (255, 255, 255), (91, 109, 135)]
    elif family in {'chain_chomp', 'bomb', 'bobomb', 'king_bobomb'} and subject in {'metal', 'generic', 'bobomb_body'}:
        colors = [(34, 38, 44), (76, 81, 90), (189, 195, 204), (13, 14, 18)]
    elif motif == 'spooky':
        colors = [(87, 71, 113), (122, 98, 152), (170, 144, 198), (55, 42, 72)]
    return tuple(_jitter(c, 8, rng) for c in colors)


# ---------------------------------
# Generic drawing helpers
# ---------------------------------


def _vertical_gradient(draw, w, h, top, bottom):
    for y in range(h):
        t = y / max(h - 1, 1)
        draw.line((0, y, w, y), fill=_mix(top, bottom, t))


def _horizontal_gradient(draw, w, h, left, right):
    for x in range(w):
        t = x / max(w - 1, 1)
        draw.line((x, 0, x, h), fill=_mix(left, right, t))


# ---------------------------------
# Surface/material renderers
# ---------------------------------


def _draw_grass(draw, w, h, colors, rng, motif='generic'):
    _vertical_gradient(draw, w, h, colors[2], colors[0])
    _soft_noise_points(draw, w, h, colors, rng, density=0.06)
    tufts = max(14, w * h // 34)
    for _ in range(tufts):
        x = rng.randint(0, w)
        base_y = rng.randint(h // 3, h)
        length = rng.randint(max(2, h // 10), max(4, h // 3))
        bend = rng.randint(-max(1, w // 12), max(1, w // 12) + 1)
        draw.line((x, base_y, x + bend, base_y - length), fill=_jitter(colors[1], 12, rng), width=1)
        if rng.rand() > 0.72:
            draw.line((x, base_y, x - bend, max(0, base_y - length + 1)), fill=_jitter(colors[0], 8, rng), width=1)
    if motif in {'wildflower_grass', 'battlefield_grass'}:
        draw.arc((0, h // 2, w - 1, h + h // 3), 180, 360, fill=_jitter(colors[3], 8, rng), width=1)
        draw.arc((-w // 4, h // 2 - 1, w * 3 // 4, h + h // 4), 180, 360, fill=_jitter(colors[0], 10, rng), width=1)
    flower_count = max(1, w * h // (250 if motif == 'wildflower_grass' else 420))
    for _ in range(flower_count):
        cx, cy = rng.randint(0, w), rng.randint(h // 3, h)
        petal = _mix(colors[2], (250, 240, 210), rng.rand() * 0.55)
        if motif == 'battlefield_grass' and rng.rand() > 0.4:
            petal = _mix((240, 230, 160), (255, 255, 255), rng.rand() * 0.3)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            draw.ellipse((cx + dx - 1, cy + dy - 1, cx + dx + 1, cy + dy + 1), fill=petal)
        draw.ellipse((cx - 1, cy - 1, cx + 1, cy + 1), fill=(235, 210, 70))

def _draw_foliage(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=colors[3])
    for _ in range(max(10, w * h // 64)):
        cx, cy = rng.randint(0, w), rng.randint(0, h)
        rw = rng.randint(max(2, w // 12), max(3, w // 4))
        rh = rng.randint(max(2, h // 12), max(3, h // 4))
        fill = _mix(colors[0], colors[2], rng.rand())
        draw.ellipse((cx - rw, cy - rh, cx + rw, cy + rh), fill=fill)
    for _ in range(max(6, w * h // 180)):
        x0, y0 = rng.randint(0, w), rng.randint(0, h)
        x1, y1 = x0 + rng.randint(-w // 6, w // 6 + 1), y0 + rng.randint(-h // 6, h // 6 + 1)
        draw.line((x0, y0, x1, y1), fill=_jitter(colors[3], 5, rng), width=1)


def _draw_water(draw, w, h, colors, rng, motif='generic'):
    _vertical_gradient(draw, w, h, colors[2], colors[3])
    draw.rectangle((0, 0, w - 1, h - 1), outline=_mix(colors[2], colors[1], 0.35), width=1)
    band_count = max(3, h // 6)
    for band in range(band_count):
        y = int((band + 0.5) * h / band_count)
        phase = rng.rand() * math.pi * 2
        amp = max(1, h // (10 if motif == 'wave' else 14))
        pts = []
        for x in range(0, w + 2, 2):
            freq = 3 if motif in {'sea_water', 'wave'} else 2
            pts.append((x, y + int(math.sin((x / max(w, 1)) * math.pi * freq + phase) * amp)))
        draw.line(pts, fill=_jitter(colors[1], 8, rng), width=1)
    for _ in range(max(2, w * h // 250)):
        x, y = rng.randint(0, w), rng.randint(0, h)
        rw, rh = rng.randint(1, max(2, w // 10)), rng.randint(1, max(2, h // 14))
        draw.arc((x - rw, y - rh, x + rw, y + rh), 190, 350, fill=colors[2], width=1)
    if motif in {'sea_water', 'wave'}:
        for _ in range(max(2, w * h // 320)):
            x0 = rng.randint(0, w)
            y0 = rng.randint(h // 4, h)
            x1 = min(w - 1, x0 + rng.randint(max(2, w // 8), max(3, w // 4)))
            y1 = min(h - 1, y0 + rng.randint(-1, 2))
            draw.arc((x0, y0 - max(1, h // 12), x1, y1 + max(1, h // 14)), 200, 340, fill=(240, 250, 255), width=1)
        if motif == 'wave':
            for _ in range(max(1, w // 12)):
                x = rng.randint(0, w)
                draw.line((x, h // 2, min(w - 1, x + 2), min(h - 1, h // 2 + 2)), fill=(230, 245, 255), width=1)

def _draw_lava(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=colors[0])
    for _ in range(max(8, w * h // 120)):
        x, y = rng.randint(0, w), rng.randint(0, h)
        rw, rh = rng.randint(max(2, w // 12), max(3, w // 5)), rng.randint(max(2, h // 12), max(3, h // 5))
        draw.ellipse((x - rw, y - rh, x + rw, y + rh), fill=_mix(colors[1], colors[2], rng.rand()))
    for _ in range(max(6, w * h // 180)):
        pts = []
        x, y = rng.randint(0, w), rng.randint(0, h)
        for _k in range(4):
            pts.append((x, y))
            x += rng.randint(-max(1, w // 7), max(1, w // 7) + 1)
            y += rng.randint(-max(1, h // 7), max(1, h // 7) + 1)
        draw.line(pts, fill=colors[3], width=1)


def _draw_stone(draw, w, h, colors, rng, bricky=False):
    mortar = _mix(colors[1], (220, 214, 205), 0.4)
    draw.rectangle((0, 0, w, h), fill=mortar)
    cell_h = max(4, h // (5 if bricky else 4))
    cell_w = max(5, w // (4 if bricky else 3))
    row = 0
    for y in range(0, h + cell_h, cell_h):
        offset = cell_w // 2 if bricky and row % 2 else 0
        for x in range(-offset, w + cell_w, cell_w):
            x1 = x + cell_w + rng.randint(-1, 2)
            y1 = y + cell_h + rng.randint(-1, 2)
            fill = _mix(colors[0], colors[2], rng.rand())
            draw.rounded_rectangle((x + 1, y + 1, x1 - 2, y1 - 2), radius=1, fill=fill, outline=colors[3])
            if rng.rand() > 0.65:
                cx = x + cell_w // 2
                draw.line((cx, y + 2, cx + rng.randint(-2, 2), y1 - 3), fill=_jitter(colors[3], 4, rng), width=1)
        row += 1


def _draw_wood(draw, w, h, colors, rng, doorish=False):
    _vertical_gradient(draw, w, h, colors[2], colors[0])
    draw.rectangle((0, 0, w - 1, h - 1), outline=colors[3], width=1)
    if doorish:
        margin = max(2, min(w, h) // 10)
        panels = 2 if h > w else 1
        for p in range(panels):
            y0 = margin + p * (h - 2 * margin) // panels
            y1 = margin + (p + 1) * (h - 2 * margin) // panels - 1
            draw.rectangle((margin, y0, w - margin, y1), outline=_jitter(colors[3], 8, rng), width=1)
    plank_h = max(4, h // 4)
    for y in range(0, h, plank_h):
        for k in range(2):
            yy = y + plank_h * (k + 1) // 3
            phase = rng.rand() * math.pi * 2
            pts = []
            for x in range(0, w + 2, 2):
                pts.append((x, yy + int(math.sin(phase + x / max(1, w) * math.pi * 2) * max(1, plank_h // 7))))
            draw.line(pts, fill=_jitter(colors[1], 10, rng), width=1)
        for _ in range(max(1, w // 24)):
            cx, cy = rng.randint(0, w), rng.randint(y, min(h, y + plank_h))
            rx, ry = max(1, w // 12), max(1, plank_h // 5)
            draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline=colors[3], width=1)
    if doorish:
        r = max(1, min(w, h) // 16)
        x = w - max(3, w // 6)
        draw.ellipse((x - r, h // 2 - r, x + r, h // 2 + r), fill=_mix(colors[2], (220, 190, 90), 0.45), outline=colors[3])


def _draw_metal(draw, w, h, colors, rng, panelish=False):
    _horizontal_gradient(draw, w, h, colors[2], colors[0])
    for x in range(0, w, max(2, w // 10)):
        draw.line((x, 0, x, h), fill=_jitter(colors[1], 6, rng), width=1)
    if panelish:
        margin = max(2, min(w, h) // 10)
        draw.rectangle((margin, margin, w - margin, h - margin), outline=colors[3], width=1)
    step = max(4, min(w, h) // 3)
    for y in range(step // 2, h, step):
        for x in range(step // 2, w, step):
            r = max(1, min(w, h) // 16)
            draw.ellipse((x - r, y - r, x + r, y + r), fill=colors[3], outline=colors[2])


def _draw_sand(draw, w, h, colors, rng):
    _vertical_gradient(draw, w, h, colors[2], colors[0])
    _soft_noise_points(draw, w, h, colors, rng, density=0.08)
    for band in range(max(4, h // 5)):
        y = int((band + 0.5) * h / max(4, h // 5))
        phase = rng.rand() * math.pi * 2
        pts = []
        for x in range(0, w + 2, 2):
            pts.append((x, y + int(math.sin(phase + x / max(1, w) * math.pi * 2) * max(1, h // 18))))
        draw.line(pts, fill=_jitter(colors[1], 7, rng), width=1)


def _draw_snow(draw, w, h, colors, rng):
    _vertical_gradient(draw, w, h, colors[1], colors[2])
    for _ in range(max(10, w * h // 90)):
        x, y = rng.randint(0, w), rng.randint(0, h)
        draw.point((x, y), fill=colors[2])
        if rng.rand() > 0.7:
            draw.line((x - 1, y, x + 1, y), fill=colors[2], width=1)
            draw.line((x, y - 1, x, y + 1), fill=colors[2], width=1)
    for band in range(max(2, h // 10)):
        y = int((band + 0.5) * h / max(2, h // 10))
        draw.arc((0, y - h // 8, w, y + h // 8), 0, 180, fill=_mix(colors[0], colors[2], 0.3), width=1)


def _draw_sky(draw, w, h, colors, rng, cloudy=False):
    _vertical_gradient(draw, w, h, colors[2], colors[0])
    count = max(3, (w * h) // 280)
    for _ in range(count):
        x = rng.randint(0, w)
        y = rng.randint(0, max(1, h * 2 // 3))
        rw = rng.randint(max(2, w // 10), max(3, w // 5))
        rh = rng.randint(max(1, h // 12), max(2, h // 8))
        alpha = 215 if cloudy else 165
        fill = (255, 255, 255, alpha)
        for dx in ([-rw // 2, 0, rw // 2] if cloudy else [0]):
            draw.ellipse((x + dx - rw, y - rh, x + dx + rw, y + rh), fill=fill)


def _draw_fabric(draw, w, h, colors, rng, royal=False):
    draw.rectangle((0, 0, w, h), fill=colors[1])
    step = max(3, min(w, h) // 6)
    for i in range(-h, w, step):
        draw.line((i, 0, i + h, h), fill=_jitter(colors[2], 6, rng), width=1)
    for i in range(0, w + h, step):
        draw.line((i, 0, i - h, h), fill=_jitter(colors[0], 6, rng), width=1)
    draw.rectangle((0, 0, w - 1, h - 1), outline=colors[3], width=1)
    if royal:
        margin = max(2, min(w, h) // 10)
        draw.rectangle((margin, margin, w - margin, h - margin), outline=_mix(colors[2], (255, 220, 120), 0.35), width=1)


def _draw_sign(draw, w, h, colors, rng):
    _draw_wood(draw, w, h, colors, rng, doorish=True)
    pad = max(2, min(w, h) // 8)
    draw.rectangle((pad, pad, w - pad, h - pad), fill=_mix(colors[2], (240, 230, 190), 0.5), outline=colors[3], width=1)
    line_count = max(2, (h - 2 * pad) // max(3, h // 7))
    for i in range(line_count):
        y = pad + (i + 1) * (h - 2 * pad) // (line_count + 1)
        x0 = pad * 2
        x1 = w - pad * 2 - rng.randint(0, max(1, w // 8))
        draw.line((x0, y, x1, y), fill=_jitter(colors[3], 10, rng), width=1)


# ---------------------------------
# Character-part renderers
# ---------------------------------


def _draw_eye(draw, w, h, colors, rng, blink=False, angry=False, style='generic', low=''):
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
    margin_x = max(1, w // 12)
    margin_y = max(1, h // 5)
    if blink:
        y = h // 2 if not angry else h // 2 - 1
        line_color = colors[3] if style != 'mario' else (63, 37, 28)
        draw.line((margin_x, y, w - margin_x, y), fill=line_color, width=max(1, h // 8))
        if style == 'mario':
            draw.arc((margin_x, max(0, y - h // 5), w - margin_x, min(h - 1, y + h // 8)), 200, 340, fill=(63, 37, 28), width=1)
        return
    sclera = colors[1]
    outline = colors[3]
    iris = colors[2]
    if style == 'mario':
        outline = (56, 35, 28)
        iris = (62, 134, 215)
    draw.ellipse((margin_x, margin_y, w - margin_x, h - margin_y), fill=sclera, outline=outline)
    dx = 0
    dy = 0
    if 'left' in low:
        dx = -max(1, w // 10)
    elif 'right' in low:
        dx = max(1, w // 10)
    if 'up' in low:
        dy = -max(1, h // 10)
    elif 'down' in low:
        dy = max(1, h // 10)
    if dx == 0 and dy == 0 and style != 'mario':
        dx = rng.randint(-max(1, w // 14), max(1, w // 14) + 1)
        dy = rng.randint(-max(1, h // 14), max(1, h // 14) + 1)
    cx = w // 2 + dx
    cy = h // 2 + dy
    iris_r = max(1, min(w, h) // 5)
    pupil_r = max(1, min(w, h) // 9)
    draw.ellipse((cx - iris_r, cy - iris_r, cx + iris_r, cy + iris_r), fill=iris)
    draw.ellipse((cx - pupil_r, cy - pupil_r, cx + pupil_r, cy + pupil_r), fill=(0, 0, 0))
    draw.ellipse((cx - 1, cy - 1, cx + 1, cy + 1), fill=(255, 255, 255))
    if angry:
        draw.line((margin_x, margin_y + 1, w - margin_x, margin_y - 1), fill=outline, width=1)
    if style == 'mario':
        lid = (244, 203, 180, 180)
        draw.arc((margin_x, margin_y - 1, w - margin_x, h // 2), 180, 360, fill=lid, width=1)

def _draw_mouth(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
    pad = max(1, min(w, h) // 7)
    draw.arc((pad, pad, w - pad, h - pad), 10, 170, fill=colors[3], width=max(1, h // 10))
    draw.ellipse((pad, h // 2, w - pad, h - pad), fill=_mix(colors[0], colors[1], 0.35), outline=colors[3])


def _draw_ghost(draw, w, h, colors, rng, face=False):
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
    pad = max(1, min(w, h) // 8)
    body_h = h - pad * 2
    draw.ellipse((pad, pad, w - pad, pad + body_h), fill=(colors[2][0], colors[2][1], colors[2][2], 235), outline=colors[3])
    for i in range(4):
        x0 = pad + i * (w - 2 * pad) // 4
        draw.ellipse((x0, h - pad * 2, x0 + (w - 2 * pad) // 4, h), fill=(colors[2][0], colors[2][1], colors[2][2], 235), outline=(0, 0, 0, 0))
    if face:
        eye_w = max(1, w // 10)
        draw.ellipse((w // 3 - eye_w, h // 3, w // 3 + eye_w, h // 2), fill=colors[3])
        draw.ellipse((2 * w // 3 - eye_w, h // 3, 2 * w // 3 + eye_w, h // 2), fill=colors[3])
        draw.arc((w // 3, h // 2, 2 * w // 3, h * 3 // 4), 15, 165, fill=colors[3], width=1)


def _draw_shell(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=colors[0])
    cx, cy = w // 2, h // 2
    for r in range(max(3, min(w, h) // 8), max(4, min(w, h) // 2), max(2, min(w, h) // 10)):
        draw.arc((cx - r, cy - r, cx + r, cy + r), 20, 160, fill=_mix(colors[2], colors[1], 0.2), width=1)
    for x in range(0, w, max(3, w // 5)):
        draw.line((x, h // 2, w // 2, 0), fill=_jitter(colors[3], 6, rng), width=1)
    for x in range(0, w, max(3, w // 5)):
        draw.line((x, h // 2, w // 2, h), fill=_jitter(colors[3], 6, rng), width=1)


def _draw_scales(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=colors[0])
    rad = max(2, min(w, h) // 6)
    step_x = max(3, rad)
    step_y = max(3, rad)
    row = 0
    for y in range(0, h + step_y, step_y):
        offset = step_x // 2 if row % 2 else 0
        for x in range(-offset, w + step_x, step_x):
            fill = _mix(colors[1], colors[2], rng.rand() * 0.5)
            draw.pieslice((x - rad, y - rad, x + rad, y + rad), 180, 360, fill=fill, outline=colors[3])
        row += 1


def _draw_fur(draw, w, h, colors, rng):
    _vertical_gradient(draw, w, h, colors[2], colors[0])
    for _ in range(max(12, w * h // 35)):
        x, y = rng.randint(0, w), rng.randint(0, h)
        length = rng.randint(max(2, h // 12), max(3, h // 4))
        ang = rng.uniform(-0.8, 0.8)
        x2 = x + int(math.sin(ang) * length)
        y2 = y - int(math.cos(ang) * length)
        draw.line((x, y, x2, y2), fill=_jitter(colors[1], 10, rng), width=1)


def _draw_feather(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
    draw.line((w // 2, h, w // 2, 0), fill=colors[3], width=1)
    count = max(5, h // 3)
    for i in range(count):
        y = h - (i + 1) * h // (count + 1)
        length = max(2, w // 2 - i * w // (count * 3 + 1))
        fill = _mix(colors[0], colors[2], i / max(count, 1))
        draw.line((w // 2, y, w // 2 + length, max(0, y - 1)), fill=fill, width=1)
        draw.line((w // 2, y, w // 2 - length, max(0, y - 1)), fill=fill, width=1)


def _draw_beak(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
    pts = [(0, h // 2), (w - 1, 1), (w - 1, h - 1)]
    draw.polygon(pts, fill=colors[1], outline=colors[3])
    draw.line((0, h // 2, w - 1, h // 2), fill=_jitter(colors[3], 5, rng), width=1)


def _draw_ivory(draw, w, h, colors, rng):
    _vertical_gradient(draw, w, h, colors[2], colors[0])
    draw.arc((0, 0, w * 2, h * 2), 180, 270, fill=colors[3], width=1)


def _draw_leaf(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
    pad = max(1, min(w, h) // 8)
    draw.ellipse((pad, pad, w - pad, h - pad), fill=colors[1], outline=colors[3])
    draw.line((w // 2, pad, w // 2, h - pad), fill=colors[3], width=1)
    for t in np.linspace(0.25, 0.75, 4):
        y = int(pad + (h - 2 * pad) * t)
        dx = max(1, w // 5)
        draw.line((w // 2, y, w // 2 - dx, y - max(1, h // 10)), fill=colors[3], width=1)
        draw.line((w // 2, y, w // 2 + dx, y - max(1, h // 10)), fill=colors[3], width=1)


def _draw_flower(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
    cx, cy = w // 2, h // 2
    r = max(2, min(w, h) // 5)
    for ang in np.linspace(0, 2 * math.pi, 6, endpoint=False):
        px = cx + int(math.cos(ang) * r * 1.6)
        py = cy + int(math.sin(ang) * r * 1.6)
        draw.ellipse((px - r, py - r, px + r, py + r), fill=_mix(colors[1], colors[2], 0.4), outline=colors[3])
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=colors[2], outline=colors[3])


def _draw_jewel(draw, w, h, colors, rng):
    _vertical_gradient(draw, w, h, colors[2], colors[0])
    pts = [(w // 2, 1), (w - 2, h // 3), (w * 3 // 4, h - 2), (w // 4, h - 2), (1, h // 3)]
    draw.polygon(pts, fill=_mix(colors[1], colors[2], 0.4), outline=colors[3])
    draw.line((w // 2, 1, w // 4, h - 2), fill=colors[2], width=1)
    draw.line((w // 2, 1, w * 3 // 4, h - 2), fill=colors[2], width=1)


def _draw_pages(draw, w, h, colors, rng):
    _vertical_gradient(draw, w, h, colors[2], colors[1])
    draw.rectangle((0, 0, w - 1, h - 1), outline=colors[3], width=1)
    for y in range(max(2, h // 8), h, max(2, h // 6)):
        draw.line((max(1, w // 6), y, w - max(2, w // 6), y), fill=_mix(colors[0], colors[3], 0.35), width=1)
    draw.line((max(1, w // 5), 0, max(1, w // 5), h), fill=_mix(colors[0], colors[3], 0.4), width=1)


def _draw_book_cover(draw, w, h, colors, rng):
    _draw_wood(draw, w, h, colors, rng, doorish=False)
    margin = max(2, min(w, h) // 8)
    draw.rectangle((margin, margin, w - margin, h - margin), outline=_mix(colors[2], (255, 220, 120), 0.3), width=1)
    draw.line((margin * 2, 0, margin * 2, h), fill=_jitter(colors[3], 6, rng), width=1)


def _draw_piano_keys(draw, w, h, colors, rng):
    white = colors[2]
    black = colors[3]
    key_w = max(3, w // 7)
    for x in range(0, w + key_w, key_w):
        draw.rectangle((x, 0, x + key_w - 1, h - 1), fill=white, outline=black)
    for idx in [0, 1, 3, 4, 5]:
        x = int((idx + 0.7) * key_w)
        bw = max(1, key_w // 2)
        draw.rectangle((x, 0, x + bw, h * 2 // 3), fill=black, outline=black)


def _draw_egg(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
    pad = max(1, min(w, h) // 10)
    draw.ellipse((pad, pad, w - pad, h - pad), fill=colors[1], outline=colors[3])
    for _ in range(max(3, min(w, h) // 5)):
        cx, cy = rng.randint(pad * 2, max(pad * 2 + 1, w - pad * 2)), rng.randint(pad * 2, max(pad * 2 + 1, h - pad * 2))
        r = max(1, min(w, h) // 10)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=_mix(colors[3], colors[2], 0.35))


def _draw_lens(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
    cx, cy = w // 2, h // 2
    r = max(2, min(w, h) // 3)
    draw.ellipse((cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2), fill=_mix(colors[3], (25, 25, 25), 0.5), outline=colors[3])
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=_mix(colors[0], colors[2], 0.3), outline=colors[2])
    draw.arc((cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1), 210, 320, fill=(255, 255, 255), width=1)


def _draw_emblem(draw, w, h, colors, rng, kind='star'):
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
    cx, cy = w // 2, h // 2
    if kind == 'lock':
        bw = max(4, w // 2)
        bh = max(4, h // 3)
        draw.rounded_rectangle((cx - bw // 2, cy, cx + bw // 2, cy + bh), radius=1, fill=colors[1], outline=colors[3])
        draw.arc((cx - bw // 3, cy - bh // 2, cx + bw // 3, cy + bh // 3), 180, 360, fill=colors[3], width=1)
    else:
        r1 = max(3, min(w, h) // 4)
        r2 = max(1, r1 // 2)
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            r = r1 if i % 2 == 0 else r2
            pts.append((cx + int(math.cos(ang) * r), cy + int(math.sin(ang) * r)))
        draw.polygon(pts, fill=_mix(colors[2], (255, 220, 100), 0.3), outline=colors[3])


def _draw_coin(draw, w, h, colors, rng, low=''):
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
    sideish = ('side' in low)
    tilt_left = ('tilt_left' in low)
    tilt_right = ('tilt_right' in low)
    cx, cy = w // 2, h // 2
    rx = max(2, w // 3)
    ry = max(2, h // 3)
    if sideish:
        rx = max(1, w // 7)
    elif tilt_left or tilt_right:
        rx = max(2, w // 4)
        cy += -1 if tilt_left else 1
    rim_fill = _mix(colors[1], colors[2], 0.45)
    inner_fill = _mix(colors[0], colors[2], 0.38)
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=rim_fill, outline=colors[3])
    inset_x = max(1, rx // 4)
    inset_y = max(1, ry // 4)
    draw.ellipse((cx - rx + inset_x, cy - ry + inset_y, cx + rx - inset_x, cy + ry - inset_y), fill=inner_fill, outline=_mix(colors[3], colors[0], 0.5))
    draw.arc((cx - rx + 1, cy - ry + 1, cx + rx - 1, cy + ry - 1), 205, 330, fill=(255, 250, 210, 220), width=1)
    if not sideish:
        bar_h = max(1, ry // 2)
        draw.rectangle((cx - max(1, rx // 7), cy - bar_h, cx + max(1, rx // 7), cy + bar_h), fill=_mix(colors[2], colors[3], 0.25))
        draw.arc((cx - rx // 2, cy - ry // 2, cx + rx // 2, cy + ry // 2), 25, 155, fill=_mix(colors[2], (255, 255, 255), 0.2), width=1)


def _draw_bobomb_body(draw, w, h, colors, rng, low=''):
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
    buddy = 'buddy' in low
    regal = 'king_' in low or 'crown' in low
    base_outer = (54, 97, 179) if buddy else colors[0]
    base_inner = (117, 163, 232) if buddy else colors[1]
    highlight = (210, 228, 255) if buddy else colors[2]
    edge = (20, 36, 75) if buddy else colors[3]
    cx, cy = w // 2, h // 2
    rx = max(3, w // 2 - 2)
    ry = max(3, h // 2 - 2)
    for t in np.linspace(1.0, 0.35, 7):
        fill = _mix(base_outer, base_inner, 1 - t)
        dx = int((1 - t) * rx * 0.4)
        dy = int((1 - t) * ry * 0.4)
        draw.ellipse((cx - int(rx * t) + dx, cy - int(ry * t) + dy, cx + int(rx * t) + dx, cy + int(ry * t) + dy), fill=fill)
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline=edge, width=1)
    draw.ellipse((cx - rx // 2, cy - ry // 2, cx - rx // 6, cy - ry // 5), fill=(255, 255, 255, 80 if buddy else 55))
    cap_w = max(2, w // 6)
    cap_h = max(2, h // 6)
    draw.rectangle((cx - cap_w // 2, 1, cx + cap_w // 2, cap_h), fill=(166, 130, 58) if regal else (126, 109, 88), outline=edge)
    if regal:
        draw.arc((cx - rx // 2, 0, cx + rx // 2, h // 3), 180, 360, fill=(237, 198, 85), width=1)


# ---------------------------------
# Sprite / overlay renderers
# ---------------------------------


def _draw_bubble_sprite(draw, w, h, colors, rng):
    cx, cy = w // 2, h // 2
    r = max(2, min(w, h) // 3)
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(220, 245, 255, 220), width=1, fill=(180, 230, 255, 50))
    draw.arc((cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1), 210, 320, fill=(255, 255, 255, 200), width=1)
    draw.ellipse((cx - r // 2, cy - r // 2, cx - r // 4, cy - r // 4), fill=(255, 255, 255, 160))


def _draw_ring_sprite(draw, w, h, colors, rng):
    cx, cy = w // 2, h // 2
    r = max(3, min(w, h) // 3)
    thickness = max(1, min(w, h) // 10)
    for off in range(thickness):
        draw.ellipse((cx - r + off, cy - r + off, cx + r - off, cy + r - off), outline=_mix(colors[2], (255, 255, 255), 0.3), width=1)


def _draw_smoke_sprite(draw, w, h, colors, rng):
    for _ in range(max(5, w * h // 256)):
        cx, cy = rng.randint(w // 4, max(w // 4 + 1, w * 3 // 4)), rng.randint(h // 4, max(h // 4 + 1, h * 3 // 4))
        rw = rng.randint(max(2, w // 8), max(3, w // 4))
        rh = rng.randint(max(2, h // 8), max(3, h // 4))
        fill = (colors[1][0], colors[1][1], colors[1][2], 80 + rng.randint(0, 60))
        draw.ellipse((cx - rw, cy - rh, cx + rw, cy + rh), fill=fill)


def _draw_flame_sprite(draw, w, h, colors, rng):
    cx, cy = w // 2, h // 2
    for scale, color in [(1.0, (colors[3][0], colors[3][1], colors[3][2], 210)), (0.72, (colors[1][0], colors[1][1], colors[1][2], 220)), (0.42, (colors[2][0], colors[2][1], colors[2][2], 230))]:
        pts = [
            (cx, int(cy - h * 0.42 * scale)),
            (int(cx + w * 0.22 * scale), int(cy - h * 0.08 * scale)),
            (int(cx + w * 0.14 * scale), int(cy + h * 0.28 * scale)),
            (cx, int(cy + h * 0.38 * scale)),
            (int(cx - w * 0.14 * scale), int(cy + h * 0.28 * scale)),
            (int(cx - w * 0.22 * scale), int(cy - h * 0.08 * scale)),
        ]
        draw.polygon(pts, fill=color)


def _draw_sparkle_sprite(draw, w, h, colors, rng):
    cx, cy = w // 2, h // 2
    rad = max(2, min(w, h) // 3)
    for ang in [0, math.pi / 4, math.pi / 2, 3 * math.pi / 4]:
        dx = int(math.cos(ang) * rad)
        dy = int(math.sin(ang) * rad)
        draw.line((cx - dx, cy - dy, cx + dx, cy + dy), fill=(255, 248, 180, 230), width=1)
    draw.ellipse((cx - 1, cy - 1, cx + 1, cy + 1), fill=(255, 255, 255, 255))


def _draw_splash_sprite(draw, w, h, colors, rng):
    cx, cy = w // 2, h // 2
    for ang in np.linspace(0, math.pi, 7):
        dx = int(math.cos(ang) * max(2, w // 3))
        dy = int(math.sin(ang) * max(2, h // 3))
        draw.line((cx, cy, cx + dx, cy - dy), fill=(220, 245, 255, 180), width=1)
    draw.arc((cx - w // 4, cy - h // 6, cx + w // 4, cy + h // 3), 0, 180, fill=(190, 230, 255, 180), width=1)


def _draw_tree_sprite(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
    trunk_w = max(2, w // 6)
    draw.rectangle((w // 2 - trunk_w // 2, h * 2 // 3, w // 2 + trunk_w // 2, h - 1), fill=(114, 78, 46, 255))
    for k in range(3):
        top = h // 8 + k * h // 6
        spread = max(3, w // 3 - k)
        draw.polygon([(w // 2, top), (w // 2 - spread, top + h // 4), (w // 2 + spread, top + h // 4)], fill=(colors[1][0], colors[1][1], colors[1][2], 240), outline=colors[3])


# ---------------------------------
# Dispatcher
# ---------------------------------



def _portrait_tile_index(low: str):
    stem = low.rsplit('/', 1)[-1].split('.', 1)[0]
    try:
        return int(stem)
    except Exception:
        return 0


def _ellipse_xy(cx, cy, rx, ry):
    return (int(cx - rx), int(cy - ry), int(cx + rx), int(cy + ry))


def _draw_round_bomb(draw, cx, cy, scale, body, fuse, shoe, eye='dot'):
    draw.ellipse(_ellipse_xy(cx, cy, 11 * scale, 11 * scale), fill=body, outline=(24, 24, 24), width=max(1, int(scale)))
    # shoes
    draw.ellipse(_ellipse_xy(cx - 6 * scale, cy + 10 * scale, 5 * scale, 3 * scale), fill=shoe, outline=(90, 70, 18))
    draw.ellipse(_ellipse_xy(cx + 6 * scale, cy + 10 * scale, 5 * scale, 3 * scale), fill=shoe, outline=(90, 70, 18))
    # wind-up key / fuse
    draw.line((int(cx + 10 * scale), int(cy - 6 * scale), int(cx + 15 * scale), int(cy - 13 * scale)), fill=fuse, width=max(1, int(scale)))
    draw.ellipse(_ellipse_xy(cx + 16 * scale, cy - 14 * scale, 2 * scale, 2 * scale), fill=(255, 212, 82), outline=(140, 90, 12))
    # eyes
    if eye == 'friendly':
        draw.ellipse(_ellipse_xy(cx - 4 * scale, cy - 1 * scale, 1.4 * scale, 2.2 * scale), fill=(255, 255, 255))
        draw.ellipse(_ellipse_xy(cx + 1 * scale, cy - 1 * scale, 1.4 * scale, 2.2 * scale), fill=(255, 255, 255))
        draw.point((int(cx - 4 * scale), int(cy)), fill=(20, 20, 20))
        draw.point((int(cx + 1 * scale), int(cy)), fill=(20, 20, 20))
    else:
        draw.ellipse(_ellipse_xy(cx - 4 * scale, cy - 1 * scale, 1.3 * scale, 2.1 * scale), fill=(255, 255, 255))
        draw.ellipse(_ellipse_xy(cx + 1 * scale, cy - 1 * scale, 1.3 * scale, 2.1 * scale), fill=(255, 255, 255))
        draw.polygon([(int(cx - 5 * scale), int(cy - 3 * scale)), (int(cx - 2 * scale), int(cy)), (int(cx - 5 * scale), int(cy + 2 * scale))], fill=(20, 20, 20))
        draw.polygon([(int(cx + 3 * scale), int(cy - 3 * scale)), (int(cx), int(cy)), (int(cx + 3 * scale), int(cy + 2 * scale))], fill=(20, 20, 20))


def _render_bobomb_battlefield_portrait_rgba(fname: str, shape, rng):
    h, w = int(shape[0]), int(shape[1])
    tile = _portrait_tile_index(fname.lower())
    cols, rows = 3, 2
    scene = Image.new('RGBA', (w * cols, h * rows), (0, 0, 0, 0))
    draw = ImageDraw.Draw(scene)
    sw, sh = scene.size

    # Sky gradient
    for y in range(sh):
        t = y / max(1, sh - 1)
        if t < 0.58:
            color = _mix((108, 177, 241), (211, 239, 255), t / 0.58)
        else:
            color = _mix((211, 239, 255), (164, 210, 126), (t - 0.58) / 0.42)
        draw.line((0, y, sw, y), fill=color)

    # clouds
    for cx, cy, rx, ry in [
        (sw * 0.18, sh * 0.17, sw * 0.10, sh * 0.07),
        (sw * 0.65, sh * 0.14, sw * 0.12, sh * 0.08),
        (sw * 0.87, sh * 0.24, sw * 0.08, sh * 0.05),
    ]:
        for dx, dy, sx, sy in [(-0.35, 0, 0.7, 0.6), (0, -0.08, 0.8, 0.7), (0.35, 0, 0.65, 0.55)]:
            draw.ellipse(_ellipse_xy(cx + dx * rx, cy + dy * ry, rx * sx, ry * sy), fill=(255, 255, 255, 225))

    # distant mountains / floating island
    mountain = [(sw * 0.34, sh * 0.60), (sw * 0.52, sh * 0.18), (sw * 0.68, sh * 0.60)]
    draw.polygon(mountain, fill=(127, 172, 88), outline=(78, 113, 59))
    draw.polygon([(sw * 0.47, sh * 0.45), (sw * 0.52, sh * 0.29), (sw * 0.57, sh * 0.45)], fill=(170, 202, 116))
    # floating island
    island = [(sw * 0.73, sh * 0.31), (sw * 0.84, sh * 0.23), (sw * 0.94, sh * 0.30), (sw * 0.88, sh * 0.37), (sw * 0.76, sh * 0.36)]
    draw.polygon(island, fill=(133, 177, 94), outline=(74, 103, 54))
    draw.rectangle((int(sw * 0.81), int(sh * 0.18), int(sw * 0.82), int(sh * 0.28)), fill=(100, 70, 44))
    draw.ellipse(_ellipse_xy(sw * 0.815, sh * 0.14, sw * 0.035, sh * 0.05), fill=(79, 138, 67), outline=(48, 88, 40))

    # rolling hills
    hill_specs = [
        ((-sw * 0.05, sh * 0.50, sw * 0.40, sh * 1.02), (113, 176, 86)),
        ((sw * 0.20, sh * 0.47, sw * 0.78, sh * 1.05), (106, 170, 78)),
        ((sw * 0.58, sh * 0.50, sw * 1.08, sh * 1.04), (117, 181, 88)),
    ]
    for box, fill in hill_specs:
        draw.ellipse(tuple(int(v) for v in box), fill=fill, outline=(64, 111, 46))

    # path to mountain
    path = [
        (sw * 0.44, sh * 0.99), (sw * 0.57, sh * 0.99), (sw * 0.54, sh * 0.78),
        (sw * 0.60, sh * 0.66), (sw * 0.55, sh * 0.54), (sw * 0.53, sh * 0.40),
        (sw * 0.49, sh * 0.32), (sw * 0.44, sh * 0.42), (sw * 0.45, sh * 0.58),
        (sw * 0.39, sh * 0.69), (sw * 0.42, sh * 0.82),
    ]
    draw.polygon([(int(x), int(y)) for x, y in path], fill=(211, 181, 110), outline=(166, 135, 80))

    # ground details
    for x in range(0, sw, max(4, w // 6)):
        y0 = int(sh * 0.72 + rng.randint(-3, 4))
        y1 = int(sh * 0.96 + rng.randint(-2, 3))
        draw.line((x, y1, x + rng.randint(-3, 4), y0), fill=(88, 141, 60), width=1)
    for _ in range(max(18, sw * sh // 900)):
        cx = int(rng.randint(0, sw))
        cy = int(rng.randint(int(sh * 0.56), sh))
        petal = (250, 246, 235) if rng.rand() > 0.5 else (255, 224, 92)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            draw.ellipse((cx + dx - 1, cy + dy - 1, cx + dx + 1, cy + dy + 1), fill=petal)
        draw.ellipse((cx - 1, cy - 1, cx + 1, cy + 1), fill=(232, 180, 60))

    # fence and cannon
    fence_y = int(sh * 0.70)
    for fx in range(int(sw * 0.03), int(sw * 0.27), max(8, w // 3)):
        draw.rectangle((fx, fence_y, fx + 2, fence_y + 10), fill=(104, 76, 44))
    draw.line((int(sw * 0.03), fence_y + 2, int(sw * 0.26), fence_y + 2), fill=(126, 92, 53), width=2)
    draw.line((int(sw * 0.03), fence_y + 7, int(sw * 0.26), fence_y + 7), fill=(126, 92, 53), width=2)
    draw.ellipse(_ellipse_xy(sw * 0.83, sh * 0.74, sw * 0.055, sh * 0.06), fill=(52, 61, 70), outline=(18, 18, 20))
    draw.polygon([(int(sw * 0.79), int(sh * 0.73)), (int(sw * 0.92), int(sh * 0.67)), (int(sw * 0.90), int(sh * 0.76))], fill=(65, 74, 82), outline=(20, 20, 20))

    # bob-ombs
    _draw_round_bomb(draw, sw * 0.24, sh * 0.77, min(w, h) / 32 * 0.9, (210, 75, 82), (255, 228, 90), (255, 192, 68), eye='friendly')
    _draw_round_bomb(draw, sw * 0.67, sh * 0.80, min(w, h) / 32 * 0.95, (40, 47, 57), (255, 192, 84), (243, 191, 68), eye='dot')

    # chain chomp silhouette hint on the left hill
    ccx, ccy = sw * 0.10, sh * 0.64
    draw.ellipse(_ellipse_xy(ccx, ccy, sw * 0.05, sh * 0.05), fill=(31, 38, 47), outline=(8, 8, 8))
    for i in range(4):
        x = ccx + (i + 1) * sw * 0.03
        y = ccy + (i % 2) * sh * 0.01
        draw.ellipse(_ellipse_xy(x, y, sw * 0.010, sh * 0.010), fill=(179, 185, 190), outline=(80, 84, 88))

    # Crop tile from a 3x2 layout.
    tile_map = {0: (0, 0), 1: (1, 0), 2: (2, 0), 3: (0, 1), 4: (1, 1)}
    col, row = tile_map.get(tile, (tile % cols, min(rows - 1, tile // cols)))
    tile_img = scene.crop((col * w, row * h, (col + 1) * w, (row + 1) * h))
    return np.array(tile_img, dtype=np.uint8)


def _render_subject(draw, w, h, intent: TextureIntent, colors, rng):
    subject = intent.subject
    role = intent.role
    low = intent.fname.lower()

    if role == 'face':
        if subject == 'ghost':
            _draw_ghost(draw, w, h, colors, rng, face=True)
        elif subject == 'mouth' or 'mouth' in low:
            _draw_mouth(draw, w, h, colors, rng)
        else:
            eye_style = 'mario' if intent.family == 'mario' else 'generic'
            _draw_eye(draw, w, h, colors, rng, blink=('closed' in low or 'blink' in low), angry=('angry' in low), style=eye_style, low=low)
        return

    if role == 'sprite':
        if intent.motif == 'bubble':
            _draw_bubble_sprite(draw, w, h, colors, rng)
        elif intent.motif == 'ring':
            _draw_ring_sprite(draw, w, h, colors, rng)
        elif intent.motif == 'smoke' or subject == 'smoke':
            _draw_smoke_sprite(draw, w, h, colors, rng)
        elif intent.motif in {'flame', 'explosion'} or subject == 'lava':
            _draw_flame_sprite(draw, w, h, colors, rng)
        elif intent.motif == 'sparkle' or subject == 'sparkle':
            _draw_sparkle_sprite(draw, w, h, colors, rng)
        elif intent.motif == 'splash':
            _draw_splash_sprite(draw, w, h, colors, rng)
        elif intent.motif == 'tree':
            _draw_tree_sprite(draw, w, h, colors, rng)
        elif subject == 'snow':
            _draw_sparkle_sprite(draw, w, h, colors, rng)
        else:
            _draw_bubble_sprite(draw, w, h, colors, rng)
        return

    if role == 'overlay':
        _draw_emblem(draw, w, h, colors, rng, kind='lock' if 'lock' in low else 'star')
        return

    if role == 'door':
        if subject == 'metal':
            _draw_metal(draw, w, h, colors, rng, panelish=True)
        elif subject == 'fabric':
            _draw_fabric(draw, w, h, colors, rng, royal=True)
        else:
            _draw_wood(draw, w, h, colors, rng, doorish=True)
        return

    if role == 'box':
        if subject == 'metal':
            _draw_metal(draw, w, h, colors, rng, panelish=True)
        elif subject == 'fabric':
            _draw_fabric(draw, w, h, colors, rng, royal=True)
        else:
            _draw_wood(draw, w, h, colors, rng, doorish=False)
        _draw_emblem(draw, w, h, _palette('emblem', intent.motif, intent.family, rng), rng)
        return

    if role == 'sign':
        _draw_sign(draw, w, h, colors, rng)
        return

    if role == 'skybox':
        _draw_sky(draw, w, h, colors, rng, cloudy=True)
        return

    if role == 'portrait' and intent.motif == 'bobomb_battlefield_portrait':
        rgba = _render_bobomb_battlefield_portrait_rgba(intent.fname, (h, w, 4), rng)
        draw._image.paste(Image.fromarray(rgba, mode='RGBA'), (0, 0))
        return

    # subject-driven tileable / actor-surface textures
    if subject == 'grass':
        _draw_grass(draw, w, h, colors, rng, motif=intent.motif)
    elif subject == 'foliage':
        if intent.motif in {'leaf', 'stem'}:
            _draw_leaf(draw, w, h, colors, rng)
        else:
            _draw_foliage(draw, w, h, colors, rng)
    elif subject == 'water':
        _draw_water(draw, w, h, colors, rng, motif=intent.motif)
    elif subject == 'lava':
        _draw_lava(draw, w, h, colors, rng)
    elif subject == 'stone':
        _draw_stone(draw, w, h, colors, rng, bricky=False)
    elif subject == 'brick':
        _draw_stone(draw, w, h, colors, rng, bricky=True)
    elif subject == 'wood':
        _draw_wood(draw, w, h, colors, rng)
    elif subject == 'metal':
        _draw_metal(draw, w, h, colors, rng)
    elif subject == 'sand':
        _draw_sand(draw, w, h, colors, rng)
    elif subject == 'snow':
        _draw_snow(draw, w, h, colors, rng)
    elif subject == 'sky':
        _draw_sky(draw, w, h, colors, rng, cloudy=False)
    elif subject == 'cloud':
        _draw_sky(draw, w, h, colors, rng, cloudy=True)
    elif subject == 'fabric':
        _draw_fabric(draw, w, h, colors, rng, royal=(intent.motif in {'dress', 'princess'}))
    elif subject == 'sign':
        _draw_sign(draw, w, h, colors, rng)
    elif subject == 'ghost':
        _draw_ghost(draw, w, h, colors, rng, face=False)
    elif subject == 'coin':
        _draw_coin(draw, w, h, colors, rng, low)
    elif subject == 'bobomb_body':
        _draw_bobomb_body(draw, w, h, colors, rng, low)
    elif subject == 'shell':
        _draw_shell(draw, w, h, colors, rng)
    elif subject == 'scales':
        _draw_scales(draw, w, h, colors, rng)
    elif subject == 'skin':
        _draw_fur(draw, w, h, colors, rng)
    elif subject == 'fur':
        _draw_fur(draw, w, h, colors, rng)
    elif subject == 'feather':
        _draw_feather(draw, w, h, colors, rng)
    elif subject == 'beak':
        _draw_beak(draw, w, h, colors, rng)
    elif subject == 'ivory':
        _draw_ivory(draw, w, h, colors, rng)
    elif subject == 'flower':
        _draw_flower(draw, w, h, colors, rng)
    elif subject == 'jewel':
        _draw_jewel(draw, w, h, colors, rng)
    elif subject == 'pages':
        _draw_pages(draw, w, h, colors, rng)
    elif subject == 'book_cover':
        _draw_book_cover(draw, w, h, colors, rng)
    elif subject == 'piano_keys':
        _draw_piano_keys(draw, w, h, colors, rng)
    elif subject == 'egg':
        _draw_egg(draw, w, h, colors, rng)
    elif subject == 'lens':
        _draw_lens(draw, w, h, colors, rng)
    elif subject == 'emblem':
        _draw_emblem(draw, w, h, colors, rng)
    else:
        # final fallback tries to stay visually meaningful rather than abstract
        if intent.role == 'wall':
            _draw_stone(draw, w, h, colors, rng, bricky=True)
        elif intent.role == 'floor':
            _draw_stone(draw, w, h, colors, rng, bricky=False)
        else:
            _draw_wood(draw, w, h, colors, rng)


def render_pil_texture(fname: str, shape, rng=None, identity=None):
    h, w = int(shape[0]), int(shape[1])
    local_rng = _to_rng(rng, fname)
    intent = analyze_texture_intent(fname)
    colors = _palette(intent.subject, intent.motif, intent.family, local_rng)

    if intent.role == 'portrait' and intent.motif == 'bobomb_battlefield_portrait':
        rgba = _render_bobomb_battlefield_portrait_rgba(fname, (h, w, 4), local_rng)
    else:
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        _render_subject(draw, w, h, intent, colors, local_rng)
        rgba = np.array(img, dtype=np.uint8)
    req_channels = shape[2] if len(shape) == 3 else 1
    if req_channels == 4:
        return rgba
    if req_channels == 3:
        return rgba[:, :, 0:3]
    intensity = np.clip(
        0.299 * rgba[:, :, 0] + 0.587 * rgba[:, :, 1] + 0.114 * rgba[:, :, 2], 0, 255
    ).astype(np.uint8)
    if req_channels == 2:
        alpha = rgba[:, :, 3]
        if np.all(alpha == 0):
            alpha = np.full_like(intensity, 255)
        return np.stack([intensity, alpha], axis=2)
    return intensity


__all__ = [
    'TextureIntent',
    'analyze_texture_intent',
    'classify_texture_role',
    'classify_texture_subject',
    'render_pil_texture',
]
