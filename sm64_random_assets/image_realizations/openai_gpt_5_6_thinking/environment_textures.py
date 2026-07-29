from __future__ import annotations

import fnmatch
import math
import re

import numpy as np
from PIL import Image, ImageDraw


# Focused high-quality environment pass for the early game spaces the player sees first:
# Bob-omb Battlefield, Whomp's Fortress, Jolly Roger Bay, Cool Cool Mountain,
# and Castle Grounds, plus the shared grass / water / outside texture banks they draw from.

_EXACT_RULES = {
    # Bob-omb Battlefield
    'levels/bob/0.rgba16.png': 'battlefield_grass',
    'levels/bob/1.rgba16.png': 'dirt_path',
    'levels/bob/2.rgba16.png': 'rockface_dark',
    'levels/bob/3.rgba16.png': 'cliff_meadow_mix',
    'levels/bob/4.rgba16.png': 'sunbaked_dirt',

    # Whomp's Fortress
    'levels/wf/0.rgba16.png': 'fortress_grass',
    'levels/wf/1.rgba16.png': 'fortress_blocks',
    'levels/wf/2.rgba16.png': 'fortress_blocks_dark',
    'levels/wf/3.rgba16.png': 'weathered_planks',
    'levels/wf/4.rgba16.png': 'rockface_mid',
    'levels/wf/5.ia8.png': 'chainlink_alpha',

    # Jolly Roger Bay
    'levels/jrb/0.rgba16.png': 'undersea_rock',
    'levels/jrb/1.rgba16.png': 'sea_water',
    'levels/jrb/2.rgba16.png': 'ship_planks',
    'levels/jrb/3.rgba16.png': 'seafloor_sand',

    # Cool, Cool Mountain
    'levels/ccm/0.rgba16.png': 'snowfield',
    'levels/ccm/1.rgba16.png': 'icy_trim',
    'levels/ccm/2.rgba16.png': 'mountain_rock',
    'levels/ccm/3.rgba16.png': 'cabin_planks',
    'levels/ccm/4.rgba16.png': 'packed_snow',
    'levels/ccm/5.rgba16.png': 'clear_ice',
    'levels/ccm/6.rgba16.png': 'mountain_rock_dark',
    'levels/ccm/7.rgba16.png': 'frozen_water',
    'levels/ccm/8.ia16.png': 'snow_foliage_alpha',
    'levels/ccm/9.ia16.png': 'ice_alpha',
    'levels/ccm/10.rgba16.png': 'cabin_beams',
    'levels/ccm/11.rgba16.png': 'rope_bridge_planks',
    'levels/ccm/12.rgba16.png': 'icy_stone',

    # Castle grounds local files
    'levels/castle_grounds/0.rgba16.png': 'castle_lawn',
    'levels/castle_grounds/1.rgba16.png': 'moat_water',
    'levels/castle_grounds/2.rgba16.png': 'castle_flagstone',
    'levels/castle_grounds/3.rgba16.png': 'castle_brick',
    'levels/castle_grounds/4.rgba16.png': 'hedge_top',
    'levels/castle_grounds/5.ia8.png': 'hedge_alpha',
}

_PATTERN_RULES = [
    ('textures/generic/bob_textures.*', 'bob_bank'),
    ('textures/grass/wf_textures.*', 'wf_grass_bank'),
    ('textures/water/jrb_textures.*', 'jrb_water_bank'),
    ('textures/outside/castle_grounds_textures.*', 'castle_outside_bank'),
]

_BANK_VARIANTS = {
    'bob_bank': [
        'battlefield_grass', 'battlefield_grass', 'dirt_path', 'battlefield_grass',
        'rockface_dark', 'sunbaked_dirt', 'battlefield_grass', 'cliff_meadow_mix',
        'battlefield_grass', 'dirt_path', 'rockface_mid', 'battlefield_grass',
        'rockface_dark', 'battlefield_grass', 'sunbaked_dirt', 'cliff_meadow_mix',
        'battlefield_grass', 'rockface_mid', 'dirt_path', 'battlefield_grass',
        'sunbaked_dirt', 'battlefield_fence_alpha',
    ],
    'wf_grass_bank': [
        'fortress_grass', 'fortress_grass', 'fortress_grass_flowers', 'fortress_grass',
        'fortress_grass', 'fortress_grass_flowers', 'fortress_grass', 'fortress_grass',
        'fortress_grass_flowers', 'fortress_grass', 'fortress_grass', 'fortress_grass_flowers',
        'fortress_grass', 'fortress_grass', 'fortress_grass_flowers', 'fortress_grass',
        'fortress_grass', 'fortress_grass_flowers', 'fortress_grass', 'fortress_grass',
        'fortress_grass_flowers', 'fortress_grass', 'vine_alpha', 'leafy_alpha',
    ],
    'jrb_water_bank': [
        'sea_water', 'sea_water_vertical', 'sea_water_vertical', 'sea_water_vertical',
        'sea_water_vertical', 'sea_water_vertical', 'sea_water', 'sea_water',
        'sea_water_vertical', 'sea_water_vertical', 'sea_water', 'sea_water_vertical',
        'sea_water', 'sea_water_vertical', 'sea_water_vertical',
    ],
    'castle_outside_bank': [
        'castle_lawn', 'castle_lawn', 'moat_water', 'castle_flagstone', 'castle_brick',
        'castle_brick', 'hedge_top', 'castle_lawn', 'roof_shingles', 'castle_flagstone',
        'moat_water', 'castle_lawn', 'castle_brick', 'hedge_top', 'castle_lawn',
        'castle_flagstone', 'castle_brick', 'roof_shingles', 'castle_banner_trim',
        'castle_lawn', 'hedge_alpha',
    ],
}


def _stable_seed(text: str) -> int:
    import hashlib
    return int(hashlib.sha256(text.encode('utf8')).hexdigest()[:16], 16) & 0x7FFFFFFF


def _to_rng(rng, fname: str):
    if rng is None:
        return np.random.RandomState(_stable_seed(fname))
    seed = int(rng.randint(0, 2 ** 31 - 1)) ^ _stable_seed(fname)
    return np.random.RandomState(seed)


def _clip(arr):
    return np.clip(arr, 0, 255).astype(np.uint8)


def _extract_numeric_index(fname: str):
    m = re.search(r'([0-9A-Fa-f]{1,5})(?=\.[a-z]+\d*\.png$)', fname)
    if m:
        s = m.group(1)
        try:
            if any(c in s for c in 'ABCDEFabcdef'):
                return int(s, 16)
            return int(s)
        except Exception:
            return None
    return None


def resolve_environment_motif(fname: str) -> str | None:
    if fname in _EXACT_RULES:
        return _EXACT_RULES[fname]
    for pattern, bank in _PATTERN_RULES:
        if fnmatch.fnmatch(fname, pattern):
            variants = _BANK_VARIANTS[bank]
            idx = _extract_numeric_index(fname)
            if idx is None:
                idx = _stable_seed(fname)
            if bank == 'bob_bank':
                slot = idx // 0x800 if idx > 0 else 0
            elif bank == 'wf_grass_bank':
                slot = idx // 0x800 if idx > 0 else 0
            elif bank == 'jrb_water_bank':
                slot = idx // 0x800 if idx > 0 else 0
            elif bank == 'castle_outside_bank':
                slot = idx // 0x800 if idx > 0 else 0
                if idx == 0x0BC00:
                    slot = len(variants) - 1
            else:
                slot = 0
            return variants[slot % len(variants)]
    return None


def can_generate(fname: str, shape=None) -> bool:
    return resolve_environment_motif(fname) is not None


def _rgba_to_requested(rgba, shape):
    req_channels = shape[2] if len(shape) == 3 else 1
    if req_channels == 4:
        return rgba
    if req_channels == 3:
        return rgba[:, :, :3]
    intensity = np.clip(0.299 * rgba[:, :, 0] + 0.587 * rgba[:, :, 1] + 0.114 * rgba[:, :, 2], 0, 255).astype(np.uint8)
    if req_channels == 2:
        alpha = rgba[:, :, 3]
        if np.all(alpha == 0):
            alpha = np.full_like(intensity, 255)
        return np.stack([intensity, alpha], axis=2)
    return intensity


def _base_noise(h, w, color, rng, delta=8):
    base = np.empty((h, w, 4), dtype=np.uint8)
    rgb = np.array(color, dtype=np.int16)
    noise = rng.randint(-delta, delta + 1, size=(h, w, 3))
    base[:, :, :3] = _clip(rgb[None, None, :] + noise)
    base[:, :, 3] = 255
    return base


def _grass_tile(h, w, rng, *, palette, flowers=False, dry=False):
    arr = _base_noise(h, w, palette[0], rng, delta=10)
    # subtle vertical mottling
    for y in range(h):
        t = y / max(h - 1, 1)
        band = np.array(palette[1 if t < 0.55 else 2], dtype=np.int16)
        arr[y, :, :3] = _clip(arr[y, :, :3].astype(np.int16) * 0.55 + band[None, :] * 0.45)
    img = Image.fromarray(arr, mode='RGBA')
    draw = ImageDraw.Draw(img)
    blade_count = max(24, (w * h) // 5)
    for _ in range(blade_count):
        x = int(rng.randint(0, w))
        y0 = int(rng.randint(0, h))
        length = int(rng.randint(max(2, h // 8), max(3, h // 3)))
        lean = int(rng.randint(-2, 3))
        color = tuple(int(c) for c in palette[int(rng.randint(1, len(palette)))]) + (255,)
        draw.line((x, y0, x + lean, max(0, y0 - length)), fill=color, width=1)
    if flowers:
        for _ in range(max(2, w * h // 160)):
            x = int(rng.randint(0, w))
            y = int(rng.randint(0, h))
            petal = (245, 236, 166, 255) if rng.rand() > 0.45 else (232, 242, 255, 255)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                draw.point((max(0, min(w - 1, x + dx)), max(0, min(h - 1, y + dy))), fill=petal)
            draw.point((x, y), fill=(238, 180, 48, 255))
    if dry:
        overlay = Image.new('RGBA', (w, h), (170, 140, 62, 36))
        img = Image.alpha_composite(img, overlay)
    return np.array(img, dtype=np.uint8)


def _water_tile(h, w, rng, *, deep=(29, 90, 156), shallow=(104, 190, 228), vertical=False, foam=False, frozen=False):
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    for y in range(h):
        t = y / max(h - 1, 1)
        if vertical:
            a, b = shallow, deep
        else:
            a, b = deep, shallow
        color = (np.array(a) * (1 - t) + np.array(b) * t).astype(np.int16)
        arr[y, :, :3] = _clip(color[None, :] + rng.randint(-8, 9, size=(w, 3)))
        arr[y, :, 3] = 255
    img = Image.fromarray(arr, mode='RGBA')
    draw = ImageDraw.Draw(img)
    wave_lines = max(4, h // 6)
    for i in range(wave_lines):
        yy = int((i + 0.5) * h / wave_lines)
        pts = []
        for x in range(0, w + 2, 2):
            amp = 1.5 if not frozen else 0.5
            offs = math.sin((x / max(w, 1)) * math.tau * (1.7 + 0.3 * i) + i * 0.7) * amp
            pts.append((x, yy + offs))
        draw.line(pts, fill=(190, 232, 252, 110 if not frozen else 90), width=1)
    if foam:
        for x in range(0, w, 4):
            y = int(h * 0.15 + 2 * math.sin(x / max(w, 1) * math.tau * 2.2))
            draw.ellipse((x, y, min(w - 1, x + 3), min(h - 1, y + 2)), fill=(245, 249, 255, 160))
    sparkle_count = max(4, (w * h) // 90)
    for _ in range(sparkle_count):
        x = int(rng.randint(0, w))
        y = int(rng.randint(0, h))
        c = (230, 250, 255, 140) if not frozen else (255, 255, 255, 110)
        draw.point((x, y), fill=c)
    if frozen:
        glaze = Image.new('RGBA', (w, h), (210, 235, 255, 40))
        img = Image.alpha_composite(img, glaze)
    return np.array(img, dtype=np.uint8)


def _stone_tile(h, w, rng, *, base=(126, 118, 106), accent=(159, 152, 139), mortar=(73, 67, 60), blocks=False, large_blocks=False):
    arr = _base_noise(h, w, base, rng, delta=13)
    img = Image.fromarray(arr, mode='RGBA')
    draw = ImageDraw.Draw(img)
    if blocks:
        cols = 4 if not large_blocks else 3
        rows = 4 if not large_blocks else 3
        bw = max(6, w // cols)
        bh = max(6, h // rows)
        y = 0
        row = 0
        while y < h:
            offset = 0 if row % 2 == 0 else bw // 2
            x = -offset
            while x < w:
                x1 = max(0, x)
                y1 = y
                x2 = min(w - 1, x + bw)
                y2 = min(h - 1, y + bh)
                fill = tuple(int(c) for c in np.clip(np.array(accent) + rng.randint(-14, 15, size=3), 0, 255)) + (255,)
                draw.rectangle((x1, y1, x2, y2), fill=fill, outline=mortar + (255,))
                if x2 - x1 > 4 and y2 - y1 > 4:
                    draw.line((x1 + 2, y1 + 2, x2 - 2, y1 + 2), fill=(255, 255, 255, 30), width=1)
                x += bw
            y += bh
            row += 1
    else:
        rock_count = max(8, (w * h) // 70)
        for _ in range(rock_count):
            cx = int(rng.randint(0, w))
            cy = int(rng.randint(0, h))
            rx = int(rng.randint(max(2, w // 10), max(3, w // 4)))
            ry = int(rng.randint(max(2, h // 12), max(3, h // 5)))
            fill = tuple(int(c) for c in np.clip(np.array(accent) + rng.randint(-18, 19, size=3), 0, 255)) + (145,)
            draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=fill)
    return np.array(img, dtype=np.uint8)


def _wood_tile(h, w, rng, *, base=(132, 98, 58), dark=(96, 69, 38), bands=True):
    arr = _base_noise(h, w, base, rng, delta=10)
    img = Image.fromarray(arr, mode='RGBA')
    draw = ImageDraw.Draw(img)
    plank_h = max(6, h // 4)
    y = 0
    band_index = 0
    while y < h:
        fill = tuple(int(c) for c in np.clip(np.array(base) + rng.randint(-12, 13, size=3), 0, 255)) + (255,)
        draw.rectangle((0, y, w, min(h - 1, y + plank_h)), fill=fill)
        if bands:
            draw.line((0, y, w, y), fill=dark + (255,), width=1)
        for _ in range(max(3, w // 4)):
            x = int(rng.randint(0, w))
            yy = int(rng.randint(y, min(h - 1, y + plank_h)))
            ln = int(rng.randint(max(2, w // 6), max(3, w // 2)))
            draw.line((x, yy, min(w - 1, x + ln), yy), fill=(dark[0], dark[1], dark[2], 110), width=1)
        if band_index % 2 == 0 and plank_h > 6:
            for x in [w // 4, (3 * w) // 4]:
                draw.ellipse((x - 1, y + plank_h // 2 - 1, x + 1, y + plank_h // 2 + 1), fill=(74, 52, 29, 255))
        y += plank_h
        band_index += 1
    return np.array(img, dtype=np.uint8)


def _snow_tile(h, w, rng, *, icy=False, packed=False):
    base = (240, 244, 250) if not packed else (224, 230, 238)
    arr = _base_noise(h, w, base, rng, delta=5)
    if icy:
        tint = np.array((190, 220, 246), dtype=np.int16)
        arr[:, :, :3] = _clip(arr[:, :, :3].astype(np.int16) * 0.7 + tint[None, None, :] * 0.3)
    img = Image.fromarray(arr, mode='RGBA')
    draw = ImageDraw.Draw(img)
    for _ in range(max(8, (w * h) // 50)):
        x = int(rng.randint(0, w))
        y = int(rng.randint(0, h))
        r = int(rng.randint(1, 3))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 140))
    if packed:
        for y in range(0, h, max(4, h // 8)):
            draw.line((0, y, w, y), fill=(210, 217, 225, 60), width=1)
    return np.array(img, dtype=np.uint8)


def _ice_tile(h, w, rng, *, alpha=False):
    rgba = _water_tile(h, w, rng, deep=(134, 189, 227), shallow=(216, 240, 255), vertical=False, foam=False, frozen=True)
    img = Image.fromarray(rgba, mode='RGBA')
    draw = ImageDraw.Draw(img)
    for _ in range(max(5, (w * h) // 120)):
        x0 = int(rng.randint(0, w))
        y0 = int(rng.randint(0, h))
        x1 = int(np.clip(x0 + rng.randint(-w // 3, w // 3 + 1), 0, w - 1))
        y1 = int(np.clip(y0 + rng.randint(-h // 3, h // 3 + 1), 0, h - 1))
        draw.line((x0, y0, x1, y1), fill=(255, 255, 255, 95), width=1)
    rgba = np.array(img, dtype=np.uint8)
    if alpha:
        # translucent chunks, for IA assets that likely want a mask / soft silhouette
        alpha_mask = np.zeros((h, w), dtype=np.uint8)
        yy, xx = np.mgrid[0:h, 0:w]
        cx, cy = w / 2.0, h / 2.0
        dist = np.sqrt(((xx - cx) / max(w / 2.2, 1)) ** 2 + ((yy - cy) / max(h / 2.2, 1)) ** 2)
        alpha_mask[dist < 0.95] = 180
        alpha_mask[dist < 0.65] = 230
        rgba[:, :, 3] = alpha_mask
    return rgba


def _sand_tile(h, w, rng):
    arr = _base_noise(h, w, (199, 182, 128), rng, delta=11)
    img = Image.fromarray(arr, mode='RGBA')
    draw = ImageDraw.Draw(img)
    for _ in range(max(10, (w * h) // 60)):
        x = int(rng.randint(0, w))
        y = int(rng.randint(0, h))
        draw.ellipse((x, y, min(w - 1, x + 1), min(h - 1, y + 1)), fill=(158, 142, 95, 255))
    return np.array(img, dtype=np.uint8)


def _leafy_alpha_tile(h, w, rng, *, snowy=False, vines=False):
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    img = Image.fromarray(rgba, mode='RGBA')
    draw = ImageDraw.Draw(img)
    colors = [
        (64, 112, 44, 220),
        (92, 146, 70, 235),
        (125, 168, 88, 230),
    ]
    if snowy:
        colors = [(190, 210, 206, 220), (220, 235, 232, 235), (240, 246, 246, 230)]
    cluster_count = max(8, (w * h) // 70)
    for _ in range(cluster_count):
        cx = int(rng.randint(0, w))
        cy = int(rng.randint(0, h))
        rx = int(rng.randint(max(2, w // 12), max(3, w // 5)))
        ry = int(rng.randint(max(2, h // 12), max(3, h // 5)))
        fill = colors[int(rng.randint(0, len(colors)))]
        draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=fill)
        if vines:
            draw.line((cx, cy - ry, cx, min(h - 1, cy + ry + 3)), fill=(58, 92, 42, 180), width=1)
    # cut transparent holes so the tile actually behaves like a masked texture
    hole_count = max(3, (w * h) // 180)
    for _ in range(hole_count):
        cx = int(rng.randint(0, w))
        cy = int(rng.randint(0, h))
        rr = int(rng.randint(max(1, min(w, h) // 10), max(2, min(w, h) // 5)))
        draw.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=(0, 0, 0, 0))
    return np.array(img, dtype=np.uint8)


def _chainlink_tile(h, w, rng):
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    img = Image.fromarray(rgba, mode='RGBA')
    draw = ImageDraw.Draw(img)
    spacing = max(5, min(w, h) // 3)
    line_color = (166, 171, 179, 215)
    # diagonal diamonds on transparent background
    for offset in range(-h, w + h, spacing):
        draw.line((offset, 0, offset + h, h), fill=line_color, width=1)
        draw.line((offset, h, offset + h, 0), fill=line_color, width=1)
    # border wire hints
    draw.rectangle((0, 0, w - 1, h - 1), outline=(112, 116, 123, 225), width=1)
    return np.array(img, dtype=np.uint8)


def _banner_trim_tile(h, w, rng):
    arr = _base_noise(h, w, (154, 112, 31), rng, delta=4)
    img = Image.fromarray(arr, mode='RGBA')
    draw = ImageDraw.Draw(img)
    band_h = max(4, h // 4)
    draw.rectangle((0, 0, w, band_h), fill=(165, 22, 24, 255))
    draw.rectangle((0, band_h, w, band_h * 2), fill=(232, 214, 120, 255))
    draw.rectangle((0, band_h * 2, w, band_h * 3), fill=(165, 22, 24, 255))
    draw.rectangle((0, band_h * 3, w, h), fill=(232, 214, 120, 255))
    return np.array(img, dtype=np.uint8)


def _motif_to_rgba(motif: str, h: int, w: int, rng):
    if motif == 'battlefield_grass':
        return _grass_tile(h, w, rng, palette=[(84, 130, 54), (110, 164, 69), (156, 194, 97)], flowers=False)
    if motif == 'fortress_grass':
        return _grass_tile(h, w, rng, palette=[(92, 134, 58), (123, 176, 79), (167, 207, 109)], flowers=False)
    if motif == 'fortress_grass_flowers':
        return _grass_tile(h, w, rng, palette=[(92, 134, 58), (123, 176, 79), (167, 207, 109)], flowers=True)
    if motif == 'castle_lawn':
        return _grass_tile(h, w, rng, palette=[(78, 125, 54), (106, 159, 74), (146, 188, 94)], flowers=False)
    if motif == 'hedge_top':
        return _grass_tile(h, w, rng, palette=[(58, 102, 44), (82, 132, 62), (120, 167, 94)], flowers=False)
    if motif == 'cliff_meadow_mix':
        rgba = _grass_tile(h, w, rng, palette=[(90, 128, 60), (118, 161, 84), (151, 189, 108)], flowers=False)
        img = Image.fromarray(rgba, mode='RGBA')
        draw = ImageDraw.Draw(img)
        for _ in range(max(5, (w * h) // 110)):
            x = int(rng.randint(0, w))
            y = int(rng.randint(0, h))
            r = int(rng.randint(2, max(3, min(w, h) // 5)))
            draw.ellipse((x - r, y - r, x + r, y + r), fill=(112, 103, 89, 180))
        return np.array(img, dtype=np.uint8)
    if motif == 'dirt_path':
        return _sand_tile(h, w, rng)
    if motif == 'sunbaked_dirt':
        rgba = _sand_tile(h, w, rng)
        rgba[:, :, :3] = _clip(rgba[:, :, :3].astype(np.int16) * np.array([1.0, 0.92, 0.75])[None, None, :])
        return rgba
    if motif == 'seafloor_sand':
        rgba = _sand_tile(h, w, rng)
        rgba[:, :, :3] = _clip(rgba[:, :, :3].astype(np.int16) * 0.8 + np.array((80, 120, 118), dtype=np.int16)[None, None, :] * 0.2)
        return rgba
    if motif == 'rockface_dark':
        return _stone_tile(h, w, rng, base=(94, 88, 82), accent=(126, 118, 111), mortar=(62, 59, 54), blocks=False)
    if motif == 'rockface_mid':
        return _stone_tile(h, w, rng, base=(111, 104, 98), accent=(145, 136, 126), mortar=(74, 69, 63), blocks=False)
    if motif == 'undersea_rock':
        rgba = _stone_tile(h, w, rng, base=(88, 99, 106), accent=(116, 133, 138), mortar=(57, 65, 72), blocks=False)
        rgba[:, :, :3] = _clip(rgba[:, :, :3].astype(np.int16) + np.array((0, 18, 24), dtype=np.int16)[None, None, :])
        return rgba
    if motif == 'mountain_rock':
        return _stone_tile(h, w, rng, base=(118, 116, 124), accent=(148, 147, 160), mortar=(81, 79, 87), blocks=False)
    if motif == 'mountain_rock_dark':
        return _stone_tile(h, w, rng, base=(95, 95, 104), accent=(123, 126, 140), mortar=(62, 63, 71), blocks=False)
    if motif == 'fortress_blocks':
        return _stone_tile(h, w, rng, base=(126, 122, 118), accent=(161, 156, 148), mortar=(76, 74, 70), blocks=True)
    if motif == 'fortress_blocks_dark':
        return _stone_tile(h, w, rng, base=(98, 97, 96), accent=(132, 131, 128), mortar=(63, 63, 61), blocks=True)
    if motif == 'castle_brick':
        return _stone_tile(h, w, rng, base=(154, 140, 126), accent=(189, 172, 156), mortar=(98, 92, 86), blocks=True, large_blocks=True)
    if motif == 'castle_flagstone':
        return _stone_tile(h, w, rng, base=(129, 124, 115), accent=(163, 157, 147), mortar=(80, 75, 69), blocks=True)
    if motif == 'icy_stone':
        rgba = _stone_tile(h, w, rng, base=(146, 154, 165), accent=(185, 198, 212), mortar=(96, 105, 116), blocks=True)
        rgba[:, :, :3] = _clip(rgba[:, :, :3].astype(np.int16) + np.array((12, 18, 24), dtype=np.int16)[None, None, :])
        return rgba
    if motif == 'weathered_planks':
        return _wood_tile(h, w, rng, base=(126, 97, 61), dark=(87, 62, 37))
    if motif == 'ship_planks':
        return _wood_tile(h, w, rng, base=(139, 106, 68), dark=(88, 62, 39))
    if motif == 'cabin_planks':
        return _wood_tile(h, w, rng, base=(147, 109, 63), dark=(93, 62, 35))
    if motif == 'cabin_beams':
        return _wood_tile(h, w, rng, base=(124, 90, 52), dark=(80, 56, 32))
    if motif == 'rope_bridge_planks':
        rgba = _wood_tile(h, w, rng, base=(132, 100, 64), dark=(88, 66, 40))
        img = Image.fromarray(rgba, mode='RGBA')
        draw = ImageDraw.Draw(img)
        for x in [w // 5, (4 * w) // 5]:
            draw.line((x, 0, x, h), fill=(126, 97, 58, 150), width=max(1, w // 12))
        return np.array(img, dtype=np.uint8)
    if motif == 'snowfield':
        return _snow_tile(h, w, rng, icy=False, packed=False)
    if motif == 'packed_snow':
        return _snow_tile(h, w, rng, icy=False, packed=True)
    if motif == 'clear_ice':
        return _ice_tile(h, w, rng, alpha=False)
    if motif == 'frozen_water':
        return _water_tile(h, w, rng, deep=(94, 153, 210), shallow=(190, 226, 247), vertical=False, foam=False, frozen=True)
    if motif == 'moat_water':
        return _water_tile(h, w, rng, deep=(24, 92, 164), shallow=(98, 186, 230), vertical=False, foam=True)
    if motif == 'sea_water':
        return _water_tile(h, w, rng, deep=(22, 88, 150), shallow=(82, 174, 218), vertical=False, foam=False)
    if motif == 'sea_water_vertical':
        return _water_tile(h, w, rng, deep=(22, 88, 150), shallow=(95, 188, 228), vertical=True, foam=False)
    if motif == 'icy_trim':
        return _water_tile(h, w, rng, deep=(169, 208, 235), shallow=(236, 246, 252), vertical=True, foam=False, frozen=True)
    if motif == 'roof_shingles':
        rgba = _base_noise(h, w, (108, 69, 51), rng, delta=8)
        img = Image.fromarray(rgba, mode='RGBA')
        draw = ImageDraw.Draw(img)
        sh = max(4, h // 5)
        for y in range(0, h + sh, sh):
            offset = 0 if (y // sh) % 2 == 0 else sh // 2
            for x in range(-offset, w + sh, sh):
                draw.rounded_rectangle((x, y, x + sh, y + sh + 1), radius=max(1, sh // 4), fill=(129, 86, 63, 255), outline=(82, 55, 39, 255))
        return np.array(img, dtype=np.uint8)
    if motif == 'hedge_alpha':
        return _leafy_alpha_tile(h, w, rng, snowy=False, vines=False)
    if motif == 'leafy_alpha':
        return _leafy_alpha_tile(h, w, rng, snowy=False, vines=False)
    if motif == 'snow_foliage_alpha':
        return _leafy_alpha_tile(h, w, rng, snowy=True, vines=False)
    if motif == 'vine_alpha':
        return _leafy_alpha_tile(h, w, rng, snowy=False, vines=True)
    if motif == 'chainlink_alpha':
        return _chainlink_tile(h, w, rng)
    if motif == 'battlefield_fence_alpha':
        return _chainlink_tile(h, w, rng)
    if motif == 'ice_alpha':
        return _ice_tile(h, w, rng, alpha=True)
    if motif == 'castle_banner_trim':
        return _banner_trim_tile(h, w, rng)
    # safe fallback in case a bank entry is edited without a handler
    return _stone_tile(h, w, rng, blocks=False)


def render_environment_texture(fname: str, shape, rng=None, identity=None):
    motif = resolve_environment_motif(fname)
    if motif is None:
        return None
    h, w = int(shape[0]), int(shape[1])
    local_rng = _to_rng(rng, fname)
    rgba = _motif_to_rgba(motif, h, w, local_rng)
    return _rgba_to_requested(rgba, shape)


__all__ = [
    'can_generate',
    'render_environment_texture',
    'resolve_environment_motif',
]
