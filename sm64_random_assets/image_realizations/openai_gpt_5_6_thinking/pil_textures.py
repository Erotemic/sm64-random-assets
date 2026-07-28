from __future__ import annotations

import hashlib
import math
from pathlib import PurePosixPath

import numpy as np
from PIL import Image, ImageDraw


# -----------------------------
# deterministic helpers
# -----------------------------


def _stable_seed(text: str) -> int:
    return int(hashlib.sha256(text.encode('utf8')).hexdigest()[:16], 16) & 0x7FFFFFFF


def _to_rng(rng, fname: str):
    if rng is None:
        return np.random.RandomState(_stable_seed(fname))
    seed = int(rng.randint(0, 2 ** 31 - 1)) ^ _stable_seed(fname)
    return np.random.RandomState(seed)


# -----------------------------
# color helpers
# -----------------------------


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
        'grass': ((73, 112, 51), (110, 158, 77), (162, 198, 108), (48, 77, 35)),
        'foliage': ((52, 95, 50), (86, 137, 74), (147, 181, 96), (29, 56, 25)),
        'water': ((32, 82, 138), (70, 136, 189), (138, 204, 230), (18, 44, 93)),
        'lava': ((114, 22, 10), (201, 64, 22), (249, 165, 59), (52, 5, 4)),
        'stone': ((98, 99, 105), (136, 137, 143), (182, 177, 166), (61, 62, 67)),
        'brick': ((130, 70, 55), (163, 92, 72), (206, 156, 124), (89, 43, 36)),
        'wood': ((101, 65, 33), (140, 96, 55), (181, 137, 90), (64, 39, 20)),
        'metal': ((88, 106, 121), (136, 155, 171), (191, 209, 220), (56, 67, 77)),
        'sand': ((187, 165, 109), (220, 198, 138), (244, 229, 186), (128, 106, 66)),
        'snow': ((191, 210, 225), (227, 237, 245), (251, 253, 255), (137, 155, 175)),
        'sky': ((78, 135, 214), (128, 180, 233), (199, 227, 250), (52, 91, 176)),
        'cloud': ((148, 184, 213), (201, 224, 238), (252, 253, 255), (105, 138, 165)),
        'fabric': ((105, 73, 128), (145, 111, 172), (204, 176, 228), (71, 43, 92)),
        'sign': ((132, 97, 58), (190, 158, 97), (241, 227, 183), (70, 45, 22)),
        'eye': ((242, 240, 234), (255, 255, 255), (74, 115, 166), (11, 17, 24)),
        'generic': ((96, 108, 120), (139, 153, 172), (195, 209, 222), (59, 68, 80)),
    }
    base = palettes.get(subject, palettes['generic'])
    return tuple(_jitter(c, 10, rng) for c in base)


# -----------------------------
# intent analysis
# -----------------------------


def classify_texture_subject(fname: str) -> str:
    low = fname.lower()
    if any(k in low for k in ['water', 'bubble', 'wave', 'sea', 'river', 'splash']):
        return 'water'
    if any(k in low for k in ['lava', 'fire', 'flame', 'hot', 'burn', 'ember']):
        return 'lava'
    if any(k in low for k in ['grass', 'flower', 'hedge', 'vine']):
        return 'grass'
    if any(k in low for k in ['leaf', 'leaves', 'bush', 'foliage', 'pine_tree', 'tree_top']):
        return 'foliage'
    if any(k in low for k in ['stone', 'rock', 'castle', 'cobble', 'column']):
        return 'stone'
    if any(k in low for k in ['brick', 'masonry']):
        return 'brick'
    if any(k in low for k in ['wood', 'log', 'plank', 'crate', 'barrel']):
        return 'wood'
    if any(k in low for k in ['metal', 'chain', 'cannon', 'gear', 'iron', 'steel', 'bolt']):
        return 'metal'
    if any(k in low for k in ['sand', 'desert', 'dune']):
        return 'sand'
    if any(k in low for k in ['snow', 'ice', 'frost']):
        return 'snow'
    if 'cloud' in low:
        return 'cloud'
    if 'sky' in low or 'skybox' in low:
        return 'sky'
    if any(k in low for k in ['cloth', 'curtain', 'carpet', 'quilt', 'banner', 'mural']):
        return 'fabric'
    if any(k in low for k in ['eye', 'iris', 'pupil', 'blink']):
        return 'eye'
    if any(k in low for k in ['sign', 'board', 'arrow', 'message']):
        return 'sign'
    if 'door' in low:
        if 'metal' in low:
            return 'metal'
        if 'mural' in low:
            return 'fabric'
        return 'wood'
    return 'generic'


def classify_texture_role(fname: str) -> str:
    low = fname.lower()
    path = PurePosixPath(low)
    if 'overlay' in low:
        return 'overlay'
    if any(k in low for k in ['bubble', 'particle', 'spark', 'smoke', 'splash', 'ring', 'shadow']):
        return 'sprite'
    if any(k in low for k in ['eye', 'blink', 'mouth', 'face']):
        return 'face'
    if 'door' in low:
        return 'door'
    if 'signpost' in low or ('sign' in low and 'door' not in low):
        return 'sign'
    if 'box_' in low or '/box/' in low or 'exclamation_box' in low:
        return 'box'
    if 'wall' in low:
        return 'wall'
    if 'floor' in low:
        return 'floor'
    if 'skyboxes' in path.parts or 'skybox' in low:
        return 'skybox'
    return 'tile'


def analyze_texture_intent(fname: str):
    return {
        'subject': classify_texture_subject(fname),
        'role': classify_texture_role(fname),
        'fname': fname,
    }


# -----------------------------
# basic drawing helpers
# -----------------------------


def _vertical_gradient(draw, w, h, top, bottom):
    for y in range(h):
        t = y / max(h - 1, 1)
        draw.line((0, y, w, y), fill=_mix(top, bottom, t))


def _horizontal_gradient(draw, w, h, left, right):
    for x in range(w):
        t = x / max(w - 1, 1)
        draw.line((x, 0, x, h), fill=_mix(left, right, t))


def _soft_noise_points(draw, w, h, colors, rng, density=0.08):
    count = max(8, int(w * h * density))
    for _ in range(count):
        draw.point((rng.randint(0, w), rng.randint(0, h)), fill=_mix(colors[0], colors[2], rng.rand()))


# -----------------------------
# material renderers
# -----------------------------


def _draw_grass(draw, w, h, colors, rng):
    _vertical_gradient(draw, w, h, colors[2], colors[0])
    _soft_noise_points(draw, w, h, colors, rng, density=0.05)
    horizon = max(1, h // 3)
    for _ in range(max(12, w * h // 40)):
        x = rng.randint(0, w)
        base_y = rng.randint(horizon, h)
        length = rng.randint(max(2, h // 10), max(3, h // 3))
        bend = rng.randint(-max(1, w // 16), max(1, w // 16) + 1)
        draw.line((x, base_y, x + bend, base_y - length), fill=_jitter(colors[1], 10, rng), width=1)
    for _ in range(max(2, (w * h) // 300)):
        cx, cy = rng.randint(0, w), rng.randint(horizon, h)
        petal = _mix(colors[2], (250, 240, 210), rng.rand() * 0.5)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            draw.ellipse((cx + dx - 1, cy + dy - 1, cx + dx + 1, cy + dy + 1), fill=petal)
        draw.ellipse((cx - 1, cy - 1, cx + 1, cy + 1), fill=(235, 210, 70))


def _draw_foliage(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=colors[3])
    for _ in range(max(10, w * h // 64)):
        cx, cy = rng.randint(0, w), rng.randint(0, h)
        rw = rng.randint(max(2, w // 10), max(3, w // 4))
        rh = rng.randint(max(2, h // 10), max(3, h // 4))
        fill = _mix(colors[0], colors[2], rng.rand())
        draw.ellipse((cx - rw, cy - rh, cx + rw, cy + rh), fill=fill)
    for _ in range(max(6, w * h // 160)):
        x0, y0 = rng.randint(0, w), rng.randint(0, h)
        x1, y1 = x0 + rng.randint(-w // 6, w // 6 + 1), y0 + rng.randint(-h // 6, h // 6 + 1)
        draw.line((x0, y0, x1, y1), fill=_jitter(colors[3], 6, rng), width=1)


def _draw_water(draw, w, h, colors, rng):
    _vertical_gradient(draw, w, h, colors[2], colors[3])
    for band in range(max(3, h // 6)):
        y = int((band + 0.5) * h / max(3, h // 6))
        pts = []
        amp = max(1, h // 14)
        phase = rng.rand() * math.pi * 2
        for x in range(0, w + 2, 2):
            yy = y + int(math.sin((x / max(w, 1)) * math.pi * 2 + phase) * amp)
            pts.append((x, yy))
        draw.line(pts, fill=_jitter(colors[1], 6, rng), width=1)
    for _ in range(max(4, w * h // 256)):
        x, y = rng.randint(0, w), rng.randint(0, h)
        rw, rh = rng.randint(1, max(2, w // 10)), rng.randint(1, max(2, h // 14))
        draw.arc((x - rw, y - rh, x + rw, y + rh), 190, 350, fill=colors[2], width=1)


def _draw_lava(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=colors[0])
    for _ in range(max(8, w * h // 120)):
        x, y = rng.randint(0, w), rng.randint(0, h)
        rw, rh = rng.randint(max(2, w // 12), max(3, w // 5)), rng.randint(max(2, h // 12), max(3, h // 5))
        draw.ellipse((x - rw, y - rh, x + rw, y + rh), fill=_mix(colors[1], colors[2], rng.rand()))
    for _ in range(max(7, w * h // 160)):
        pts = []
        x = rng.randint(0, w)
        y = rng.randint(0, h)
        for _k in range(4):
            pts.append((x, y))
            x += rng.randint(-max(1, w // 7), max(1, w // 7) + 1)
            y += rng.randint(-max(1, h // 7), max(1, h // 7) + 1)
        draw.line(pts, fill=colors[3], width=1)


def _draw_stone(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=colors[1])
    cols = max(2, w // 10)
    rows = max(2, h // 10)
    cell_w = max(4, w // cols)
    cell_h = max(4, h // rows)
    for ry in range(rows + 1):
        y0 = ry * cell_h
        offset = (cell_w // 2) if ry % 2 else 0
        for cx in range(-1, cols + 1):
            x0 = cx * cell_w + offset
            x1 = x0 + cell_w + rng.randint(-1, 2)
            y1 = y0 + cell_h + rng.randint(-1, 2)
            fill = _mix(colors[0], colors[2], rng.rand())
            draw.rounded_rectangle((x0 + 1, y0 + 1, x1 - 1, y1 - 1), radius=1, fill=fill, outline=colors[3])
    for _ in range(max(4, w * h // 300)):
        x = rng.randint(0, w)
        y = rng.randint(0, h)
        draw.line((x, y, x + rng.randint(-5, 5), y + rng.randint(-5, 5)), fill=_jitter(colors[3], 4, rng), width=1)


def _draw_brick(draw, w, h, colors, rng):
    draw.rectangle((0, 0, w, h), fill=_mix(colors[2], (230, 220, 200), 0.55))
    brick_h = max(4, h // 5)
    brick_w = max(6, w // 4)
    row = 0
    for y in range(0, h + brick_h, brick_h):
        offset = brick_w // 2 if row % 2 else 0
        for x in range(-offset, w + brick_w, brick_w):
            fill = _mix(colors[0], colors[2], rng.rand() * 0.6)
            draw.rectangle((x + 1, y + 1, x + brick_w - 2, y + brick_h - 2), fill=fill, outline=colors[3])
            if rng.rand() > 0.6:
                crack_x = x + rng.randint(2, max(3, brick_w - 2))
                draw.line((crack_x, y + 2, crack_x + rng.randint(-1, 1), y + brick_h - 2), fill=_jitter(colors[3], 4, rng), width=1)
        row += 1


def _draw_wood(draw, w, h, colors, rng, role='tile'):
    if role in {'door', 'box'}:
        _vertical_gradient(draw, w, h, colors[2], colors[0])
        margin = max(2, min(w, h) // 10)
        panels = 2 if h >= w else 1
        draw.rectangle((0, 0, w - 1, h - 1), outline=colors[3], width=1)
        for p in range(panels):
            y0 = margin + p * (h - 2 * margin) // panels
            y1 = margin + (p + 1) * (h - 2 * margin) // panels - 1
            draw.rectangle((margin, y0, w - margin, y1), outline=_jitter(colors[3], 8, rng), width=1)
            for y in range(y0 + 1, y1, max(2, (y1 - y0) // 5)):
                phase = rng.rand() * math.pi * 2
                pts = []
                for x in range(margin, w - margin, 2):
                    pts.append((x, y + int(math.sin(phase + x / max(1, w) * math.pi * 2) * max(1, h // 40))))
                draw.line(pts, fill=_jitter(colors[1], 8, rng), width=1)
        knob_r = max(1, min(w, h) // 14)
        draw.ellipse((w - margin * 2 - knob_r, h // 2 - knob_r, w - margin * 2 + knob_r, h // 2 + knob_r), fill=_mix(colors[2], (220, 190, 90), 0.45), outline=colors[3])
    else:
        _vertical_gradient(draw, w, h, colors[2], colors[0])
        plank_h = max(4, h // 4)
        for y in range(0, h, plank_h):
            draw.rectangle((0, y, w - 1, min(h - 1, y + plank_h - 1)), outline=colors[3], width=1)
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


def _draw_metal(draw, w, h, colors, rng, role='tile'):
    _horizontal_gradient(draw, w, h, colors[2], colors[0])
    for x in range(0, w, max(2, w // 12)):
        draw.line((x, 0, x, h), fill=_jitter(colors[1], 7, rng), width=1)
    if role in {'door', 'box'}:
        margin = max(2, min(w, h) // 10)
        draw.rectangle((margin, margin, w - margin, h - margin), outline=colors[3], width=1)
        for x in [margin, w - margin]:
            for y in [margin, h - margin]:
                r = max(1, min(w, h) // 18)
                draw.ellipse((x - r, y - r, x + r, y + r), fill=colors[3], outline=colors[2])
        if role == 'door':
            r = max(1, min(w, h) // 16)
            draw.ellipse((w - margin * 2 - r, h // 2 - r, w - margin * 2 + r, h // 2 + r), fill=_mix(colors[2], (230, 215, 120), 0.25), outline=colors[3])
    else:
        step = max(4, min(w, h) // 3)
        for y in range(step // 2, h, step):
            for x in range(step // 2, w, step):
                r = max(1, min(w, h) // 14)
                draw.ellipse((x - r, y - r, x + r, y + r), fill=colors[3], outline=colors[2])


def _draw_sand(draw, w, h, colors, rng):
    _vertical_gradient(draw, w, h, colors[2], colors[0])
    _soft_noise_points(draw, w, h, colors, rng, density=0.08)
    for band in range(max(4, h // 5)):
        y = int((band + 0.5) * h / max(4, h // 5))
        pts = []
        phase = rng.rand() * math.pi * 2
        amp = max(1, h // 18)
        for x in range(0, w + 2, 2):
            pts.append((x, y + int(math.sin(phase + x / max(1, w) * math.pi * 2) * amp)))
        draw.line(pts, fill=_jitter(colors[1], 8, rng), width=1)


def _draw_snow(draw, w, h, colors, rng):
    _vertical_gradient(draw, w, h, colors[1], colors[2])
    for _ in range(max(10, w * h // 80)):
        x, y = rng.randint(0, w), rng.randint(0, h)
        draw.point((x, y), fill=colors[2])
        if rng.rand() > 0.75:
            draw.line((x - 1, y, x + 1, y), fill=colors[2], width=1)
            draw.line((x, y - 1, x, y + 1), fill=colors[2], width=1)
    for band in range(max(2, h // 10)):
        y = int((band + 0.5) * h / max(2, h // 10))
        draw.arc((0, y - h // 8, w, y + h // 8), 0, 180, fill=_mix(colors[0], colors[2], 0.3), width=1)


def _draw_sky(draw, w, h, colors, rng, cloudy=False, night=False):
    if night:
        _vertical_gradient(draw, w, h, (18, 28, 74), (104, 134, 190))
        for _ in range(max(10, w * h // 120)):
            x, y = rng.randint(0, w), rng.randint(0, max(1, h * 3 // 4))
            draw.point((x, y), fill=(240, 245, 255))
    else:
        _vertical_gradient(draw, w, h, colors[2], colors[0])
    if cloudy:
        for _ in range(max(3, (w * h) // 220)):
            cx, cy = rng.randint(0, w), rng.randint(0, h)
            rw, rh = rng.randint(max(2, w // 8), max(3, w // 4)), rng.randint(max(2, h // 10), max(3, h // 5))
            fill = (255, 255, 255, 220)
            for dx in [-rw // 2, 0, rw // 2]:
                draw.ellipse((cx + dx - rw // 2, cy - rh // 2, cx + dx + rw // 2, cy + rh // 2), fill=fill)
    else:
        for _ in range(max(2, (w * h) // 360)):
            x = rng.randint(0, w)
            y = rng.randint(0, max(1, h * 2 // 3))
            rw = rng.randint(max(2, w // 10), max(3, w // 5))
            rh = rng.randint(max(1, h // 12), max(2, h // 8))
            draw.ellipse((x - rw, y - rh, x + rw, y + rh), fill=(255, 255, 255, 180))


def _draw_fabric(draw, w, h, colors, rng, role='tile'):
    draw.rectangle((0, 0, w, h), fill=colors[1])
    step = max(3, min(w, h) // 6)
    for i in range(-h, w, step):
        draw.line((i, 0, i + h, h), fill=_jitter(colors[2], 6, rng), width=1)
    for i in range(0, w + h, step):
        draw.line((i, 0, i - h, h), fill=_jitter(colors[0], 6, rng), width=1)
    draw.rectangle((0, 0, w - 1, h - 1), outline=colors[3], width=1)
    if role in {'door', 'sign'}:
        margin = max(2, min(w, h) // 10)
        draw.rectangle((margin, margin, w - margin, h - margin), outline=_mix(colors[2], (255, 220, 120), 0.3), width=1)


def _draw_sign(draw, w, h, colors, rng):
    _draw_wood(draw, w, h, colors, rng, role='door')
    pad = max(2, min(w, h) // 8)
    draw.rectangle((pad, pad, w - pad, h - pad), fill=_mix(colors[2], (240, 230, 190), 0.5), outline=colors[3], width=1)
    line_count = max(2, (h - 2 * pad) // max(3, h // 7))
    for i in range(line_count):
        y = pad + (i + 1) * (h - 2 * pad) // (line_count + 1)
        x0 = pad * 2
        x1 = w - pad * 2 - rng.randint(0, max(1, w // 8))
        draw.line((x0, y, x1, y), fill=_jitter(colors[3], 10, rng), width=1)
    if rng.rand() > 0.5:
        ay = h - pad * 2
        draw.polygon([(pad * 2, ay), (w // 2, h - pad), (w - pad * 2, ay)], fill=_mix(colors[1], colors[3], 0.4))


def _draw_eye(draw, w, h, colors, rng, fname=''):
    draw.rectangle((0, 0, w, h), fill=(0, 0, 0, 0))
    margin_x = max(1, w // 12)
    margin_y = max(1, h // 5)
    if 'closed' in fname or 'blink' in fname:
        draw.line((margin_x, h // 2, w - margin_x, h // 2), fill=colors[3], width=max(1, h // 8))
        return
    draw.ellipse((margin_x, margin_y, w - margin_x, h - margin_y), fill=colors[1], outline=colors[3])
    cx = w // 2 + rng.randint(-max(1, w // 12), max(1, w // 12) + 1)
    cy = h // 2 + rng.randint(-max(1, h // 12), max(1, h // 12) + 1)
    iris_r = max(1, min(w, h) // 5)
    pupil_r = max(1, min(w, h) // 9)
    draw.ellipse((cx - iris_r, cy - iris_r, cx + iris_r, cy + iris_r), fill=colors[2])
    draw.ellipse((cx - pupil_r, cy - pupil_r, cx + pupil_r, cy + pupil_r), fill=colors[3])
    draw.ellipse((cx - 1, cy - 1, cx + 1, cy + 1), fill=colors[1])


def _draw_box(draw, w, h, colors, rng, subject='generic'):
    if subject == 'metal':
        _draw_metal(draw, w, h, colors, rng, role='box')
    elif subject == 'wood':
        _draw_wood(draw, w, h, colors, rng, role='box')
    else:
        draw.rectangle((0, 0, w, h), fill=colors[1], outline=colors[3], width=1)
    pad = max(2, min(w, h) // 6)
    # emblem star or exclamation cue
    if w > 8 and h > 8:
        cx, cy = w // 2, h // 2
        r1 = max(2, min(w, h) // 5)
        r2 = max(1, r1 // 2)
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            r = r1 if i % 2 == 0 else r2
            pts.append((cx + int(math.cos(ang) * r), cy + int(math.sin(ang) * r)))
        draw.polygon(pts, fill=_mix(colors[2], (255, 231, 88), 0.4), outline=colors[3])


# -----------------------------
# sprite / overlay renderers
# -----------------------------


def _draw_bubble_sprite(draw, w, h, colors, rng):
    cx, cy = w // 2, h // 2
    r = max(2, min(w, h) // 3)
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(220, 245, 255, 220), width=1, fill=(180, 230, 255, 50))
    draw.arc((cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1), 210, 320, fill=(255, 255, 255, 200), width=1)
    draw.ellipse((cx - r // 2, cy - r // 2, cx - r // 4, cy - r // 4), fill=(255, 255, 255, 160))


def _draw_ring_sprite(draw, w, h, colors, rng):
    cx, cy = w // 2, h // 2
    r = max(3, min(w, h) // 3)
    r2 = max(1, r - max(1, min(w, h) // 8))
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=_mix(colors[2], (255, 255, 255), 0.25), width=2)
    draw.ellipse((cx - r2, cy - r2, cx + r2, cy + r2), outline=(0, 0, 0, 0), width=1)


def _draw_particle_sprite(draw, w, h, colors, rng, subject='generic'):
    cx, cy = w // 2, h // 2
    if subject == 'snow':
        for ang in [0, math.pi / 3, 2 * math.pi / 3]:
            dx = int(math.cos(ang) * max(2, w // 3))
            dy = int(math.sin(ang) * max(2, h // 3))
            draw.line((cx - dx, cy - dy, cx + dx, cy + dy), fill=(250, 252, 255, 220), width=1)
    elif subject == 'water':
        _draw_bubble_sprite(draw, w, h, colors, rng)
    elif subject == 'lava':
        r = max(2, min(w, h) // 4)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=_mix(colors[1], colors[2], 0.5), outline=colors[3])
    else:
        r = max(2, min(w, h) // 4)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=_mix(colors[1], colors[2], 0.5))


def _draw_overlay_emblem(draw, w, h, colors, rng, subject='generic'):
    if subject in {'metal', 'wood', 'fabric'}:
        cx, cy = w // 2, h // 2
        r1 = max(3, min(w, h) // 4)
        r2 = max(1, r1 // 2)
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            r = r1 if i % 2 == 0 else r2
            pts.append((cx + int(math.cos(ang) * r), cy + int(math.sin(ang) * r)))
        draw.polygon(pts, fill=_mix(colors[2], (255, 220, 100), 0.35), outline=colors[3])
    else:
        _draw_particle_sprite(draw, w, h, colors, rng, subject=subject)


# -----------------------------
# dispatch
# -----------------------------


def render_pil_texture(fname: str, shape, rng=None, identity=None):
    h, w = int(shape[0]), int(shape[1])
    local_rng = _to_rng(rng, fname)
    intent = analyze_texture_intent(fname)
    subject = intent['subject']
    role = intent['role']
    colors = _palette(subject, local_rng)

    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if role == 'sprite':
        if 'ring' in fname.lower():
            _draw_ring_sprite(draw, w, h, colors, local_rng)
        else:
            _draw_particle_sprite(draw, w, h, colors, local_rng, subject=subject)
    elif role == 'overlay':
        _draw_overlay_emblem(draw, w, h, colors, local_rng, subject=subject)
    elif role == 'face':
        _draw_eye(draw, w, h, colors, local_rng, fname=fname.lower())
    elif role == 'door':
        if subject == 'metal':
            _draw_metal(draw, w, h, colors, local_rng, role='door')
        elif subject == 'fabric':
            _draw_fabric(draw, w, h, colors, local_rng, role='door')
        else:
            _draw_wood(draw, w, h, colors, local_rng, role='door')
    elif role == 'sign':
        _draw_sign(draw, w, h, colors, local_rng)
    elif role == 'box':
        _draw_box(draw, w, h, colors, local_rng, subject=subject)
    elif role == 'skybox':
        _draw_sky(draw, w, h, colors, local_rng, cloudy=True, night='bitfs' in fname.lower() or 'bbh' in fname.lower())
    else:
        if subject == 'grass':
            _draw_grass(draw, w, h, colors, local_rng)
        elif subject == 'foliage':
            _draw_foliage(draw, w, h, colors, local_rng)
        elif subject == 'water':
            _draw_water(draw, w, h, colors, local_rng)
        elif subject == 'lava':
            _draw_lava(draw, w, h, colors, local_rng)
        elif subject == 'stone':
            _draw_stone(draw, w, h, colors, local_rng)
        elif subject == 'brick':
            _draw_brick(draw, w, h, colors, local_rng)
        elif subject == 'wood':
            _draw_wood(draw, w, h, colors, local_rng)
        elif subject == 'metal':
            _draw_metal(draw, w, h, colors, local_rng)
        elif subject == 'sand':
            _draw_sand(draw, w, h, colors, local_rng)
        elif subject == 'snow':
            _draw_snow(draw, w, h, colors, local_rng)
        elif subject == 'sky':
            _draw_sky(draw, w, h, colors, local_rng, cloudy=False)
        elif subject == 'cloud':
            _draw_sky(draw, w, h, colors, local_rng, cloudy=True)
        elif subject == 'fabric':
            _draw_fabric(draw, w, h, colors, local_rng)
        elif subject == 'sign':
            _draw_sign(draw, w, h, colors, local_rng)
        else:
            # structured fallback: choose by likely architectural use
            if role == 'floor':
                _draw_stone(draw, w, h, colors, local_rng)
            elif role == 'wall':
                _draw_brick(draw, w, h, colors, local_rng)
            else:
                _draw_wood(draw, w, h, colors, local_rng)

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


__all__ = ['analyze_texture_intent', 'classify_texture_role', 'classify_texture_subject', 'render_pil_texture']
