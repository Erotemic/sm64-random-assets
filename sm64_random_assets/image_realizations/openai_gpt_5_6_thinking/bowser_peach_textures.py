from __future__ import annotations

import math
import re

import numpy as np
from PIL import Image, ImageDraw


FAKEOUT_PORTRAIT_FILES = {
    'levels/castle_inside/5.rgba16.png': 'peach',
    'levels/castle_inside/6.rgba16.png': 'bowser',
}


def supports_bowser_peach_texture(identity, info) -> bool:
    fname = identity.fname
    return (
        fname in FAKEOUT_PORTRAIT_FILES
        or fname.startswith('actors/bowser/')
        or fname.startswith('actors/peach/')
        or fname.startswith('actors/bowser_flame/')
    )


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


def _paint_gradient(draw, size, top, bottom):
    w, h = size
    for y in range(h):
        t = y / max(1, h - 1)
        color = tuple(int(round(a + (b - a) * t)) for a, b in zip(top, bottom))
        draw.line((0, y, w, y), fill=color)


def _draw_frame(draw, w, h, s):
    outer = max(2, 2 * s)
    inner = max(1, s)
    # Draw only the border bands; do not cover the portrait interior.
    draw.rectangle((0, 0, w - 1, h - 1), outline=(57, 35, 27, 255), width=max(1, 3 * s))
    draw.rectangle((outer, outer, w - 1 - outer, h - 1 - outer), outline=(218, 163, 65, 255), width=max(1, 2 * s))
    draw.rectangle((outer + 3 * s, outer + 3 * s, w - 1 - outer - 3 * s, h - 1 - outer - 3 * s), outline=(116, 70, 32, 255), width=inner)
    # Four corner ornaments stay readable after downsampling.
    for cx, cy in [(5 * s, 5 * s), (w - 5 * s, 5 * s), (5 * s, h - 5 * s), (w - 5 * s, h - 5 * s)]:
        r = max(1, 2 * s)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(239, 194, 88, 255), outline=(89, 52, 24, 255))


def _render_peach_fakeout(shape, rng):
    img, draw, s = _canvas(shape, scale=6, background=(25, 32, 79, 255))
    w, h = img.size
    _paint_gradient(draw, (w, h), (38, 59, 125, 255), (117, 43, 103, 255))
    # Soft palace-window halo.
    draw.ellipse((w * 0.22, -h * 0.20, w * 0.78, h * 0.90), fill=(240, 221, 177, 60))
    for idx in range(14):
        x = int(rng.randint(w * 0.12, w * 0.88))
        y = int(rng.randint(h * 0.08, h * 0.88))
        r = int(rng.randint(max(1, s // 2), max(2, s + 1)))
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(255, 241, 194, int(rng.randint(40, 105))))

    cx = w * 0.50
    # Hair mass, neck, and dress first.
    hair = (247, 197, 69, 255)
    hair_shadow = (190, 126, 42, 255)
    draw.ellipse((w * 0.22, h * 0.14, w * 0.78, h * 1.10), fill=hair_shadow)
    draw.ellipse((w * 0.25, h * 0.10, w * 0.75, h * 0.92), fill=hair)
    draw.rectangle((cx - 5*s, h * 0.60, cx + 5*s, h * 0.78), fill=(247, 193, 154, 255))
    draw.polygon([
        (w * 0.14, h), (w * 0.25, h * 0.67), (w * 0.42, h * 0.61),
        (w * 0.58, h * 0.61), (w * 0.75, h * 0.67), (w * 0.86, h),
    ], fill=(228, 82, 143, 255), outline=(119, 37, 78, 255))
    draw.arc((w * 0.17, h * 0.61, w * 0.83, h * 1.08), 190, 350, fill=(255, 172, 206, 255), width=max(1, 2*s))

    # Face and ears.
    face_box = (w * 0.33, h * 0.20, w * 0.67, h * 0.70)
    draw.ellipse(face_box, fill=(255, 210, 174, 255), outline=(161, 99, 77, 255), width=max(1, s))
    draw.ellipse((w * 0.29, h * 0.37, w * 0.36, h * 0.50), fill=(255, 202, 169, 255))
    draw.ellipse((w * 0.64, h * 0.37, w * 0.71, h * 0.50), fill=(255, 202, 169, 255))
    # Hair fringe.
    draw.polygon([
        (w * 0.32, h * 0.29), (w * 0.39, h * 0.15), (w * 0.47, h * 0.27),
        (w * 0.54, h * 0.13), (w * 0.68, h * 0.30), (w * 0.62, h * 0.21),
        (w * 0.36, h * 0.22),
    ], fill=hair)

    # Crown and gems.
    crown_y = h * 0.11
    draw.polygon([
        (w * 0.39, crown_y + 7*s), (w * 0.40, crown_y), (w * 0.46, crown_y + 5*s),
        (w * 0.50, crown_y - 2*s), (w * 0.54, crown_y + 5*s), (w * 0.60, crown_y),
        (w * 0.61, crown_y + 7*s),
    ], fill=(245, 194, 49, 255), outline=(117, 72, 20, 255))
    draw.ellipse((cx - 2*s, crown_y + 2*s, cx + 2*s, crown_y + 6*s), fill=(55, 160, 229, 255))

    # Eyes, brows, nose, lips.
    for ex in (w * 0.42, w * 0.58):
        draw.ellipse((ex - 3*s, h * 0.38, ex + 3*s, h * 0.49), fill=(250, 250, 246, 255), outline=(74, 50, 55, 255))
        draw.ellipse((ex - 1.5*s, h * 0.395, ex + 1.5*s, h * 0.48), fill=(58, 139, 218, 255))
        draw.ellipse((ex - 0.5*s, h * 0.41, ex + 0.5*s, h * 0.48), fill=(27, 35, 65, 255))
        draw.line((ex - 3*s, h * 0.37, ex + 3*s, h * 0.36), fill=(91, 52, 52, 255), width=max(1, s))
    draw.line((cx, h * 0.48, cx - s, h * 0.55), fill=(187, 112, 92, 255), width=max(1, s))
    draw.arc((cx - 4*s, h * 0.54, cx + 4*s, h * 0.63), 15, 165, fill=(177, 45, 89, 255), width=max(1, 2*s))
    # Earrings and chest jewel.
    for ex in (w * 0.315, w * 0.685):
        draw.ellipse((ex - 2*s, h * 0.48, ex + 2*s, h * 0.56), fill=(70, 178, 232, 255), outline=(225, 238, 246, 255))
    draw.ellipse((cx - 3*s, h * 0.69, cx + 3*s, h * 0.79), fill=(58, 179, 232, 255), outline=(242, 246, 245, 255))

    _draw_frame(draw, w, h, s)
    return _finish(img, shape)


def _render_bowser_fakeout(shape, rng):
    img, draw, s = _canvas(shape, scale=6, background=(35, 12, 24, 255))
    w, h = img.size
    _paint_gradient(draw, (w, h), (55, 17, 45, 255), (135, 28, 24, 255))
    # Fire and smoke silhouette in the background.
    for idx in range(11):
        x = w * (0.08 + idx * 0.084)
        flame_h = h * (0.22 + 0.12 * math.sin(idx * 1.7))
        draw.polygon([
            (x - 4*s, h), (x - 2*s, h - flame_h * 0.45), (x, h - flame_h),
            (x + 2*s, h - flame_h * 0.40), (x + 5*s, h),
        ], fill=(227, 67, 24, 110))

    cx = w * 0.50
    # Shell/back mass and red mane.
    draw.ellipse((w * 0.17, h * 0.25, w * 0.83, h * 1.10), fill=(42, 102, 55, 255), outline=(17, 48, 27, 255), width=max(1, 2*s))
    mane = (184, 42, 25, 255)
    mane_pts = []
    for idx in range(15):
        angle = math.pi * (1.04 + idx / 14 * 0.92)
        r = w * (0.25 if idx % 2 else 0.31)
        mane_pts.append((cx + math.cos(angle) * r, h * 0.47 + math.sin(angle) * h * 0.39))
    mane_pts += [(w * 0.72, h * 0.75), (w * 0.28, h * 0.75)]
    draw.polygon(mane_pts, fill=mane)

    # Head and muzzle.
    draw.ellipse((w * 0.29, h * 0.18, w * 0.71, h * 0.72), fill=(110, 169, 57, 255), outline=(35, 73, 31, 255), width=max(1, 2*s))
    draw.ellipse((w * 0.34, h * 0.45, w * 0.66, h * 0.76), fill=(225, 151, 52, 255), outline=(107, 65, 26, 255), width=max(1, s))
    # Horns.
    draw.polygon([(w * 0.34, h * 0.28), (w * 0.19, h * 0.09), (w * 0.40, h * 0.18)], fill=(241, 222, 161, 255), outline=(101, 76, 41, 255))
    draw.polygon([(w * 0.66, h * 0.28), (w * 0.81, h * 0.09), (w * 0.60, h * 0.18)], fill=(241, 222, 161, 255), outline=(101, 76, 41, 255))
    # Eyes and angry brows.
    for ex in (w * 0.42, w * 0.58):
        draw.polygon([(ex - 3*s, h * 0.35), (ex + 3*s, h * 0.35), (ex + 2*s, h * 0.48), (ex - 2*s, h * 0.48)], fill=(247, 224, 130, 255), outline=(36, 29, 25, 255))
        draw.ellipse((ex - s, h * 0.39, ex + s, h * 0.47), fill=(180, 36, 22, 255))
        draw.line((ex - 4*s, h * 0.32, ex + 3*s, h * 0.36), fill=(57, 24, 20, 255), width=max(1, 2*s))
    # Nose, mouth, fangs.
    draw.ellipse((cx - 5*s, h * 0.48, cx + 5*s, h * 0.57), fill=(182, 105, 36, 255))
    draw.ellipse((cx - 4*s, h * 0.50, cx - 1*s, h * 0.55), fill=(35, 25, 22, 255))
    draw.ellipse((cx + 1*s, h * 0.50, cx + 4*s, h * 0.55), fill=(35, 25, 22, 255))
    draw.arc((w * 0.36, h * 0.52, w * 0.64, h * 0.70), 5, 175, fill=(65, 24, 20, 255), width=max(1, 2*s))
    draw.polygon([(w * 0.40, h * 0.61), (w * 0.44, h * 0.61), (w * 0.42, h * 0.72)], fill=(247, 232, 187, 255))
    draw.polygon([(w * 0.56, h * 0.61), (w * 0.60, h * 0.61), (w * 0.58, h * 0.72)], fill=(247, 232, 187, 255))

    _draw_frame(draw, w, h, s)
    return _finish(img, shape)


def _hex_pattern(draw, w, h, s, fill_a, fill_b, outline):
    radius = max(3*s, min(w, h) // 8)
    dx = radius * 1.55
    dy = radius * 1.35
    row = 0
    y = -radius
    while y < h + radius:
        x = -radius + (dx * 0.5 if row % 2 else 0)
        while x < w + radius:
            pts = []
            for k in range(6):
                ang = math.pi / 3 * k
                pts.append((x + math.cos(ang) * radius, y + math.sin(ang) * radius))
            draw.polygon(pts, fill=fill_a if (int(x / max(dx, 1)) + row) % 2 else fill_b, outline=outline)
            x += dx
        y += dy
        row += 1


def _render_bowser_actor(fname, shape, rng):
    low = fname.lower()
    img, draw, s = _canvas(shape, scale=4, background=(0, 0, 0, 255))
    w, h = img.size
    cx, cy = w / 2, h / 2

    if 'shell_edge' in low:
        _paint_gradient(draw, (w, h), (239, 207, 96, 255), (151, 105, 32, 255))
        for x in range(-h, w + h, max(4*s, w // 8)):
            draw.line((x, 0, x + h, h), fill=(255, 237, 155, 120), width=max(1, s))
    elif 'shell' in low:
        _paint_gradient(draw, (w, h), (55, 129, 54, 255), (21, 69, 34, 255))
        _hex_pattern(draw, w, h, s, (69, 147, 61, 255), (44, 111, 48, 255), (24, 65, 30, 255))
        for _ in range(max(2, w*h // (180*s*s))):
            x = int(rng.randint(0, w)); y = int(rng.randint(0, h)); r = max(2*s, min(w,h)//10)
            draw.polygon([(x-r, y+r), (x, y-r), (x+r, y+r)], fill=(240, 224, 170, 230), outline=(100, 77, 43, 255))
    elif 'armband_spike' in low or any(token in low for token in ['claw_edge', 'claw_horn', 'tooth']):
        _paint_gradient(draw, (w, h), (255, 244, 203, 255), (166, 137, 87, 255))
        for x in range(0, w, max(5*s, w//5)):
            draw.polygon([(x, h), (min(w, x + w//8), 0), (min(w, x + w//4), h)], fill=(246, 232, 184, 255), outline=(116, 91, 54, 255))
    elif 'armband' in low:
        _paint_gradient(draw, (w, h), (60, 58, 57, 255), (20, 20, 22, 255))
        for x in range(max(3*s, w//10), w, max(7*s, w//4)):
            r = max(2*s, min(w,h)//9)
            draw.ellipse((x-r, cy-r, x+r, cy+r), fill=(192, 199, 203, 255), outline=(63, 65, 67, 255))
    elif 'chest' in low:
        _paint_gradient(draw, (w, h), (239, 190, 91, 255), (184, 123, 44, 255))
        plate_h = max(4*s, h//5)
        for y in range(0, h, plate_h):
            y0 = min(h - s, y + s)
            y1 = min(h - s, y + plate_h)
            if y1 < y0:
                continue
            draw.rounded_rectangle((s, y0, w-s, y1), radius=max(1, 2*s), outline=(113, 71, 30, 255), width=max(1,s))
            draw.line((2*s, min(h-s, y+2*s), w-2*s, min(h-s, y+2*s)), fill=(255, 225, 144, 120), width=max(1,s))
    elif 'hair' in low or 'eyebrow' in low:
        draw.rectangle((0, 0, w, h), fill=(130, 35, 22, 255))
        spike = max(4*s, w//8)
        for x in range(-spike, w + spike, spike):
            draw.polygon([(x, h), (x + spike//2, 0), (x + spike, h)], fill=(197, 54, 27, 255), outline=(84, 25, 20, 255))
    elif 'tongue' in low:
        _paint_gradient(draw, (w, h), (235, 91, 116, 255), (139, 42, 72, 255))
        draw.line((cx, 0, cx, h), fill=(103, 31, 54, 90), width=max(1, s))
    elif 'nostril' in low:
        draw.rectangle((0, 0, w, h), fill=(213, 137, 48, 255))
        draw.ellipse((w*.18, h*.25, w*.43, h*.78), fill=(38, 29, 23, 255))
        draw.ellipse((w*.57, h*.25, w*.82, h*.78), fill=(38, 29, 23, 255))
    elif 'muzzle' in low:
        _paint_gradient(draw, (w, h), (235, 164, 70, 255), (185, 108, 38, 255))
        draw.ellipse((w*.08, h*.25, w*.92, h*.90), outline=(105, 61, 28, 255), width=max(1,2*s))
        for _ in range(10):
            x = int(rng.randint(w*.2, w*.8)); y = int(rng.randint(h*.45, h*.8)); r=max(1,s)
            draw.ellipse((x-r,y-r,x+r,y+r), fill=(116, 71, 35, 150))
    elif 'mouth' in low:
        _paint_gradient(draw, (w, h), (73, 24, 27, 255), (24, 11, 15, 255))
        draw.arc((w*.12,h*.10,w*.88,h*.90), 5, 175, fill=(236, 220, 173, 255), width=max(1,2*s))
    elif 'eye' in low:
        draw.rectangle((0, 0, w, h), fill=(111, 169, 58, 255))
        closed = 'closed' in low
        half = 'half_closed' in low
        direction = 0.0
        if 'far_left' in low: direction = -0.28
        elif 'left' in low: direction = -0.16
        elif 'right' in low: direction = 0.16
        if closed:
            draw.arc((w*.12,h*.25,w*.88,h*.80), 195, 345, fill=(45, 31, 25, 255), width=max(1,3*s))
        else:
            top = h*.34 if half else h*.18
            bottom = h*.68 if half else h*.84
            draw.ellipse((w*.14,top,w*.86,bottom), fill=(246, 225, 139, 255), outline=(50, 36, 27, 255), width=max(1,s))
            px = cx + direction*w
            iris = (54, 120, 208, 255) if 'blue_eye' in low else (195, 51, 25, 255)
            draw.ellipse((px-w*.09,h*.30,px+w*.09,h*.73), fill=iris, outline=(42,28,25,255))
            draw.ellipse((px-w*.025,h*.34,px+w*.025,h*.72), fill=(20,17,19,255))
            draw.ellipse((px-w*.04,h*.31,px-w*.015,h*.39), fill=(255,255,245,220))
    elif 'upper_face' in low:
        _paint_gradient(draw, (w, h), (128, 184, 63, 255), (65, 118, 42, 255))
        draw.polygon([(0,h*.4),(w*.35,h*.12),(w*.5,h*.4),(w*.65,h*.12),(w,h*.4),(w,h),(0,h)], fill=(107,163,55,255))
    else:  # body / general Bowser skin
        _paint_gradient(draw, (w, h), (225, 151, 54, 255), (104, 154, 53, 255))
        _hex_pattern(draw, w, h, s, (216, 143, 50, 95), (116, 165, 61, 95), (84, 104, 44, 110))
    return _finish(img, shape)


def _render_peach_actor(fname, shape, rng):
    low = fname.lower()
    img, draw, s = _canvas(shape, scale=4, background=(255, 207, 174, 255))
    w, h = img.size
    cx, cy = w / 2, h / 2

    if 'jewel' in low:
        draw.rectangle((0,0,w,h), fill=(20, 72, 112, 255))
        gem = [(cx, h*.05), (w*.88,h*.34), (w*.68,h*.88), (w*.32,h*.88), (w*.12,h*.34)]
        draw.polygon(gem, fill=(54, 184, 232, 255), outline=(225, 245, 251, 255))
        draw.polygon([(cx,h*.08),(w*.48,h*.46),(w*.16,h*.34)], fill=(166, 235, 251, 210))
        draw.polygon([(cx,h*.08),(w*.52,h*.46),(w*.84,h*.34)], fill=(65, 143, 220, 210))
        draw.polygon([(w*.48,h*.46),(w*.52,h*.46),(w*.66,h*.84),(w*.34,h*.84)], fill=(30, 111, 188, 220))
    elif 'dress' in low:
        _paint_gradient(draw, (w,h), (255, 172, 211, 255), (199, 61, 129, 255))
        for y in range(0, h, max(5*s,h//6)):
            draw.arc((0,y-h*.18,w,y+h*.28), 10, 170, fill=(255,222,235,90), width=max(1,s))
        for _ in range(max(4,w*h//(180*s*s))):
            x=int(rng.randint(0,w)); y=int(rng.randint(0,h)); r=max(1,s)
            draw.ellipse((x-r,y-r,x+r,y+r), fill=(255,235,244,80))
    elif 'eye' in low:
        draw.rectangle((0,0,w,h), fill=(255,210,177,255))
        if 'closed' in low and 'mostly' not in low:
            draw.arc((w*.12,h*.25,w*.88,h*.78), 190, 350, fill=(87,48,54,255), width=max(1,3*s))
            for i in range(4):
                x=w*(.26+i*.16)
                draw.line((x,h*.61,x-w*.03,h*.72), fill=(87,48,54,255), width=max(1,s))
        else:
            openness = .35 if 'mostly_closed' in low else (.60 if 'mostly_open' in low else .82)
            top=cy-h*openness/2; bottom=cy+h*openness/2
            draw.ellipse((w*.13,top,w*.87,bottom), fill=(251,249,247,255), outline=(93,50,57,255), width=max(1,s))
            draw.ellipse((cx-w*.11,top+h*.04,cx+w*.11,bottom-h*.02), fill=(56,142,218,255))
            draw.ellipse((cx-w*.035,top+h*.06,cx+w*.035,bottom-h*.01), fill=(25,37,67,255))
            for i in range(4):
                x=w*(.25+i*.17)
                draw.line((x,top+s,x-w*.025,max(0,top-3*s)), fill=(83,43,51,255), width=max(1,s))
    elif 'lips' in low:
        draw.rectangle((0,0,w,h), fill=(255,210,177,255))
        if 'scrunched' in low:
            draw.polygon([(w*.27,cy),(cx,cy-h*.10),(w*.73,cy),(cx,cy+h*.13)], fill=(190,48,92,255), outline=(116,34,62,255))
        else:
            draw.arc((w*.18,h*.28,w*.82,h*.72), 8, 172, fill=(196,49,93,255), width=max(2,4*s))
            draw.arc((w*.20,h*.38,w*.80,h*.78), 188, 352, fill=(149,37,72,255), width=max(1,2*s))
    elif 'nostril' in low:
        draw.rectangle((0,0,w,h), fill=(255,210,177,255))
        draw.arc((w*.28,h*.20,w*.72,h*.78), 25, 155, fill=(180,107,92,255), width=max(1,2*s))
    else:
        _paint_gradient(draw, (w,h), (255,213,184,255), (239,175,150,255))
    return _finish(img, shape)


def _render_bowser_flame(fname, shape, rng):
    img, draw, s = _canvas(shape, scale=4, background=(0, 0, 0, 0))
    w, h = img.size
    match = re.search(r'_(\d+)\.', fname)
    frame = int(match.group(1)) if match else 0
    phase = frame / 14.0 * math.tau
    cx = w * (0.50 + 0.05 * math.sin(phase))
    base_y = h * 0.94
    outer_h = h * (0.66 + 0.12 * math.sin(phase + 0.8))
    outer_w = w * (0.29 + 0.05 * math.cos(phase * 1.3))
    outer = [
        (cx - outer_w, base_y),
        (cx - outer_w * .72, base_y - outer_h * .38),
        (cx - outer_w * .30, base_y - outer_h * .60),
        (cx - outer_w * .08, base_y - outer_h),
        (cx + outer_w * .18, base_y - outer_h * .66),
        (cx + outer_w * .74, base_y - outer_h * .40),
        (cx + outer_w, base_y),
    ]
    draw.polygon(outer, fill=(213, 43, 20, 230))
    mid = [
        (cx - outer_w * .62, base_y),
        (cx - outer_w * .42, base_y - outer_h * .38),
        (cx - outer_w * .08, base_y - outer_h * .73),
        (cx + outer_w * .16, base_y - outer_h * .46),
        (cx + outer_w * .60, base_y),
    ]
    draw.polygon(mid, fill=(247, 119, 25, 245))
    inner = [
        (cx - outer_w * .35, base_y),
        (cx - outer_w * .12, base_y - outer_h * .44),
        (cx + outer_w * .12, base_y - outer_h * .24),
        (cx + outer_w * .34, base_y),
    ]
    draw.polygon(inner, fill=(255, 231, 111, 255))
    # Small frame-dependent embers create visible animation differentiation.
    for idx in range(3):
        ex = cx + math.sin(phase + idx * 2.1) * outer_w * .75
        ey = base_y - outer_h * (.72 + idx * .09)
        r = max(1, int((2 + idx) * s * .55))
        draw.ellipse((ex-r,ey-r,ex+r,ey+r), fill=(255, 151, 42, 150))
    return _finish(img, shape)


def render_bowser_peach_texture(fname: str, shape, rng=None, identity=None):
    local_rng = _local_rng(rng, fname)
    if fname in FAKEOUT_PORTRAIT_FILES:
        if FAKEOUT_PORTRAIT_FILES[fname] == 'peach':
            return _render_peach_fakeout(shape, local_rng)
        return _render_bowser_fakeout(shape, local_rng)
    if fname.startswith('actors/bowser_flame/'):
        return _render_bowser_flame(fname, shape, local_rng)
    if fname.startswith('actors/bowser/'):
        return _render_bowser_actor(fname, shape, local_rng)
    if fname.startswith('actors/peach/'):
        return _render_peach_actor(fname, shape, local_rng)
    return None


__all__ = [
    'FAKEOUT_PORTRAIT_FILES',
    'render_bowser_peach_texture',
    'supports_bowser_peach_texture',
]
