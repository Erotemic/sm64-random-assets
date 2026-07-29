from __future__ import annotations

import math
import re
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw


# These actor families have multiple semantically named textures that previously
# fell through to a small set of generic material renderers.  Claim the complete
# family so every part is rendered coherently while still looking unlike its
# neighbors.
DIFFERENTIATED_ACTOR_FAMILIES = frozenset({
    'amp',
    'bobomb',
    'bookend',
    'bully',
    'chain_chomp',
    'chillychief',
    'dorrie',
    'eyerok',
    'flyguy',
    'haunted_cage',
    'heave_ho',
    'king_bobomb',
    'klepto',
    'koopa',
    'lakitu_cameraman',
    'lakitu_enemy',
    'mad_piano',
    'monty_mole',
    'penguin',
    'piranha_plant',
    'scuttlebug',
    'seaweed',
    'snowman',
    'spindrift',
    'treasure_chest',
    'ukiki',
    'unagi',
    'whomp',
    'wiggler',
    'yoshi',
})

# These are frame sequences where filename-aware phase changes are more useful
# than rendering the same generic sprite repeatedly.
DIFFERENTIATED_ANIMATION_FAMILIES = frozenset({
    'explosion',
    'flame',
    'impact_smoke',
    'stomp_smoke',
    'walk_smoke',
    'water_wave',
    'yoshi_egg',
})


@dataclass(frozen=True)
class FamilyStyle:
    primary: tuple[int, int, int]
    secondary: tuple[int, int, int]
    accent: tuple[int, int, int]
    dark: tuple[int, int, int]
    surface: str


FAMILY_STYLES = {
    'amp': FamilyStyle((61, 69, 92), (100, 112, 145), (244, 215, 54), (27, 29, 42), 'metal'),
    'bobomb': FamilyStyle((29, 35, 45), (69, 83, 101), (241, 205, 83), (8, 11, 16), 'metal'),
    'king_bobomb': FamilyStyle((38, 44, 60), (87, 101, 124), (238, 190, 58), (10, 14, 21), 'metal'),
    'bookend': FamilyStyle((89, 34, 27), (151, 69, 42), (226, 194, 126), (47, 21, 20), 'book'),
    'bully': FamilyStyle((44, 48, 55), (86, 91, 101), (235, 177, 52), (15, 17, 22), 'metal'),
    'chillychief': FamilyStyle((100, 155, 202), (169, 214, 238), (237, 247, 250), (37, 77, 116), 'ice'),
    'chain_chomp': FamilyStyle((27, 31, 38), (78, 86, 98), (244, 239, 213), (5, 7, 10), 'metal'),
    'dorrie': FamilyStyle((75, 131, 185), (114, 174, 217), (240, 178, 87), (29, 67, 105), 'scales'),
    'eyerok': FamilyStyle((139, 104, 66), (183, 146, 98), (70, 169, 212), (74, 51, 34), 'stone'),
    'flyguy': FamilyStyle((177, 41, 45), (225, 78, 72), (238, 211, 140), (76, 22, 25), 'fabric'),
    'haunted_cage': FamilyStyle((84, 69, 58), (137, 111, 79), (178, 151, 97), (42, 35, 32), 'wood_metal'),
    'heave_ho': FamilyStyle((45, 86, 118), (83, 138, 169), (232, 188, 52), (25, 46, 61), 'machine'),
    'klepto': FamilyStyle((45, 42, 54), (92, 80, 101), (232, 172, 57), (18, 18, 24), 'feather'),
    'koopa': FamilyStyle((71, 148, 66), (126, 189, 82), (238, 203, 92), (31, 78, 34), 'scales'),
    'lakitu_cameraman': FamilyStyle((91, 153, 61), (145, 196, 82), (239, 206, 83), (42, 86, 37), 'scales'),
    'lakitu_enemy': FamilyStyle((108, 157, 60), (159, 198, 83), (232, 184, 58), (52, 87, 38), 'scales'),
    'mad_piano': FamilyStyle((94, 48, 33), (154, 88, 48), (236, 219, 174), (42, 22, 18), 'wood'),
    'monty_mole': FamilyStyle((91, 62, 43), (145, 99, 62), (233, 190, 131), (48, 31, 24), 'fur'),
    'penguin': FamilyStyle((35, 45, 58), (74, 92, 109), (236, 177, 48), (12, 17, 24), 'feather'),
    'piranha_plant': FamilyStyle((173, 38, 43), (229, 74, 73), (84, 161, 65), (76, 22, 29), 'plant'),
    'scuttlebug': FamilyStyle((75, 55, 111), (131, 87, 153), (232, 162, 60), (38, 28, 59), 'chitin'),
    'seaweed': FamilyStyle((39, 105, 65), (71, 151, 91), (167, 210, 103), (20, 61, 38), 'plant'),
    'snowman': FamilyStyle((220, 232, 240), (247, 250, 251), (75, 127, 181), (104, 123, 140), 'snow'),
    'spindrift': FamilyStyle((74, 151, 67), (133, 197, 91), (238, 123, 169), (34, 91, 37), 'plant'),
    'treasure_chest': FamilyStyle((115, 68, 37), (177, 111, 54), (224, 183, 72), (61, 36, 25), 'wood_metal'),
    'ukiki': FamilyStyle((99, 65, 44), (154, 105, 70), (232, 181, 127), (47, 31, 25), 'fur'),
    'unagi': FamilyStyle((57, 104, 128), (91, 157, 177), (227, 187, 98), (28, 57, 73), 'scales'),
    'whomp': FamilyStyle((118, 112, 103), (160, 153, 139), (224, 205, 157), (69, 66, 64), 'stone'),
    'wiggler': FamilyStyle((235, 180, 48), (250, 215, 80), (210, 58, 45), (137, 91, 24), 'segments'),
    'yoshi': FamilyStyle((61, 157, 75), (110, 196, 94), (240, 190, 85), (25, 83, 40), 'scales'),
}


def actor_family_from_fname(fname: str) -> str | None:
    if not fname.startswith('actors/'):
        return None
    parts = fname.split('/', 2)
    if len(parts) < 3:
        return None
    return parts[1]


def supports_differentiated_texture(identity, info) -> bool:
    family = actor_family_from_fname(identity.fname)
    return family in DIFFERENTIATED_ACTOR_FAMILIES or family in DIFFERENTIATED_ANIMATION_FAMILIES


def _stable_seed(text: str) -> int:
    import hashlib
    return int(hashlib.sha256(text.encode('utf8')).hexdigest()[:16], 16) & 0x7FFFFFFF


def _local_rng(rng, fname: str):
    if rng is None:
        return np.random.RandomState(_stable_seed(fname))
    return np.random.RandomState(int(rng.randint(0, 2 ** 31 - 1)) ^ _stable_seed(fname))


def _canvas(shape, scale=4, background=(0, 0, 0, 0)):
    h, w = int(shape[0]), int(shape[1])
    img = Image.new('RGBA', (w * scale, h * scale), background)
    return img, ImageDraw.Draw(img, 'RGBA'), scale


def _finish(img: Image.Image, shape):
    h, w = int(shape[0]), int(shape[1])
    img = img.resize((w, h), Image.Resampling.LANCZOS)
    rgba = np.asarray(img, dtype=np.uint8)
    channels = int(shape[2]) if len(shape) == 3 else 1
    if channels == 4:
        return rgba
    if channels == 3:
        return rgba[..., :3]
    intensity = np.clip(
        0.299 * rgba[..., 0] + 0.587 * rgba[..., 1] + 0.114 * rgba[..., 2],
        0,
        255,
    ).astype(np.uint8)
    if channels == 2:
        return np.stack([intensity, rgba[..., 3]], axis=2)
    return intensity


def _mix(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def _gradient(draw, w, h, top, bottom, alpha=255):
    for y in range(h):
        t = y / max(1, h - 1)
        c = _mix(top, bottom, t) + (alpha,)
        draw.line((0, y, w, y), fill=c)


def _frame_index(fname: str) -> int:
    match = re.search(r'_(\d+)(?:_unused)?\.', fname)
    return int(match.group(1)) if match else 0


def _material_background(draw, w, h, s, style: FamilyStyle, rng, role: str):
    _gradient(draw, w, h, style.secondary, style.primary)
    if style.surface in {'metal', 'machine'}:
        for x in range(-h, w + h, max(4 * s, w // 7)):
            draw.line((x, 0, x + h, h), fill=style.accent + (45,), width=max(1, s))
        for y in range(max(4 * s, h // 4), h, max(6 * s, h // 3)):
            draw.line((0, y, w, y), fill=style.dark + (110,), width=max(1, s))
    elif style.surface == 'stone':
        for _ in range(max(6, w * h // (180 * s * s))):
            x = int(rng.randint(0, w))
            y = int(rng.randint(0, h))
            rx = int(rng.randint(max(2 * s, w // 12), max(3 * s, w // 5)))
            ry = int(rng.randint(max(2 * s, h // 14), max(3 * s, h // 6)))
            draw.ellipse((x-rx, y-ry, x+rx, y+ry), fill=style.secondary + (100,), outline=style.dark + (100,))
    elif style.surface in {'wood', 'wood_metal', 'book'}:
        spacing = max(5 * s, h // 4)
        for y in range(0, h, spacing):
            draw.line((0, y, w, y), fill=style.dark + (180,), width=max(1, s))
        for _ in range(max(5, w // max(2 * s, 1))):
            y = int(rng.randint(0, h))
            x = int(rng.randint(0, w))
            draw.arc((x-w//5, y-2*s, x+w//3, y+2*s), 185, 355, fill=style.accent + (55,), width=max(1, s))
    elif style.surface in {'scales', 'chitin', 'segments'}:
        r = max(3 * s, min(w, h) // 9)
        row = 0
        for y in range(-r, h + r, max(2 * s, int(r * 1.45))):
            offset = r if row % 2 else 0
            for x in range(-r + offset, w + r, max(3 * s, r * 2)):
                draw.arc((x-r, y-r, x+r, y+r), 10, 170, fill=style.accent + (90,), width=max(1, s))
            row += 1
    elif style.surface in {'fur', 'feather'}:
        for _ in range(max(18, w * h // (90 * s * s))):
            x = int(rng.randint(0, w))
            y = int(rng.randint(0, h))
            length = int(rng.randint(2 * s, max(2 * s + 1, 6 * s)))
            lean = int(rng.randint(-2 * s, 2 * s + 1))
            draw.line((x, y, x + lean, min(h, y + length)), fill=style.accent + (80,), width=max(1, s))
    elif style.surface in {'plant'}:
        for _ in range(max(10, w * h // (130 * s * s))):
            x = int(rng.randint(0, w))
            y = int(rng.randint(0, h))
            rx = int(rng.randint(2 * s, max(2 * s + 1, 5 * s)))
            draw.ellipse((x-rx, y-rx//2, x+rx, y+rx//2), fill=style.secondary + (110,))
    elif style.surface in {'ice', 'snow'}:
        for _ in range(max(8, w * h // (150 * s * s))):
            x = int(rng.randint(0, w))
            y = int(rng.randint(0, h))
            r = int(rng.randint(max(1, s), max(2, 3 * s)))
            draw.ellipse((x-r, y-r, x+r, y+r), fill=(255, 255, 255, 90))

    # A role-specific band prevents same-palette body parts from collapsing into
    # visually identical swatches.
    role_seed = _stable_seed(role)
    band_y = int((0.18 + (role_seed % 5) * 0.13) * h)
    draw.line((0, band_y, w, band_y), fill=style.accent + (45,), width=max(1, s))


def _eye_texture(draw, w, h, s, style, low):
    _gradient(draw, w, h, style.primary, style.secondary)
    fully_closed = ('closed' in low and 'mostly_closed' not in low and 'half_closed' not in low) or 'blink' in low
    mostly_closed = 'mostly_closed' in low
    half_closed = 'half_closed' in low
    mostly_open = 'mostly_open' in low
    angry = 'angry' in low or 'frown' in low
    if fully_closed:
        open_amount = 0.10
    elif mostly_closed:
        open_amount = 0.24
    elif half_closed:
        open_amount = 0.32
    elif mostly_open:
        open_amount = 0.47
    else:
        open_amount = 0.58
    cx, cy = w * 0.5, h * 0.52
    rx, ry = w * 0.28, h * open_amount * 0.42
    if 'border' in low:
        draw.ellipse((cx-rx, cy-h*0.22, cx+rx, cy+h*0.22), fill=style.dark + (255,))
        draw.ellipse((cx-rx*0.72, cy-h*0.15, cx+rx*0.72, cy+h*0.15), fill=style.primary + (255,))
        return
    if 'iris' in low and 'eye' not in low.rsplit('/', 1)[-1].replace('eyerok_', ''):
        rr = min(w, h) * 0.31
        draw.ellipse((cx-rr, cy-rr, cx+rr, cy+rr), fill=style.accent + (255,), outline=style.dark + (255,), width=max(1, s))
        pupil = rr * 0.40
        draw.ellipse((cx-pupil, cy-pupil, cx+pupil, cy+pupil), fill=style.dark + (255,))
        draw.ellipse((cx-pupil*0.45, cy-pupil*0.72, cx, cy-pupil*0.18), fill=(255,255,255,220))
        return
    if fully_closed:
        draw.arc((cx-rx, cy-h*0.10, cx+rx, cy+h*0.10), 5, 175, fill=style.dark + (255,), width=max(2, 2*s))
    else:
        draw.ellipse((cx-rx, cy-ry, cx+rx, cy+ry), fill=(246, 244, 226, 255), outline=style.dark + (255,), width=max(1, s))
        look = 0.0
        if 'left' in low:
            look = -0.22
        elif 'right' in low:
            look = 0.22
        iris_x = cx + look * rx
        iris_r = min(rx, max(2*s, ry * 0.70))
        iris_color = style.accent
        draw.ellipse((iris_x-iris_r, cy-iris_r, iris_x+iris_r, cy+iris_r), fill=iris_color + (255,), outline=style.dark + (255,))
        pupil = max(1, int(iris_r * 0.42))
        draw.ellipse((iris_x-pupil, cy-pupil, iris_x+pupil, cy+pupil), fill=style.dark + (255,))
        draw.ellipse((iris_x-pupil*0.55, cy-pupil*0.75, iris_x, cy-pupil*0.20), fill=(255, 255, 255, 220))
    if angry:
        draw.line((w*0.18, h*0.25, w*0.52, h*0.35), fill=style.dark + (255,), width=max(2, 2*s))
        draw.line((w*0.82, h*0.25, w*0.48, h*0.35), fill=style.dark + (255,), width=max(2, 2*s))
    if 'unused' in low:
        # Keep alternate/unused states visually distinct instead of byte-identical.
        draw.arc((w*0.10, h*0.08, w*0.42, h*0.34), 190, 330, fill=style.accent + (120,), width=max(1, s))


def _mouth_texture(draw, w, h, s, style, low):
    _gradient(draw, w, h, style.primary, style.secondary)
    if 'nostril' in low or 'nose' in low or 'snout' in low or 'muzzle' in low or 'cheek' in low:
        skin = _mix(style.accent, (236, 178, 119), 0.45)
        draw.ellipse((w*0.18, h*0.22, w*0.82, h*0.84), fill=skin + (255,), outline=style.dark + (255,), width=max(1, s))
        if 'nostril' in low or 'nose' in low or 'snout' in low:
            for x in (w*0.40, w*0.60):
                draw.ellipse((x-2*s, h*0.52-2*s, x+2*s, h*0.52+2*s), fill=style.dark + (255,))
    else:
        draw.ellipse((w*0.12, h*0.25, w*0.88, h*0.78), fill=style.dark + (255,), outline=style.accent + (255,), width=max(1, s))
        if 'frown' in low:
            draw.arc((w*0.23, h*0.48, w*0.77, h*0.85), 200, 340, fill=(231, 183, 150, 255), width=max(1, 2*s))
        elif 'tongue' in low:
            draw.ellipse((w*0.26, h*0.46, w*0.74, h*0.88), fill=(212, 78, 103, 255), outline=(111, 39, 56, 255))
            draw.line((w*0.5, h*0.55, w*0.5, h*0.82), fill=(147, 49, 70, 190), width=max(1, s))
        else:
            draw.arc((w*0.22, h*0.30, w*0.78, h*0.75), 15, 165, fill=(234, 173, 143, 255), width=max(1, 2*s))


def _ivory_texture(draw, w, h, s, style, low):
    _gradient(draw, w, h, (251, 241, 203), (193, 161, 105))
    if 'tooth' in low or 'claw' in low or 'horn' in low or 'beak' in low:
        draw.polygon([(w*0.12, h*0.16), (w*0.88, h*0.42), (w*0.16, h*0.88)], fill=(241, 224, 170, 255), outline=style.dark + (255,))
        draw.line((w*0.20, h*0.27, w*0.72, h*0.43), fill=(255, 252, 224, 180), width=max(1, s))


def _leaf_texture(draw, w, h, s, style, low):
    # Transparent outside the leaf silhouette.
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
    if 'stem' in low or 'seaweed' in low or 'center' in low or 'base' in low or 'tip' in low:
        pts = []
        for i in range(12):
            t = i / 11
            x = w * (0.50 + 0.14 * math.sin(t * math.pi * 2.0 + (_stable_seed(low) % 7)))
            y = h * (0.95 - t * 0.88)
            pts.append((x, y))
        draw.line(pts, fill=style.secondary + (255,), width=max(2*s, w//7))
        draw.line(pts, fill=style.accent + (145,), width=max(1, s))
    elif 'petal' in low or 'flower' in low:
        cx, cy = w/2, h/2
        for i in range(8):
            ang = i * math.tau / 8
            px = cx + math.cos(ang) * w * 0.20
            py = cy + math.sin(ang) * h * 0.20
            draw.ellipse((px-w*0.16, py-h*0.12, px+w*0.16, py+h*0.12), fill=style.accent + (240,), outline=style.dark + (130,))
        draw.ellipse((cx-w*0.10, cy-h*0.10, cx+w*0.10, cy+h*0.10), fill=(232, 180, 48, 255))
    else:
        draw.ellipse((w*0.08, h*0.22, w*0.92, h*0.78), fill=style.secondary + (245,), outline=style.dark + (255,), width=max(1, s))
        draw.line((w*0.12, h*0.72, w*0.88, h*0.28), fill=style.accent + (210,), width=max(1, 2*s))
        for t in (0.28, 0.44, 0.60, 0.76):
            x = w*(0.12 + 0.76*t)
            y = h*(0.72 - 0.44*t)
            draw.line((x, y, x-w*0.16, y-h*0.14), fill=style.accent + (130,), width=max(1, s))
            draw.line((x, y, x+w*0.12, y+h*0.13), fill=style.accent + (130,), width=max(1, s))


def _shell_texture(draw, w, h, s, style, low):
    _gradient(draw, w, h, style.primary, style.secondary)
    if 'front' in low:
        draw.ellipse((w*0.12, h*0.10, w*0.88, h*0.90), fill=style.secondary + (255,), outline=style.dark + (255,), width=max(1, 2*s))
        draw.ellipse((w*0.28, h*0.24, w*0.72, h*0.76), fill=style.accent + (170,), outline=style.dark + (170,))
        if 'top' in low:
            draw.arc((w*0.18, h*0.03, w*0.82, h*0.55), 190, 350, fill=(255, 255, 220, 180), width=max(1, 2*s))
    else:
        cells = 4
        cw = w / cells
        ch = h / cells
        for row in range(cells):
            for col in range(cells):
                x0, y0 = col*cw, row*ch
                fill = style.primary if (row+col)%2 else style.secondary
                draw.rounded_rectangle((x0+s, y0+s, x0+cw-s, y0+ch-s), radius=max(1, 2*s), fill=fill+(255,), outline=style.dark+(180,))


def _mechanical_part(draw, w, h, s, style, low):
    _material_background(draw, w, h, s, style, np.random.RandomState(_stable_seed(low)), low)
    if 'lens' in low:
        for frac, color in [(0.42, style.dark), (0.32, (40, 93, 145)), (0.20, (76, 170, 218)), (0.08, (230, 247, 255))]:
            r = min(w, h) * frac
            draw.ellipse((w/2-r, h/2-r, w/2+r, h/2+r), fill=color+(255,))
    elif 'roller' in low:
        draw.rounded_rectangle((w*0.08, h*0.25, w*0.92, h*0.75), radius=max(2*s, h//5), fill=style.dark+(255,), outline=style.accent+(255,), width=max(1, s))
        for x in range(int(w*0.18), int(w*0.90), max(3*s, w//6)):
            draw.line((x, h*0.28, x, h*0.72), fill=style.secondary+(180,), width=max(1, s))
    elif 'turnkey' in low:
        draw.ellipse((w*0.34, h*0.35, w*0.66, h*0.67), fill=style.accent+(255,), outline=style.dark+(255,))
        draw.rectangle((w*0.45, h*0.08, w*0.55, h*0.92), fill=style.accent+(255,))
        draw.rectangle((w*0.12, h*0.14, w*0.88, h*0.30), fill=style.accent+(255,))
    elif 'electricity' in low:
        draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
        pts = [(0, h*0.55), (w*0.22, h*0.35), (w*0.38, h*0.62), (w*0.57, h*0.24), (w*0.72, h*0.54), (w, h*0.30)]
        draw.line(pts, fill=style.accent+(255,), width=max(2, 3*s))
        draw.line(pts, fill=(255, 252, 184, 255), width=max(1, s))
    elif 'propeller' in low:
        draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
        cx, cy = w/2, h/2
        for ang in (0, math.pi/2):
            dx, dy = math.cos(ang)*w*0.38, math.sin(ang)*h*0.38
            px, py = -math.sin(ang)*w*0.08, math.cos(ang)*h*0.08
            draw.polygon([(cx+px, cy+py), (cx+dx+px, cy+dy+py), (cx+dx-px, cy+dy-py), (cx-px, cy-py)], fill=style.secondary+(230,), outline=style.dark+(255,))
        draw.ellipse((cx-3*s, cy-3*s, cx+3*s, cy+3*s), fill=style.accent+(255,))
    elif 'logo' in low:
        draw.ellipse((w*0.18, h*0.18, w*0.82, h*0.82), fill=style.accent+(255,), outline=style.dark+(255,), width=max(1, 2*s))
        draw.polygon([(w*0.50, h*0.28), (w*0.62, h*0.65), (w*0.37, h*0.65)], fill=style.dark+(255,))


def _bars_or_lock(draw, w, h, s, style, low):
    if 'bars' in low:
        draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
        for x in range(2*s, w, max(5*s, w//6)):
            draw.rectangle((x, 0, min(w-1, x+2*s), h), fill=style.secondary+(245,))
            draw.line((x, 0, x, h), fill=style.accent+(180,), width=max(1, s))
        for y in (h*0.28, h*0.72):
            draw.rectangle((0, y-s, w, y+s), fill=style.secondary+(245,))
    elif 'lock' in low:
        _gradient(draw, w, h, style.primary, style.dark)
        draw.rounded_rectangle((w*0.22, h*0.38, w*0.78, h*0.86), radius=max(2*s, w//10), fill=style.accent+(255,), outline=style.dark+(255,), width=max(1, 2*s))
        draw.arc((w*0.30, h*0.08, w*0.70, h*0.60), 180, 360, fill=style.accent+(255,), width=max(2, 3*s))
        draw.ellipse((w*0.46, h*0.56, w*0.54, h*0.68), fill=style.dark+(255,))
        draw.rectangle((w*0.485, h*0.64, w*0.515, h*0.78), fill=style.dark+(255,))


def _piano_or_book(draw, w, h, s, style, low, rng):
    if 'key' in low:
        draw.rectangle((0, 0, w, h), fill=(242, 234, 207, 255))
        key_count = max(4, w // max(4*s, 1))
        kw = w / key_count
        for i in range(key_count):
            x = i * kw
            draw.rectangle((x, 0, x+kw, h), outline=style.dark+(255,), width=max(1, s))
        for i in range(key_count-1):
            if i % 3 != 2:
                x = (i+0.68)*kw
                draw.rectangle((x, 0, x+kw*0.44, h*0.58), fill=style.dark+(255,))
        if 'corner' in low:
            draw.rectangle((0, 0, w*0.18, h), fill=style.secondary+(255,))
        elif 'edge' in low:
            draw.line((0, h-2*s, w, h-2*s), fill=style.accent+(255,), width=max(1, 2*s))
    elif 'pages' in low:
        draw.rectangle((0, 0, w, h), fill=(235, 220, 175, 255))
        for y in range(2*s, h, max(2*s, h//7)):
            draw.line((0, y, w, y), fill=(149, 127, 91, 110), width=max(1, s))
    elif 'spine' in low:
        _gradient(draw, w, h, style.primary, style.dark)
        for x in (w*0.25, w*0.75):
            draw.line((x, 0, x, h), fill=style.accent+(180,), width=max(1, 2*s))
    elif 'cover' in low:
        _gradient(draw, w, h, style.secondary, style.primary)
        draw.rectangle((w*0.10, h*0.10, w*0.90, h*0.90), outline=style.accent+(255,), width=max(1, 2*s))
        draw.ellipse((w*0.36, h*0.31, w*0.64, h*0.69), outline=style.accent+(200,), width=max(1, s))
    else:
        _material_background(draw, w, h, s, style, rng, low)


def _render_actor(fname, shape, rng):
    family = actor_family_from_fname(fname)
    style = FAMILY_STYLES[family]
    low = fname.lower()
    base = low.rsplit('/', 1)[-1]
    part = base.split('.', 1)[0]
    family_prefix = family + '_'
    if part.startswith(family_prefix):
        part = part[len(family_prefix):]
    img, draw, s = _canvas(shape, scale=4, background=style.primary + (255,))
    w, h = img.size

    is_eye_part = (
        part.startswith(('eye', 'eyes', 'iris'))
        or '_eye' in part
        or '_eyes' in part
        or '_iris' in part
        or part.endswith(('eye', 'eyes', 'iris'))
    )
    if is_eye_part:
        _eye_texture(draw, w, h, s, style, low)
    elif 'face_blink' in part:
        _mouth_texture(draw, w, h, s, style, low)
        draw.arc((w*0.18, h*0.25, w*0.46, h*0.42), 5, 175, fill=style.dark + (255,), width=max(1, 2*s))
        draw.arc((w*0.54, h*0.25, w*0.82, h*0.42), 5, 175, fill=style.dark + (255,), width=max(1, 2*s))
    elif any(token in part for token in ('mouth', 'frown', 'tongue', 'nostril', 'nose', 'snout', 'muzzle', 'cheek', 'face')):
        _mouth_texture(draw, w, h, s, style, low)
    elif any(token in part for token in ('tooth', 'claw', 'horn', 'beak')):
        _ivory_texture(draw, w, h, s, style, low)
    elif any(token in part for token in ('leaf', 'stem', 'petal', 'flower')) or family == 'seaweed':
        _leaf_texture(draw, w, h, s, style, low)
    elif 'shell' in part:
        _shell_texture(draw, w, h, s, style, low)
    elif any(token in part for token in ('lens', 'roller', 'turnkey', 'electricity', 'propeller', 'logo')):
        _mechanical_part(draw, w, h, s, style, low)
    elif any(token in part for token in ('bars', 'lock')):
        _bars_or_lock(draw, w, h, s, style, low)
    elif family in {'mad_piano', 'bookend'}:
        _piano_or_book(draw, w, h, s, style, low, rng)
    else:
        _material_background(draw, w, h, s, style, rng, part)
        if 'shoe' in part or 'mitten' in part or 'hand' in part or 'arm' in part or 'leg' in part:
            draw.rounded_rectangle((w*0.16, h*0.24, w*0.84, h*0.80), radius=max(3*s, min(w,h)//6), fill=style.accent+(190,), outline=style.dark+(255,), width=max(1, s))
        if 'wing' in part or 'fin' in part:
            draw.polygon([(w*0.08, h*0.70), (w*0.48, h*0.12), (w*0.92, h*0.65), (w*0.56, h*0.88)], fill=style.secondary+(220,), outline=style.dark+(255,))
            for t in (0.30, 0.48, 0.66):
                draw.line((w*0.22, h*0.70, w*t, h*0.28), fill=style.accent+(130,), width=max(1, s))
        if 'crown' in part:
            draw.polygon([(w*0.12,h*0.78),(w*0.18,h*0.18),(w*0.38,h*0.48),(w*0.50,h*0.08),(w*0.62,h*0.48),(w*0.82,h*0.18),(w*0.88,h*0.78)], fill=style.accent+(255,), outline=style.dark+(255,))
        if 'sunglasses' in part:
            draw.rounded_rectangle((w*0.08,h*0.30,w*0.45,h*0.72), radius=max(2*s,w//12), fill=(20,24,31,255), outline=style.accent+(255,))
            draw.rounded_rectangle((w*0.55,h*0.30,w*0.92,h*0.72), radius=max(2*s,w//12), fill=(20,24,31,255), outline=style.accent+(255,))
            draw.line((w*0.45,h*0.46,w*0.55,h*0.46), fill=style.dark+(255,), width=max(1,2*s))

    if 'left_side' in low:
        draw.rectangle((0, 0, max(1, w//7), h), fill=(255, 255, 255, 38))
        draw.rectangle((w-max(1, w//8), 0, w, h), fill=style.dark + (50,))
    elif 'right_side' in low:
        draw.rectangle((0, 0, max(1, w//8), h), fill=style.dark + (50,))
        draw.rectangle((w-max(1, w//7), 0, w, h), fill=(255, 255, 255, 38))
    if 'bob-omb_buddy' in low:
        draw.line((0, h*0.22, w, h*0.22), fill=(76, 149, 220, 120), width=max(1, 2*s))
    elif 'king_bob-omb_body' in low:
        draw.polygon([(w*0.50,h*0.12),(w*0.62,h*0.30),(w*0.50,h*0.48),(w*0.38,h*0.30)], fill=style.accent+(120,))

    # Filename-specific asymmetric mark keeps left/right and adjacent materials
    # distinguishable without depending on source artwork.
    mark = _stable_seed(part) % 4
    if not any(token in part for token in ('eye', 'iris', 'bars', 'electricity', 'propeller', 'leaf', 'stem', 'petal', 'flower')):
        if mark == 0:
            draw.arc((w*0.05, h*0.05, w*0.55, h*0.55), 195, 305, fill=(255,255,255,45), width=max(1,s))
        elif mark == 1:
            draw.line((w*0.08,h*0.82,w*0.92,h*0.18), fill=style.accent+(45,), width=max(1,s))
        elif mark == 2:
            draw.ellipse((w*0.72,h*0.12,w*0.86,h*0.26), fill=style.accent+(70,))
        else:
            draw.line((w*0.10,h*0.18,w*0.90,h*0.18), fill=style.accent+(55,), width=max(1,s))

    return _finish(img, shape)


def _render_flame(fname, shape, rng):
    idx = _frame_index(fname)
    img, draw, s = _canvas(shape, scale=4)
    w, h = img.size
    phase = idx / 8.0
    lobes = 7
    outer = []
    for i in range(lobes * 2 + 1):
        t = i / (lobes * 2)
        x = w * (0.08 + 0.84 * t)
        wave = math.sin(t * math.pi * lobes + phase * math.tau)
        y = h * (0.86 - (0.58 + 0.08 * wave) * math.sin(t * math.pi))
        outer.append((x, y))
    outer += [(w*0.92,h*0.92),(w*0.08,h*0.92)]
    draw.polygon(outer, fill=(231, 73, 20, 235))
    inner = [(w*0.26,h*0.82),(w*(0.40+0.06*math.sin(phase*math.tau)),h*0.36),(w*0.52,h*0.72),(w*(0.65+0.04*math.cos(phase*math.tau)),h*0.46),(w*0.76,h*0.84)]
    draw.polygon(inner, fill=(255, 188, 44, 245))
    draw.ellipse((w*0.39,h*0.62,w*0.61,h*0.90), fill=(255, 239, 154, 220))
    return _finish(img, shape)


def _render_explosion(fname, shape, rng):
    idx = _frame_index(fname)
    img, draw, s = _canvas(shape, scale=4)
    w, h = img.size
    cx, cy = w/2, h/2
    progress = idx / 6.0
    radius = min(w,h) * (0.14 + 0.36 * math.sin(progress * math.pi * 0.78 + 0.10))
    points = []
    spikes = 14
    for i in range(spikes*2):
        ang = i * math.pi / spikes + idx * 0.17
        rr = radius * (1.0 if i%2==0 else 0.52)
        points.append((cx+math.cos(ang)*rr, cy+math.sin(ang)*rr))
    alpha = int(255 * (1.0 - 0.42*progress))
    draw.polygon(points, fill=(239, 75, 24, alpha))
    draw.ellipse((cx-radius*0.58,cy-radius*0.58,cx+radius*0.58,cy+radius*0.58), fill=(255, 188, 47, min(255,alpha+15)))
    draw.ellipse((cx-radius*0.25,cy-radius*0.25,cx+radius*0.25,cy+radius*0.25), fill=(255, 246, 176, min(255,alpha+25)))
    if progress > 0.45:
        for i in range(7):
            ang = i * math.tau / 7 + idx*0.31
            r = radius*(0.8+0.55*progress)
            pr = max(2*s, int(radius*0.12*(1-progress*0.4)))
            x,y = cx+math.cos(ang)*r, cy+math.sin(ang)*r
            draw.ellipse((x-pr,y-pr,x+pr,y+pr), fill=(99,78,68,int(150*(1-progress)+50)))
    return _finish(img, shape)


def _render_smoke(fname, shape, rng):
    idx = _frame_index(fname)
    img, draw, s = _canvas(shape, scale=4)
    w, h = img.size
    family = actor_family_from_fname(fname)
    max_frame = {'walk_smoke': 6, 'stomp_smoke': 5, 'impact_smoke': 3}[family]
    progress = idx / max(1, max_frame)
    count = 5 + idx
    base_alpha = int(225 * (1-progress*0.70))
    for i in range(count):
        ang = i * math.tau / count + idx * 0.23
        ring = min(w,h) * (0.08 + progress*0.28)
        x = w/2 + math.cos(ang)*ring
        y = h/2 + math.sin(ang)*ring*0.65 - progress*h*0.06
        rr = min(w,h)*(0.14 + progress*0.06) * (0.78 + 0.25*math.sin(i*1.7))
        tone = 205 + int(25*(i%2))
        draw.ellipse((x-rr,y-rr,x+rr,y+rr), fill=(tone,tone,tone,base_alpha))
    return _finish(img, shape)


def _render_water_wave(fname, shape, rng):
    idx = _frame_index(fname)
    img, draw, s = _canvas(shape, scale=4)
    w, h = img.size
    progress = idx / 3.0
    cx, cy = w/2, h/2
    for ring_idx in range(2):
        rx = w*(0.16 + progress*0.22 + ring_idx*0.14)
        ry = h*(0.07 + progress*0.10 + ring_idx*0.06)
        alpha = int(220 - progress*100 - ring_idx*45)
        draw.ellipse((cx-rx,cy-ry,cx+rx,cy+ry), outline=(148,221,251,max(40,alpha)), width=max(1,2*s))
    for i in range(5):
        x = w*(0.18+i*0.16)
        y = cy + math.sin(i*1.4+idx)*h*0.05
        draw.ellipse((x-2*s,y-2*s,x+2*s,y+2*s), fill=(225,248,255,int(170-progress*80)))
    return _finish(img, shape)


def _render_yoshi_egg(fname, shape, rng):
    idx = _frame_index(fname)
    img, draw, s = _canvas(shape, scale=4, background=(237, 239, 216, 255))
    w, h = img.size
    _gradient(draw, w, h, (251, 250, 231), (216, 222, 194))
    angle = idx * math.tau / 8.0
    spot_centers = [
        (0.50 + 0.26*math.cos(angle), 0.48 + 0.18*math.sin(angle)),
        (0.50 + 0.24*math.cos(angle+2.1), 0.50 + 0.20*math.sin(angle+2.1)),
        (0.50 + 0.22*math.cos(angle+4.2), 0.52 + 0.17*math.sin(angle+4.2)),
    ]
    for i,(px,py) in enumerate(spot_centers):
        rx=w*(0.12+0.025*i); ry=h*(0.15-0.015*i)
        draw.ellipse((w*px-rx,h*py-ry,w*px+rx,h*py+ry), fill=(72,169,70,255), outline=(33,101,42,180))
    draw.arc((w*0.12,h*0.10,w*0.72,h*0.72), 205, 300, fill=(255,255,255,185), width=max(1,2*s))
    return _finish(img, shape)


def render_differentiated_texture(fname: str, shape, rng=None, identity=None):
    family = actor_family_from_fname(fname)
    local_rng = _local_rng(rng, fname)
    if family in DIFFERENTIATED_ACTOR_FAMILIES:
        return _render_actor(fname, shape, local_rng)
    if family == 'flame':
        return _render_flame(fname, shape, local_rng)
    if family == 'explosion':
        return _render_explosion(fname, shape, local_rng)
    if family in {'walk_smoke', 'stomp_smoke', 'impact_smoke'}:
        return _render_smoke(fname, shape, local_rng)
    if family == 'water_wave':
        return _render_water_wave(fname, shape, local_rng)
    if family == 'yoshi_egg':
        return _render_yoshi_egg(fname, shape, local_rng)
    return None


__all__ = [
    'DIFFERENTIATED_ACTOR_FAMILIES',
    'DIFFERENTIATED_ANIMATION_FAMILIES',
    'actor_family_from_fname',
    'render_differentiated_texture',
    'supports_differentiated_texture',
]
