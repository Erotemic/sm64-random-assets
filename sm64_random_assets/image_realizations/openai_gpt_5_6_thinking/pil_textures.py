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


_CASTLE_PORTRAIT_FILE_RULES = [
    ('levels/castle_inside/17.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_bobomb_battlefield_top')),
    ('levels/castle_inside/18.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_bobomb_battlefield_bottom')),
    ('levels/castle_inside/19.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_cool_cool_mountain_top')),
    ('levels/castle_inside/20.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_cool_cool_mountain_bottom')),
    ('levels/castle_inside/21.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_whomps_fortress_top')),
    ('levels/castle_inside/22.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_whomps_fortress_bottom')),
    ('levels/castle_inside/23.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_jolly_roger_bay_top')),
    ('levels/castle_inside/23_us.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_jolly_roger_bay_top')),
    ('levels/castle_inside/24.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_jolly_roger_bay_bottom')),
    ('levels/castle_inside/24_us.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_jolly_roger_bay_bottom')),
    ('levels/castle_inside/25.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_lethal_lava_land_top')),
    ('levels/castle_inside/26.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_lethal_lava_land_bottom')),
    ('levels/castle_inside/27.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_shifting_sand_land_top')),
    ('levels/castle_inside/28.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_shifting_sand_land_bottom')),
    ('levels/castle_inside/29.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_tiny_huge_island_tiny')),
    ('levels/castle_inside/30.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_tiny_huge_island_huge')),
    ('levels/castle_inside/31.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_snowmans_land_top')),
    ('levels/castle_inside/32.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_snowmans_land_bottom')),
    ('levels/castle_inside/33.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_wet_dry_world_top')),
    ('levels/castle_inside/34.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_wet_dry_world_bottom')),
    ('levels/castle_inside/35.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_tall_tall_mountain_top')),
    ('levels/castle_inside/36.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_tall_tall_mountain_bottom')),
    ('levels/castle_inside/37.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_tick_tock_clock_top')),
    ('levels/castle_inside/38.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_tick_tock_clock_bottom')),
    ('levels/castle_inside/39.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_rainbow_ride_top')),
    ('levels/castle_inside/40.rgba16.png', dict(subject='portrait', role='portrait', motif='castle_portrait_rainbow_ride_bottom')),
]

_CASTLE_PORTRAIT_LAYOUTS = {
    'levels/castle_inside/17.rgba16.png': ('bobomb_battlefield', 'top'),
    'levels/castle_inside/18.rgba16.png': ('bobomb_battlefield', 'bottom'),
    'levels/castle_inside/19.rgba16.png': ('cool_cool_mountain', 'top'),
    'levels/castle_inside/20.rgba16.png': ('cool_cool_mountain', 'bottom'),
    'levels/castle_inside/21.rgba16.png': ('whomps_fortress', 'top'),
    'levels/castle_inside/22.rgba16.png': ('whomps_fortress', 'bottom'),
    'levels/castle_inside/23.rgba16.png': ('jolly_roger_bay', 'top'),
    'levels/castle_inside/23_us.rgba16.png': ('jolly_roger_bay', 'top'),
    'levels/castle_inside/24.rgba16.png': ('jolly_roger_bay', 'bottom'),
    'levels/castle_inside/24_us.rgba16.png': ('jolly_roger_bay', 'bottom'),
    'levels/castle_inside/25.rgba16.png': ('lethal_lava_land', 'top'),
    'levels/castle_inside/26.rgba16.png': ('lethal_lava_land', 'bottom'),
    'levels/castle_inside/27.rgba16.png': ('shifting_sand_land', 'top'),
    'levels/castle_inside/28.rgba16.png': ('shifting_sand_land', 'bottom'),
    'levels/castle_inside/29.rgba16.png': ('tiny_huge_island_tiny', 'full'),
    'levels/castle_inside/30.rgba16.png': ('tiny_huge_island_huge', 'full'),
    'levels/castle_inside/31.rgba16.png': ('snowmans_land', 'top'),
    'levels/castle_inside/32.rgba16.png': ('snowmans_land', 'bottom'),
    'levels/castle_inside/33.rgba16.png': ('wet_dry_world', 'top'),
    'levels/castle_inside/34.rgba16.png': ('wet_dry_world', 'bottom'),
    'levels/castle_inside/35.rgba16.png': ('tall_tall_mountain', 'top'),
    'levels/castle_inside/36.rgba16.png': ('tall_tall_mountain', 'bottom'),
    'levels/castle_inside/37.rgba16.png': ('tick_tock_clock', 'top'),
    'levels/castle_inside/38.rgba16.png': ('tick_tock_clock', 'bottom'),
    'levels/castle_inside/39.rgba16.png': ('rainbow_ride', 'top'),
    'levels/castle_inside/40.rgba16.png': ('rainbow_ride', 'bottom'),
}


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
    *_CASTLE_PORTRAIT_FILE_RULES,
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



def _draw_highres_bobomb(draw, cx, cy, radius, body, shoes, fuse, *, king=False, buddy=False):
    outline = (24, 23, 27, 255)
    # Drop shadow anchors the character into the painted ground.
    draw.ellipse((cx - radius * 0.9, cy + radius * 0.72, cx + radius * 0.9, cy + radius * 1.12), fill=(30, 45, 25, 70))
    # Feet.
    shoe_y = cy + radius * 0.72
    shoe_rx = radius * 0.44
    shoe_ry = radius * 0.24
    draw.ellipse((cx - radius * 0.78 - shoe_rx, shoe_y - shoe_ry, cx - radius * 0.78 + shoe_rx, shoe_y + shoe_ry), fill=shoes, outline=outline, width=max(1, radius // 14))
    draw.ellipse((cx + radius * 0.78 - shoe_rx, shoe_y - shoe_ry, cx + radius * 0.78 + shoe_rx, shoe_y + shoe_ry), fill=shoes, outline=outline, width=max(1, radius // 14))
    # Spherical body with concentric painterly shading.
    for step in range(18, 0, -1):
        t = step / 18.0
        rx = radius * t
        ry = radius * t
        # Shift highlights up-left and shadows down-right.
        shift_x = radius * (1 - t) * -0.22
        shift_y = radius * (1 - t) * -0.24
        shaded = _mix(body[0], body[1], 1 - t)
        draw.ellipse((cx - rx + shift_x, cy - ry + shift_y, cx + rx + shift_x, cy + ry + shift_y), fill=shaded)
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=outline, width=max(2, radius // 10))
    # Glossy brush highlight.
    draw.ellipse((cx - radius * 0.58, cy - radius * 0.62, cx - radius * 0.12, cy - radius * 0.18), fill=(255, 255, 255, 95))
    # Fuse cap and fuse.
    cap_w = radius * 0.44
    cap_h = radius * 0.27
    cap_fill = (195, 152, 58, 255) if king else (123, 99, 72, 255)
    draw.rounded_rectangle((cx - cap_w / 2, cy - radius - cap_h * 0.42, cx + cap_w / 2, cy - radius + cap_h * 0.58), radius=max(2, int(radius * 0.08)), fill=cap_fill, outline=outline, width=max(1, radius // 14))
    fuse_start = (cx + cap_w * 0.25, cy - radius - cap_h * 0.15)
    fuse_end = (cx + radius * 0.92, cy - radius * 1.48)
    draw.line((fuse_start[0], fuse_start[1], fuse_end[0], fuse_end[1]), fill=fuse, width=max(2, radius // 8))
    spark_r = max(3, radius * 0.14)
    draw.ellipse((fuse_end[0] - spark_r, fuse_end[1] - spark_r, fuse_end[0] + spark_r, fuse_end[1] + spark_r), fill=(255, 207, 64, 255), outline=(180, 92, 20, 255), width=max(1, radius // 18))
    # Eyes.
    eye_y = cy - radius * 0.04
    eye_dx = radius * 0.34
    eye_rx = radius * 0.13
    eye_ry = radius * 0.20
    for sign in (-1, 1):
        ex = cx + sign * eye_dx
        draw.ellipse((ex - eye_rx, eye_y - eye_ry, ex + eye_rx, eye_y + eye_ry), fill=(250, 250, 244, 255), outline=outline, width=max(1, radius // 18))
        pupil_shift = radius * (0.03 if buddy else -0.01)
        draw.ellipse((ex - eye_rx * 0.38 + pupil_shift, eye_y - eye_ry * 0.22, ex + eye_rx * 0.38 + pupil_shift, eye_y + eye_ry * 0.45), fill=(24, 23, 27, 255))
    if king:
        crown_y = cy - radius * 1.18
        crown_w = radius * 1.15
        crown_h = radius * 0.48
        pts = [
            (cx - crown_w / 2, crown_y + crown_h),
            (cx - crown_w * 0.40, crown_y),
            (cx - crown_w * 0.15, crown_y + crown_h * 0.42),
            (cx, crown_y - crown_h * 0.16),
            (cx + crown_w * 0.15, crown_y + crown_h * 0.42),
            (cx + crown_w * 0.40, crown_y),
            (cx + crown_w / 2, crown_y + crown_h),
        ]
        draw.polygon(pts, fill=(238, 190, 61, 255), outline=outline)
        draw.ellipse((cx - radius * 0.12, crown_y + crown_h * 0.36, cx + radius * 0.12, crown_y + crown_h * 0.60), fill=(209, 61, 61, 255), outline=outline)




def _lerp_color(a, b, t):
    return tuple(int(round(ai + (bi - ai) * t)) for ai, bi in zip(a, b))


def _paint_vertical_gradient(draw, w, h, stops):
    stops = sorted(stops, key=lambda item: item[0])
    for y in range(h):
        t = y / max(1, h - 1)
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t <= t1:
                lt = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
                draw.line((0, y, w, y), fill=_lerp_color(c0, c1, max(0.0, min(1.0, lt))))
                break
        else:
            draw.line((0, y, w, y), fill=stops[-1][1])


def _draw_cloud_cluster(draw, cx, cy, rx, ry, fill=(255, 255, 250, 210)):
    offsets = [(-0.45, 0.10, 0.56, 0.46), (0.0, -0.10, 0.72, 0.60), (0.46, 0.08, 0.52, 0.44)]
    for ox, oy, sx, sy in offsets:
        draw.ellipse((cx + ox * rx - sx * rx, cy + oy * ry - sy * ry, cx + ox * rx + sx * rx, cy + oy * ry + sy * ry), fill=fill)


def _draw_pine_tree(draw, x, base_y, scale, leaf=(56, 120, 70, 255), trunk=(112, 79, 48, 255)):
    trunk_w = max(3, int(4 * scale))
    draw.rectangle((x - trunk_w // 2, base_y - 11 * scale, x + trunk_w // 2, base_y), fill=trunk)
    for idx, spread in enumerate((13, 10, 7)):
        top = base_y - (28 - idx * 8) * scale
        pts = [(x, top), (x - spread * scale, top + 12 * scale), (x + spread * scale, top + 12 * scale)]
        draw.polygon(pts, fill=leaf, outline=(34, 73, 43, 255))


def _draw_house(draw, x, y, scale, wall=(181, 150, 110, 255), roof=(154, 64, 46, 255)):
    draw.rectangle((x, y, x + 18 * scale, y + 14 * scale), fill=wall, outline=(88, 67, 46, 255))
    draw.polygon([(x - 2 * scale, y + 2 * scale), (x + 9 * scale, y - 7 * scale), (x + 20 * scale, y + 2 * scale)], fill=roof, outline=(88, 43, 31, 255))
    draw.rectangle((x + 7 * scale, y + 5 * scale, x + 11 * scale, y + 14 * scale), fill=(103, 74, 44, 255))
    draw.rectangle((x + 2 * scale, y + 5 * scale, x + 6 * scale, y + 9 * scale), fill=(168, 214, 233, 255), outline=(82, 120, 146, 255))


def _draw_gear(draw, cx, cy, inner_r, outer_r, teeth, fill=(185, 151, 74, 255), outline=(86, 67, 35, 255)):
    pts = []
    for idx in range(teeth * 2):
        ang = (2 * math.pi * idx) / (teeth * 2)
        radius = outer_r if idx % 2 == 0 else inner_r
        pts.append((cx + math.cos(ang) * radius, cy + math.sin(ang) * radius))
    draw.polygon(pts, fill=fill, outline=outline)
    draw.ellipse((cx - inner_r * 0.45, cy - inner_r * 0.45, cx + inner_r * 0.45, cy + inner_r * 0.45), fill=(235, 214, 167, 255), outline=outline)


def _draw_rainbow_arc(draw, bbox, width):
    colors = [
        (235, 76, 88, 255),
        (244, 150, 57, 255),
        (244, 216, 82, 255),
        (92, 194, 103, 255),
        (87, 153, 235, 255),
        (150, 112, 219, 255),
    ]
    for idx, color in enumerate(colors):
        inset = idx * width
        draw.arc((bbox[0] + inset, bbox[1] + inset, bbox[2] - inset, bbox[3] - inset), 190, 350, fill=color, width=max(1, width))


def _draw_portrait_border(draw, w, h):
    draw.rectangle((2, 2, w - 3, h - 3), outline=(78, 54, 34, 255), width=4)
    draw.rectangle((8, 8, w - 9, h - 9), outline=(171, 129, 79, 190), width=2)


def _draw_scattered_dabs(draw, rng, w, h, colors, count):
    for _ in range(count):
        x = int(rng.randint(0, w))
        y = int(rng.randint(0, h))
        rx = int(rng.randint(1, 4))
        ry = int(rng.randint(1, 4))
        color = colors[int(rng.randint(0, len(colors)))]
        draw.ellipse((x - rx, y - ry, x + rx, y + ry), fill=color)


def _render_generic_castle_portrait_full(scene_key):
    scale = 1
    final_size = 64
    work_size = 256
    sw = sh = work_size
    rng = np.random.RandomState(_stable_seed(f'castle-portrait-{scene_key}-v1'))
    scene = Image.new('RGBA', (sw, sh), (0, 0, 0, 255))
    draw = ImageDraw.Draw(scene, 'RGBA')

    if scene_key == 'cool_cool_mountain':
        _paint_vertical_gradient(draw, sw, sh, [(0.0, (116, 180, 242)), (0.58, (214, 236, 252)), (1.0, (239, 245, 252))])
        _draw_cloud_cluster(draw, 56 * scale, 42 * scale, 34 * scale, 14 * scale)
        _draw_cloud_cluster(draw, 185 * scale, 52 * scale, 42 * scale, 16 * scale)
        draw.polygon([(0, 184 * scale), (58 * scale, 108 * scale), (94 * scale, 150 * scale), (132 * scale, 70 * scale), (178 * scale, 142 * scale), (228 * scale, 92 * scale), (sw, 164 * scale), (sw, sh), (0, sh)], fill=(148, 176, 203, 255))
        draw.polygon([(24 * scale, sh), (98 * scale, 144 * scale), (154 * scale, sh)], fill=(232, 239, 247, 255), outline=(184, 200, 220, 255))
        draw.polygon([(122 * scale, sh), (194 * scale, 118 * scale), (sw, sh)], fill=(245, 248, 252, 255), outline=(198, 210, 223, 255))
        draw.polygon([(0, 216 * scale), (76 * scale, 188 * scale), (124 * scale, 214 * scale), (sw, 175 * scale), (sw, sh), (0, sh)], fill=(214, 224, 235, 255))
        draw.line((72 * scale, 188 * scale, 114 * scale, 158 * scale), fill=(142, 160, 181, 255), width=5 * scale)
        draw.line((114 * scale, 158 * scale, 128 * scale, 124 * scale), fill=(142, 160, 181, 255), width=4 * scale)
        _draw_house(draw, 166 * scale, 176 * scale, scale)
        draw.ellipse((184 * scale, 170 * scale, 212 * scale, 196 * scale), fill=(250, 250, 253, 255), outline=(150, 162, 180, 255))
        draw.ellipse((190 * scale, 177 * scale, 197 * scale, 184 * scale), fill=(32, 36, 45, 255))
        draw.ellipse((201 * scale, 177 * scale, 208 * scale, 184 * scale), fill=(32, 36, 45, 255))
        draw.polygon([(199 * scale, 184 * scale), (195 * scale, 189 * scale), (203 * scale, 189 * scale)], fill=(236, 180, 87, 255))
        _draw_scattered_dabs(draw, rng, sw, sh, [(255, 255, 255, 60), (217, 233, 247, 60)], 120)
    elif scene_key == 'whomps_fortress':
        _paint_vertical_gradient(draw, sw, sh, [(0.0, (110, 180, 244)), (0.64, (205, 231, 249)), (1.0, (128, 192, 126))])
        _draw_cloud_cluster(draw, 68 * scale, 48 * scale, 30 * scale, 14 * scale)
        draw.polygon([(20 * scale, sh), (94 * scale, 128 * scale), (168 * scale, sh)], fill=(133, 184, 110, 255))
        draw.polygon([(102 * scale, 150 * scale), (188 * scale, 90 * scale), (232 * scale, 174 * scale), (182 * scale, 205 * scale)], fill=(113, 155, 100, 255), outline=(52, 94, 56, 255))
        stone = (162, 165, 173, 255)
        stone_dark = (118, 122, 132, 255)
        draw.rectangle((104 * scale, 92 * scale, 146 * scale, 170 * scale), fill=stone, outline=stone_dark, width=3 * scale)
        draw.rectangle((134 * scale, 62 * scale, 186 * scale, 184 * scale), fill=stone, outline=stone_dark, width=3 * scale)
        draw.rectangle((120 * scale, 110 * scale, 134 * scale, 184 * scale), fill=stone_dark)
        draw.line((136 * scale, 92 * scale, 184 * scale, 62 * scale), fill=(192, 144, 88, 255), width=4 * scale)
        draw.ellipse((30 * scale, 178 * scale, 76 * scale, 222 * scale), fill=(62, 74, 86, 255), outline=(19, 23, 30, 255), width=3 * scale)
        draw.line((54 * scale, 178 * scale, 54 * scale, 154 * scale), fill=(88, 64, 44, 255), width=3 * scale)
        _draw_pine_tree(draw, 218 * scale, 173 * scale, scale * 0.8)
        _draw_scattered_dabs(draw, rng, sw, sh, [(166, 184, 192, 70), (240, 244, 250, 70), (112, 168, 104, 50)], 110)
    elif scene_key == 'jolly_roger_bay':
        _paint_vertical_gradient(draw, sw, sh, [(0.0, (87, 154, 219)), (0.46, (167, 214, 239)), (1.0, (36, 106, 153))])
        draw.ellipse((-10 * scale, 126 * scale, 104 * scale, 242 * scale), fill=(72, 136, 87, 255), outline=(42, 90, 51, 255))
        draw.rectangle((0, 148 * scale, sw, sh), fill=(51, 121, 176, 255))
        for y in range(160 * scale, sh, 12 * scale):
            draw.line((0, y, sw, y - 8 * scale), fill=(87, 154, 206, 120), width=2 * scale)
        hull = [(108 * scale, 146 * scale), (206 * scale, 146 * scale), (186 * scale, 182 * scale), (124 * scale, 182 * scale)]
        draw.polygon(hull, fill=(112, 78, 52, 255), outline=(61, 44, 31, 255))
        draw.line((156 * scale, 146 * scale, 156 * scale, 88 * scale), fill=(121, 83, 54, 255), width=3 * scale)
        draw.polygon([(156 * scale, 90 * scale), (186 * scale, 112 * scale), (156 * scale, 126 * scale)], fill=(242, 239, 214, 255), outline=(176, 169, 132, 255))
        draw.arc((188 * scale, 164 * scale, 238 * scale, 212 * scale), 190, 350, fill=(225, 196, 86, 255), width=3 * scale)
        draw.line((213 * scale, 188 * scale, 213 * scale, 218 * scale), fill=(119, 83, 50, 255), width=3 * scale)
        draw.line((108 * scale, 148 * scale, 78 * scale, 112 * scale), fill=(61, 44, 31, 255), width=3 * scale)
        eel = [(204 * scale, 206 * scale), (198 * scale, 214 * scale), (206 * scale, 224 * scale), (214 * scale, 219 * scale), (220 * scale, 208 * scale)]
        draw.line(eel, fill=(34, 64, 90, 200), width=10 * scale)
        _draw_scattered_dabs(draw, rng, sw, sh, [(130, 188, 229, 55), (42, 104, 153, 55), (255, 255, 255, 35)], 130)
    elif scene_key == 'lethal_lava_land':
        _paint_vertical_gradient(draw, sw, sh, [(0.0, (111, 70, 81)), (0.42, (188, 98, 74)), (1.0, (243, 142, 58))])
        draw.rectangle((0, 150 * scale, sw, sh), fill=(234, 86, 35, 255))
        for y in range(170 * scale, sh, 14 * scale):
            draw.line((0, y, sw, y - 4 * scale), fill=(255, 171, 70, 110), width=2 * scale)
        draw.polygon([(74 * scale, 178 * scale), (126 * scale, 92 * scale), (180 * scale, 178 * scale)], fill=(76, 58, 53, 255), outline=(40, 30, 28, 255))
        draw.polygon([(108 * scale, 132 * scale), (126 * scale, 92 * scale), (144 * scale, 132 * scale)], fill=(226, 156, 41, 255))
        for cx, cy, rad in [(60, 190, 14), (100, 210, 12), (156, 196, 10), (202, 208, 13)]:
            draw.ellipse((cx * scale - rad * scale, cy * scale - rad * scale, cx * scale + rad * scale, cy * scale + rad * scale), fill=(98, 77, 66, 255), outline=(42, 33, 28, 255))
        draw.ellipse((202 * scale, 180 * scale, 232 * scale, 210 * scale), fill=(40, 37, 44, 255), outline=(18, 16, 20, 255))
        draw.ellipse((208 * scale, 188 * scale, 214 * scale, 194 * scale), fill=(255, 111, 89, 255))
        draw.ellipse((220 * scale, 188 * scale, 226 * scale, 194 * scale), fill=(255, 111, 89, 255))
        _draw_scattered_dabs(draw, rng, sw, sh, [(255, 192, 80, 70), (92, 66, 56, 70), (255, 244, 172, 40)], 100)
    elif scene_key == 'shifting_sand_land':
        _paint_vertical_gradient(draw, sw, sh, [(0.0, (106, 180, 242)), (0.62, (229, 240, 245)), (1.0, (241, 213, 141))])
        draw.polygon([(0, 192 * scale), (84 * scale, 142 * scale), (152 * scale, 182 * scale), (sw, 148 * scale), (sw, sh), (0, sh)], fill=(227, 194, 111, 255))
        draw.polygon([(56 * scale, 170 * scale), (98 * scale, 104 * scale), (140 * scale, 170 * scale)], fill=(203, 163, 88, 255), outline=(137, 111, 62, 255))
        draw.polygon([(120 * scale, 174 * scale), (170 * scale, 94 * scale), (220 * scale, 174 * scale)], fill=(221, 183, 101, 255), outline=(137, 111, 62, 255))
        draw.polygon([(148 * scale, 190 * scale), (178 * scale, 162 * scale), (208 * scale, 190 * scale), (178 * scale, 218 * scale)], fill=(205, 174, 95, 255), outline=(137, 111, 62, 255))
        draw.rectangle((208 * scale, 144 * scale, 214 * scale, 194 * scale), fill=(114, 82, 48, 255))
        for lx in (194, 220):
            draw.polygon([(lx * scale, 140 * scale), ((lx - 18) * scale, 164 * scale), ((lx + 18) * scale, 164 * scale)], fill=(58, 138, 72, 255), outline=(34, 88, 44, 255))
        draw.arc((12 * scale, 20 * scale, 52 * scale, 60 * scale), 0, 360, fill=(247, 235, 139, 255), width=6 * scale)
        _draw_scattered_dabs(draw, rng, sw, sh, [(251, 233, 166, 55), (193, 161, 89, 55), (255, 255, 250, 30)], 120)
    elif scene_key == 'tiny_huge_island_tiny':
        _paint_vertical_gradient(draw, sw, sh, [(0.0, (106, 188, 243)), (0.52, (190, 226, 245)), (1.0, (58, 151, 203))])
        draw.rectangle((0, 154 * scale, sw, sh), fill=(64, 163, 214, 255))
        draw.ellipse((88 * scale, 132 * scale, 170 * scale, 188 * scale), fill=(86, 173, 87, 255), outline=(45, 96, 50, 255))
        draw.polygon([(118 * scale, 156 * scale), (130 * scale, 120 * scale), (142 * scale, 156 * scale)], fill=(115, 156, 72, 255))
        draw.rectangle((127 * scale, 136 * scale, 133 * scale, 156 * scale), fill=(114, 81, 49, 255))
        draw.polygon([(92 * scale, 164 * scale), (76 * scale, 175 * scale), (88 * scale, 184 * scale)], fill=(112, 84, 56, 255))
        draw.ellipse((92 * scale, 160 * scale, 100 * scale, 168 * scale), fill=(227, 78, 78, 255))
        for y in range(166 * scale, sh, 14 * scale):
            draw.line((0, y, sw, y - 5 * scale), fill=(125, 202, 231, 100), width=2 * scale)
        _draw_scattered_dabs(draw, rng, sw, sh, [(255, 255, 255, 35), (95, 186, 233, 45), (71, 151, 109, 45)], 120)
    elif scene_key == 'tiny_huge_island_huge':
        _paint_vertical_gradient(draw, sw, sh, [(0.0, (98, 183, 238)), (0.52, (190, 226, 245)), (1.0, (76, 165, 104))])
        draw.ellipse((-10 * scale, 138 * scale, 266 * scale, 286 * scale), fill=(102, 184, 90, 255), outline=(54, 107, 53, 255))
        draw.rectangle((30 * scale, 132 * scale, 38 * scale, 198 * scale), fill=(126, 84, 48, 255))
        draw.ellipse((2 * scale, 88 * scale, 66 * scale, 148 * scale), fill=(62, 144, 72, 255), outline=(36, 92, 46, 255))
        draw.rectangle((196 * scale, 142 * scale, 204 * scale, 212 * scale), fill=(118, 82, 45, 255))
        draw.ellipse((164 * scale, 92 * scale, 236 * scale, 160 * scale), fill=(59, 139, 70, 255), outline=(33, 86, 43, 255))
        draw.ellipse((104 * scale, 166 * scale, 152 * scale, 206 * scale), fill=(222, 74, 74, 255), outline=(120, 34, 34, 255))
        for dotx, doty in [(116, 176), (126, 184), (138, 176), (128, 166)]:
            draw.ellipse((dotx * scale, doty * scale, (dotx + 4) * scale, (doty + 4) * scale), fill=(255, 255, 252, 255))
        _draw_scattered_dabs(draw, rng, sw, sh, [(255, 255, 255, 30), (72, 155, 93, 50), (124, 207, 235, 40)], 110)
    elif scene_key == 'snowmans_land':
        _paint_vertical_gradient(draw, sw, sh, [(0.0, (129, 184, 235)), (0.56, (211, 233, 247)), (1.0, (234, 240, 247))])
        draw.polygon([(0, 190 * scale), (56 * scale, 150 * scale), (116 * scale, 178 * scale), (186 * scale, 132 * scale), (sw, 174 * scale), (sw, sh), (0, sh)], fill=(230, 236, 243, 255))
        draw.ellipse((116 * scale, 136 * scale, 204 * scale, 222 * scale), fill=(248, 249, 252, 255), outline=(177, 193, 209, 255))
        draw.ellipse((130 * scale, 90 * scale, 192 * scale, 150 * scale), fill=(250, 250, 253, 255), outline=(177, 193, 209, 255))
        draw.ellipse((148 * scale, 108 * scale, 154 * scale, 114 * scale), fill=(32, 36, 45, 255))
        draw.ellipse((170 * scale, 108 * scale, 176 * scale, 114 * scale), fill=(32, 36, 45, 255))
        draw.polygon([(160 * scale, 116 * scale), (190 * scale, 122 * scale), (160 * scale, 128 * scale)], fill=(240, 160, 62, 255))
        _draw_pine_tree(draw, 58 * scale, 182 * scale, scale * 0.9, leaf=(66, 120, 82, 255))
        _draw_pine_tree(draw, 218 * scale, 176 * scale, scale * 0.7, leaf=(62, 116, 78, 255))
        _draw_scattered_dabs(draw, rng, sw, sh, [(255, 255, 255, 60), (205, 223, 238, 40)], 130)
    elif scene_key == 'wet_dry_world':
        _paint_vertical_gradient(draw, sw, sh, [(0.0, (129, 168, 237)), (0.50, (211, 226, 245)), (1.0, (99, 164, 208))])
        waterline = 156 * scale
        draw.rectangle((0, waterline, sw, sh), fill=(84, 151, 199, 255))
        for x, hgt, col in [(38, 56, (196, 178, 96, 255)), (78, 72, (210, 98, 86, 255)), (124, 48, (206, 199, 164, 255)), (166, 62, (169, 190, 117, 255)), (208, 82, (196, 150, 87, 255))]:
            draw.rectangle((x * scale, (waterline - hgt), (x + 24) * scale, waterline), fill=col, outline=(92, 83, 71, 255))
            draw.rectangle(((x + 8) * scale, (waterline - hgt + 16), (x + 16) * scale, (waterline - hgt + 32)), fill=(140, 197, 227, 255), outline=(76, 120, 146, 255))
        draw.line((0, waterline, sw, waterline), fill=(197, 228, 245, 180), width=3 * scale)
        for y in range(waterline + 8 * scale, sh, 12 * scale):
            draw.line((0, y, sw, y - 4 * scale), fill=(126, 192, 227, 100), width=2 * scale)
        _draw_scattered_dabs(draw, rng, sw, sh, [(138, 203, 234, 45), (236, 241, 248, 35), (192, 168, 103, 30)], 120)
    elif scene_key == 'tall_tall_mountain':
        _paint_vertical_gradient(draw, sw, sh, [(0.0, (112, 185, 242)), (0.56, (208, 232, 247)), (1.0, (114, 183, 106))])
        draw.polygon([(24 * scale, sh), (124 * scale, 88 * scale), (224 * scale, sh)], fill=(116, 160, 90, 255), outline=(55, 96, 51, 255))
        draw.polygon([(84 * scale, 178 * scale), (128 * scale, 88 * scale), (170 * scale, 178 * scale)], fill=(148, 186, 109, 255))
        draw.line((120 * scale, 126 * scale, 108 * scale, 210 * scale), fill=(187, 226, 239, 255), width=6 * scale)
        draw.line((108 * scale, 210 * scale, 96 * scale, sh), fill=(187, 226, 239, 255), width=7 * scale)
        for mx in (64, 172, 198):
            draw.ellipse((mx * scale, 198 * scale, (mx + 24) * scale, (198 + 14) * scale), fill=(208, 158, 118, 255), outline=(126, 90, 64, 255))
            draw.rectangle(((mx + 10) * scale, 180 * scale, (mx + 14) * scale, 198 * scale), fill=(193, 171, 130, 255))
        draw.ellipse((174 * scale, 150 * scale, 196 * scale, 174 * scale), fill=(155, 110, 79, 255), outline=(88, 59, 38, 255))
        draw.line((186 * scale, 164 * scale, 198 * scale, 152 * scale), fill=(88, 59, 38, 255), width=3 * scale)
        _draw_scattered_dabs(draw, rng, sw, sh, [(255, 255, 255, 35), (120, 180, 113, 45), (179, 224, 235, 45)], 120)
    elif scene_key == 'tick_tock_clock':
        _paint_vertical_gradient(draw, sw, sh, [(0.0, (90, 78, 98)), (0.55, (158, 141, 112)), (1.0, (207, 177, 105))])
        draw.ellipse((18 * scale, 18 * scale, 238 * scale, 238 * scale), fill=(231, 205, 131, 255), outline=(111, 80, 37, 255), width=6 * scale)
        draw.ellipse((42 * scale, 42 * scale, 214 * scale, 214 * scale), fill=(245, 233, 196, 255), outline=(154, 122, 62, 255), width=4 * scale)
        for ang in range(12):
            rad = math.radians(ang * 30 - 90)
            x0 = 128 * scale + math.cos(rad) * 74 * scale
            y0 = 128 * scale + math.sin(rad) * 74 * scale
            x1 = 128 * scale + math.cos(rad) * 86 * scale
            y1 = 128 * scale + math.sin(rad) * 86 * scale
            draw.line((x0, y0, x1, y1), fill=(111, 80, 37, 255), width=3 * scale)
        _draw_gear(draw, 66 * scale, 66 * scale, 18 * scale, 28 * scale, 10)
        _draw_gear(draw, 198 * scale, 82 * scale, 14 * scale, 24 * scale, 9, fill=(174, 142, 71, 255))
        _draw_gear(draw, 188 * scale, 194 * scale, 18 * scale, 30 * scale, 11, fill=(194, 163, 86, 255))
        draw.line((128 * scale, 128 * scale, 128 * scale, 72 * scale), fill=(74, 56, 37, 255), width=5 * scale)
        draw.line((128 * scale, 128 * scale, 168 * scale, 152 * scale), fill=(74, 56, 37, 255), width=5 * scale)
        draw.ellipse((118 * scale, 118 * scale, 138 * scale, 138 * scale), fill=(74, 56, 37, 255))
        _draw_scattered_dabs(draw, rng, sw, sh, [(247, 232, 189, 25), (110, 92, 67, 35), (220, 181, 98, 35)], 100)
    elif scene_key == 'rainbow_ride':
        _paint_vertical_gradient(draw, sw, sh, [(0.0, (138, 191, 249)), (0.56, (228, 239, 252)), (1.0, (244, 233, 247))])
        _draw_cloud_cluster(draw, 58 * scale, 68 * scale, 34 * scale, 15 * scale)
        _draw_cloud_cluster(draw, 192 * scale, 52 * scale, 42 * scale, 16 * scale)
        _draw_cloud_cluster(draw, 128 * scale, 150 * scale, 56 * scale, 20 * scale, fill=(255, 255, 251, 230))
        _draw_rainbow_arc(draw, (12 * scale, 70 * scale, 248 * scale, 250 * scale), max(2, int(3 * scale)))
        draw.polygon([(104 * scale, 170 * scale), (156 * scale, 170 * scale), (164 * scale, 182 * scale), (96 * scale, 182 * scale)], fill=(167, 122, 87, 255), outline=(95, 67, 44, 255))
        draw.line((116 * scale, 170 * scale, 108 * scale, 142 * scale), fill=(95, 67, 44, 255), width=3 * scale)
        draw.line((144 * scale, 170 * scale, 150 * scale, 144 * scale), fill=(95, 67, 44, 255), width=3 * scale)
        for px, py in [(72, 184), (188, 174), (214, 196)]:
            draw.rectangle((px * scale, py * scale, (px + 22) * scale, (py + 6) * scale), fill=(214, 197, 164, 255), outline=(123, 111, 85, 255))
        _draw_scattered_dabs(draw, rng, sw, sh, [(255, 255, 255, 55), (248, 218, 235, 35), (126, 187, 246, 35)], 125)
    else:
        raise KeyError(scene_key)

    _draw_portrait_border(draw, sw, sh)
    return scene.resize((final_size, final_size), Image.Resampling.LANCZOS)


def _render_bobomb_battlefield_portrait_full():
    # Generate at 4x resolution, then downsample. The fixed seed guarantees that
    # the two independently requested 64x32 halves always match perfectly.
    scale = 4
    size = 64
    sw = sh = size * scale
    rng = np.random.RandomState(_stable_seed('bobomb-battlefield-portrait-v2'))
    scene = Image.new('RGBA', (sw, sh), (0, 0, 0, 255))
    draw = ImageDraw.Draw(scene, 'RGBA')

    # Painted sky gradient.
    for y in range(sh):
        t = y / max(1, sh - 1)
        if t < 0.56:
            color = _mix((73, 143, 218), (191, 225, 246), t / 0.56)
        else:
            color = _mix((191, 225, 246), (170, 207, 135), (t - 0.56) / 0.44)
        draw.line((0, y, sw, y), fill=color)

    # Broad painterly cloud shapes.
    cloud_specs = [
        (44, 42, 44, 18),
        (177, 35, 50, 20),
        (225, 66, 34, 14),
    ]
    for cx, cy, rw, rh in cloud_specs:
        cx *= scale; cy *= scale; rw *= scale; rh *= scale
        for dx, dy, sx, sy in [(-0.38, 0.05, 0.70, 0.62), (0, -0.10, 0.86, 0.76), (0.38, 0.04, 0.68, 0.58)]:
            draw.ellipse((cx + dx * rw - sx * rw, cy + dy * rh - sy * rh, cx + dx * rw + sx * rw, cy + dy * rh + sy * rh), fill=(255, 255, 248, 222))

    # Distant blue-green ridges.
    draw.polygon([(0, 150), (52, 103), (91, 135), (132, 78), (178, 130), (221, 100), (256, 145), (256, 190), (0, 190)], fill=(90, 137, 111, 255))
    draw.polygon([(0, 162), (59, 123), (105, 153), (157, 112), (213, 151), (256, 129), (256, 190), (0, 190)], fill=(106, 158, 102, 255))

    # Central mountain and summit flag.
    mountain = [(73, 190), (128, 48), (188, 190)]
    draw.polygon(mountain, fill=(102, 151, 78, 255), outline=(49, 91, 48, 255))
    draw.polygon([(108, 121), (128, 62), (148, 121)], fill=(150, 184, 104, 255))
    draw.polygon([(122, 74), (128, 52), (134, 74)], fill=(224, 222, 183, 255))
    draw.line((128, 48, 128, 28), fill=(74, 56, 37, 255), width=3)
    draw.polygon([(128, 28), (148, 34), (128, 40)], fill=(222, 64, 58, 255), outline=(105, 38, 35, 255))

    # Winding ochre path through the mountain and meadow.
    path = [(111, 256), (149, 256), (143, 224), (155, 203), (144, 184), (151, 162), (137, 142), (142, 119), (132, 99), (126, 76), (121, 101), (127, 126), (117, 148), (126, 170), (113, 193), (121, 216)]
    draw.polygon(path, fill=(221, 184, 101, 255), outline=(151, 112, 57, 255))

    # Foreground rolling meadow.
    draw.ellipse((-74, 150, 198, 337), fill=(89, 158, 69, 255), outline=(53, 105, 46, 255))
    draw.ellipse((91, 151, 335, 335), fill=(101, 169, 76, 255), outline=(53, 105, 46, 255))
    draw.ellipse((42, 191, 268, 364), fill=(117, 180, 82, 255))

    # Floating island and lone tree.
    draw.polygon([(184, 83), (220, 71), (247, 84), (232, 101), (197, 100)], fill=(107, 165, 82, 255), outline=(54, 102, 45, 255))
    draw.polygon([(197, 100), (232, 101), (219, 113), (207, 109)], fill=(105, 82, 55, 255))
    draw.rectangle((215, 49, 221, 78), fill=(100, 66, 42, 255))
    draw.ellipse((198, 27, 239, 65), fill=(64, 133, 67, 255), outline=(42, 88, 44, 255))

    # Fence and cannon silhouette.
    fence_y = 199
    for fx in range(13, 80, 17):
        draw.rectangle((fx, fence_y - 15, fx + 5, fence_y + 15), fill=(102, 72, 42, 255))
    draw.line((13, fence_y - 7, 79, fence_y - 7), fill=(131, 91, 50, 255), width=5)
    draw.line((13, fence_y + 6, 79, fence_y + 6), fill=(131, 91, 50, 255), width=5)
    draw.ellipse((208, 185, 244, 221), fill=(48, 57, 66, 255), outline=(18, 20, 23, 255), width=3)
    draw.polygon([(221, 191), (255, 174), (252, 204)], fill=(63, 73, 82, 255), outline=(18, 20, 23, 255))

    # Characters: a friendly buddy and King Bob-omb make the identity obvious.
    _draw_highres_bobomb(draw, 61, 212, 24, ((171, 43, 53, 255), (232, 88, 92, 255)), (244, 187, 57, 255), (226, 190, 76, 255), buddy=True)
    _draw_highres_bobomb(draw, 188, 216, 32, ((24, 29, 37, 255), (88, 96, 109, 255)), (240, 183, 51, 255), (225, 183, 77, 255), king=True)

    # Chain Chomp silhouette and chain links in the middle distance.
    draw.ellipse((14, 140, 55, 181), fill=(27, 33, 41, 255), outline=(9, 11, 14, 255), width=3)
    draw.ellipse((23, 150, 28, 158), fill=(245, 245, 240, 255))
    draw.ellipse((39, 150, 44, 158), fill=(245, 245, 240, 255))
    for i in range(5):
        x = 52 + i * 10
        y = 174 + (i % 2) * 3
        draw.ellipse((x, y, x + 8, y + 6), outline=(171, 177, 181, 255), width=2)

    # Flowers and blades create readable course texture without overwhelming the portrait.
    for _ in range(52):
        x = int(rng.randint(0, sw))
        y = int(rng.randint(172, sh))
        draw.line((x, y + 7, x + int(rng.randint(-2, 3)), y), fill=(55, 121, 48, 210), width=1)
        if rng.rand() < 0.34:
            petal = (255, 244, 218, 255) if rng.rand() < 0.7 else (252, 210, 68, 255)
            draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=petal)
            draw.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(212, 146, 45, 255))

    # Thin painted border, useful when the texture warps in the ripple mesh.
    draw.rectangle((2, 2, sw - 3, sh - 3), outline=(55, 76, 49, 180), width=3)

    # Downsample with antialiasing into the actual 64x64 painting.
    return scene.resize((size, size), Image.Resampling.LANCZOS)


def _render_castle_portrait_full(scene_key: str):
    if scene_key == 'bobomb_battlefield':
        return _render_bobomb_battlefield_portrait_full()
    return _render_generic_castle_portrait_full(scene_key)


def _render_castle_portrait_rgba(fname: str, shape):
    key = fname.lower()
    if key not in _CASTLE_PORTRAIT_LAYOUTS:
        raise KeyError(f'unsupported castle portrait: {fname}')
    scene_key, segment = _CASTLE_PORTRAIT_LAYOUTS[key]
    full = _render_castle_portrait_full(scene_key)
    if segment == 'top':
        crop = full.crop((0, 0, 64, 32))
    elif segment == 'bottom':
        crop = full.crop((0, 32, 64, 64))
    elif segment == 'full':
        crop = full
    else:
        raise KeyError(segment)
    if crop.size != (int(shape[1]), int(shape[0])):
        crop = crop.resize((int(shape[1]), int(shape[0])), Image.Resampling.LANCZOS)
    return np.asarray(crop, dtype=np.uint8)


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

    if intent.role == 'portrait':
        rgba = _render_castle_portrait_rgba(fname, (h, w, 4))
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
