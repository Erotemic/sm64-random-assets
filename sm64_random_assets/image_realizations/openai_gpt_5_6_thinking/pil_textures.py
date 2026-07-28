from __future__ import annotations

import hashlib
import math
from pathlib import PurePosixPath

import numpy as np
from PIL import Image, ImageDraw


def _stable_seed(text: str) -> int:
    return int(hashlib.sha256(text.encode('utf8')).hexdigest()[:16], 16) & 0x7FFFFFFF


def _to_rng(rng, fname: str):
    if rng is None:
        return np.random.RandomState(_stable_seed(fname))
    # derive a child rng from the passed deterministic rng without mutating global state
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


def _palette(subject: str, rng):
    palettes = {
        'grass': ((72, 119, 64), (108, 156, 77), (154, 185, 94), (46, 84, 48)),
        'water': ((42, 87, 135), (75, 138, 189), (121, 188, 214), (19, 52, 95)),
        'lava': ((153, 42, 18), (223, 96, 33), (246, 184, 73), (92, 12, 8)),
        'stone': ((103, 104, 109), (145, 145, 147), (182, 175, 161), (64, 63, 66)),
        'wood': ((98, 62, 33), (136, 92, 56), (176, 132, 88), (62, 37, 22)),
        'metal': ((91, 109, 122), (131, 152, 165), (189, 206, 214), (56, 67, 74)),
        'brick': ((123, 71, 58), (156, 94, 79), (204, 165, 129), (88, 49, 40)),
        'sand': ((185, 161, 102), (220, 197, 134), (242, 225, 181), (125, 104, 64)),
        'snow': ((190, 208, 224), (224, 236, 244), (250, 252, 255), (132, 151, 170)),
        'sky': ((76, 134, 212), (129, 182, 232), (201, 227, 250), (47, 89, 173)),
        'cloud': ((150, 184, 214), (206, 226, 239), (250, 252, 255), (103, 135, 162)),
        'foliage': ((47, 86, 52), (84, 135, 74), (139, 174, 88), (27, 54, 29)),
        'fabric': ((107, 69, 126), (147, 108, 171), (208, 174, 226), (69, 39, 87)),
        'eye': ((242, 240, 234), (255, 255, 255), (50, 62, 78), (11, 17, 24)),
        'sign': ((130, 96, 57), (193, 163, 98), (241, 226, 183), (70, 46, 22)),
        'generic': ((92, 103, 118), (138, 152, 173), (198, 209, 221), (58, 66, 77)),
    }
    base = palettes.get(subject, palettes['generic'])
    return tuple(_jitter(c, 12, rng) for c in base)


def classify_texture_subject(fname: str) -> str:
    low = fname.lower()
    path = PurePosixPath(low)
    parts = path.parts
    tokens = set(parts)
    if any(k in low for k in ['water', 'bubble', 'wave', 'sea', 'river']):
        return 'water'
    if any(k in low for k in ['lava', 'fire', 'flame', 'hot', 'burn']):
        return 'lava'
    if any(k in low for k in ['grass', 'flower', 'leaf', 'hedge', 'tree', 'bush']):
        return 'grass'
    if any(k in low for k in ['stone', 'rock', 'castle', 'wall', 'cobble']):
        return 'stone'
    if any(k in low for k in ['wood', 'log', 'tree', 'door', 'plank']):
        return 'wood'
    if any(k in low for k in ['metal', 'chain', 'cannon', 'gear', 'iron', 'steel']):
        return 'metal'
    if any(k in low for k in ['brick', 'masonry']):
        return 'brick'
    if any(k in low for k in ['sand', 'desert', 'dune']):
        return 'sand'
    if any(k in low for k in ['snow', 'ice', 'frost']):
        return 'snow'
    if any(k in low for k in ['sky', 'cloud']):
        return 'sky' if 'sky' in low else 'cloud'
    if any(k in low for k in ['cloth', 'curtain', 'carpet', 'quilt', 'banner']):
        return 'fabric'
    if any(k in low for k in ['eye', 'iris', 'pupil', 'blink']):
        return 'eye'
    if any(k in low for k in ['sign', 'board', 'arrow', 'message']):
        return 'sign'
    if 'leaves' in tokens or 'foliage' in tokens:
        return 'foliage'
    return 'generic'


def _vertical_gradient(draw, w, h, top, bottom):
    for y in range(h):
        t = y / max(h - 1, 1)
        draw.line((0, y, w, y), fill=_mix(top, bottom, t))


def _draw_grass(draw, w, h, colors, rng):
    _vertical_gradient(draw, w, h, colors[1], colors[0])
    for y in range(0, h, max(2, h // 8)):
        draw.line((0, y, w, y), fill=_jitter(colors[3], 6, rng), width=1)
    for x in range(0, w, max(2, w // 12)):
        base_y = h - 1
        tip_y = rng.randint(max(0, h // 5), max(1, h // 2))
        bend = rng.randint(-max(1, w // 12), max(1, w // 12) + 1)
        draw.line((x, base_y, x + bend, tip_y), fill=_jitter(colors[2], 10, rng), width=1)
    for _ in range(max(2, (w * h) // 256)):
        cx = rng.randint(0, w)
        cy = rng.randint(0, h)
        r = max(1, min(w, h) // 12)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=_jitter(colors[2], 12, rng))


def _draw_water(draw, w, h, colors, rng):
    _vertical_gradient(draw, w, h, colors[1], colors[3])
    for i in range(max(3, h // 5)):
        y = int((i + 0.5) * h / max(3, h // 5))
        pts = []
        for x in range(0, w + 3, 3):
            amp = max(1, h // 12)
            yy = y + int(math.sin((x / max(w, 1)) * math.pi * 2 + i) * amp)
            pts.append((x, yy))
        draw.line(pts, fill=_jitter(colors[2], 8, rng), width=1)
    for _ in range(max(3, (w * h) // 192)):
        x = rng.randint(0, w)
        y = rng.randint(0, h)
        r = rng.randint(1, max(2, min(w, h) // 10))
        draw.ellipse((x - r, y - r, x + r, y + r), outline=_jitter(colors[2], 8, rng), width=1)


def _draw_lava(draw, w, h, colors, rng):
    _vertical_gradient(draw, w, h, colors[1], colors[3])
    for _ in range(max(6, (w * h) // 128)):
        x = rng.randint(0, w)
        y = rng.randint(0, h)
        rx = rng.randint(max(1, w // 10), max(2, w // 4))
        ry = rng.randint(max(1, h // 10), max(2, h // 4))
        fill = _mix(colors[0], colors[2], rng.rand())
        draw.ellipse((x - rx, y - ry, x + rx, y + ry), fill=fill)
    for _ in range(max(3, (w * h) // 256)):
        x = rng.randint(0, w)
        y = rng.randint(0, h)
        draw.ellipse((x - 1, y - 1, x + 1, y + 1), fill=colors[2])


def _draw_stone(draw, w, h, colors, rng, *, bricky=False):
    bg = colors[1]
    draw.rectangle((0, 0, w, h), fill=bg)
    cell_w = max(4, w // (4 if bricky else 3))
    cell_h = max(4, h // (4 if bricky else 3))
    y = 0
    row = 0
    while y < h:
        offset = (cell_w // 2) if bricky and (row % 2) else 0
        x = -offset
        while x < w:
            ww = cell_w + rng.randint(-max(1, cell_w // 4), max(1, cell_w // 4) + 1)
            hh = cell_h + rng.randint(-max(1, cell_h // 4), max(1, cell_h // 4) + 1)
            color = _mix(colors[0], colors[2], rng.rand())
            draw.rounded_rectangle((x + 1, y + 1, x + ww - 1, y + hh - 1), radius=1, fill=color, outline=colors[3])
            x += cell_w
        y += cell_h
        row += 1


def _draw_wood(draw, w, h, colors, rng):
    _vertical_gradient(draw, w, h, colors[2], colors[0])
    plank_h = max(4, h // 4)
    for y in range(0, h, plank_h):
        draw.rectangle((0, y, w, min(h, y + plank_h)), outline=colors[3], width=1)
        for k in range(2):
            yy = y + plank_h * (k + 1) // 3
            pts = []
            phase = rng.rand() * math.pi * 2
            for x in range(0, w + 2, 2):
                wave = int(math.sin(phase + x / max(1, w) * math.pi * 2) * max(1, plank_h // 8))
                pts.append((x, yy + wave))
            draw.line(pts, fill=_jitter(colors[1], 10, rng), width=1)
        for _ in range(max(1, w // 24)):
            cx = rng.randint(0, w)
            cy = rng.randint(y, min(h, y + plank_h))
            rx = max(1, w // 12)
            ry = max(1, plank_h // 5)
            draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline=colors[3], width=1)


def _draw_metal(draw, w, h, colors, rng):
    _vertical_gradient(draw, w, h, colors[2], colors[0])
    for x in range(0, w, max(3, w // 6)):
        draw.line((x, 0, x, h), fill=_jitter(colors[1], 6, rng), width=1)
    for y in range(0, h, max(3, h // 6)):
        draw.line((0, y, w, y), fill=_jitter(colors[1], 6, rng), width=1)
    step = max(4, min(w, h) // 3)
    for y in range(step // 2, h, step):
        for x in range(step // 2, w, step):
            r = max(1, min(w, h) // 12)
            draw.ellipse((x - r, y - r, x + r, y + r), fill=colors[3], outline=colors[2])


def _draw_speckles(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=colors[1])
    for _ in range(max(8, (w * h) // 16)):
        x = rng.randint(0, w)
        y = rng.randint(0, h)
        draw.point((x, y), fill=_mix(colors[0], colors[2], rng.rand()))
    for _ in range(max(2, (w * h) // 256)):
        x = rng.randint(0, w)
        y = rng.randint(0, h)
        r = max(1, min(w, h) // 10)
        draw.ellipse((x - r, y - r, x + r, y + r), outline=_jitter(colors[3], 4, rng), width=1)


def _draw_clouds(draw, w, h, colors, rng):
    _vertical_gradient(draw, w, h, colors[0], colors[1])
    for _ in range(max(3, (w * h) // 256)):
        cx = rng.randint(0, w)
        cy = rng.randint(0, h)
        rw = rng.randint(max(2, w // 8), max(3, w // 4))
        rh = rng.randint(max(2, h // 10), max(3, h // 5))
        for dx in [-rw // 2, 0, rw // 2]:
            draw.ellipse((cx + dx - rw // 2, cy - rh // 2, cx + dx + rw // 2, cy + rh // 2), fill=colors[2])


def _draw_fabric(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=colors[1])
    step = max(3, min(w, h) // 6)
    for i in range(-h, w, step):
        draw.line((i, 0, i + h, h), fill=_jitter(colors[2], 8, rng), width=1)
    for i in range(0, w + h, step):
        draw.line((i, 0, i - h, h), fill=_jitter(colors[0], 8, rng), width=1)
    draw.rectangle((0, 0, w - 1, h - 1), outline=colors[3], width=1)


def _draw_eye(draw, w, h, colors, rng, fname=''):
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
    margin_x = max(1, w // 12)
    margin_y = max(1, h // 5)
    draw.ellipse((margin_x, margin_y, w - margin_x, h - margin_y), fill=colors[1], outline=colors[3])
    cx = w // 2 + rng.randint(-max(1, w // 10), max(1, w // 10) + 1)
    cy = h // 2 + rng.randint(-max(1, h // 10), max(1, h // 10) + 1)
    rr = max(1, min(w, h) // 6)
    draw.ellipse((cx - rr * 2, cy - rr * 2, cx + rr * 2, cy + rr * 2), fill=colors[2])
    draw.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=colors[3])
    draw.ellipse((cx - 1, cy - 1, cx, cy), fill=colors[1])
    if 'closed' in str(fname):
        draw.line((margin_x, h // 2, w - margin_x, h // 2), fill=colors[3], width=max(1, h // 8))


def _draw_sign(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=colors[0])
    pad = max(1, min(w, h) // 8)
    draw.rounded_rectangle((pad, pad, w - pad, h - pad), radius=max(1, pad // 2), fill=colors[2], outline=colors[3], width=1)
    for i in range(2, 6):
        y = pad + i * max(1, (h - 2 * pad) // 8)
        draw.line((pad * 2, y, w - pad * 2, y), fill=_jitter(colors[1], 8, rng), width=1)
    arrow_y = h - pad * 2
    draw.polygon([(pad * 2, arrow_y), (w // 2, h - pad), (w - pad * 2, arrow_y)], fill=colors[1])


def _draw_generic(draw, w, h, colors, rng):
    _vertical_gradient(draw, w, h, colors[1], colors[0])
    step = max(3, min(w, h) // 4)
    for y in range(0, h + step, step):
        for x in range(0, w + step, step):
            fill = colors[(x // step + y // step) % 3]
            draw.polygon([(x, y + step // 2), (x + step // 2, y), (x + step, y + step // 2), (x + step // 2, y + step)], fill=fill, outline=colors[3])



def render_pil_texture(fname: str, shape, rng=None, identity=None):
    h, w = int(shape[0]), int(shape[1])
    local_rng = _to_rng(rng, fname)
    subject = classify_texture_subject(fname)
    colors = _palette(subject, local_rng)

    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if subject == 'grass' or subject == 'foliage':
        _draw_grass(draw, w, h, colors, local_rng)
    elif subject == 'water':
        _draw_water(draw, w, h, colors, local_rng)
    elif subject == 'lava':
        _draw_lava(draw, w, h, colors, local_rng)
    elif subject == 'stone':
        _draw_stone(draw, w, h, colors, local_rng, bricky=False)
    elif subject == 'brick':
        _draw_stone(draw, w, h, colors, local_rng, bricky=True)
    elif subject == 'wood':
        _draw_wood(draw, w, h, colors, local_rng)
    elif subject == 'metal':
        _draw_metal(draw, w, h, colors, local_rng)
    elif subject in {'sand', 'snow'}:
        _draw_speckles(draw, w, h, colors, local_rng)
    elif subject in {'sky', 'cloud'}:
        _draw_clouds(draw, w, h, colors, local_rng)
    elif subject == 'fabric':
        _draw_fabric(draw, w, h, colors, local_rng)
    elif subject == 'eye':
        _draw_eye(draw, w, h, colors, local_rng, fname=fname)
    elif subject == 'sign':
        _draw_sign(draw, w, h, colors, local_rng)
    else:
        _draw_generic(draw, w, h, colors, local_rng)

    rgba = np.array(img, dtype=np.uint8)
    req_channels = shape[2] if len(shape) == 3 else 1
    if req_channels == 4:
        return rgba
    if req_channels == 3:
        return rgba[:, :, 0:3]
    # grayscale conversion
    intensity = np.clip(
        0.299 * rgba[:, :, 0] + 0.587 * rgba[:, :, 1] + 0.114 * rgba[:, :, 2], 0, 255
    ).astype(np.uint8)
    if req_channels == 2:
        alpha = rgba[:, :, 3]
        if np.all(alpha == 0):
            alpha = np.full_like(intensity, 255)
        return np.stack([intensity, alpha], axis=2)
    return intensity


__all__ = ['classify_texture_subject', 'render_pil_texture']
