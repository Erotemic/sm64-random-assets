from __future__ import annotations

import dataclasses as dc
import fnmatch
import math
import re
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw

from . import pil_textures


@dc.dataclass(frozen=True)
class FrequentTextureSpec:
    name: str
    patterns: tuple[str, ...]
    exposure_score: float
    renderer: str
    reason: str


FREQUENT_TEXTURE_SPECS = (
    FrequentTextureSpec(
        name='mario_details',
        patterns=('actors/mario/*', 'actors/mario_cap/*'),
        exposure_score=1.00,
        renderer='mario',
        reason='Player avatar textures are visible throughout normal play.',
    ),
    FrequentTextureSpec(
        name='collectibles',
        patterns=('actors/star/*', 'actors/coin/*'),
        exposure_score=0.96,
        renderer='collectible',
        reason='Coins and stars are recurring focal objects.',
    ),
    FrequentTextureSpec(
        name='shadows',
        patterns=('textures/segment2/shadow_quarter_*',),
        exposure_score=0.94,
        renderer='shadow',
        reason='Projected actor shadows appear throughout gameplay.',
    ),
    FrequentTextureSpec(
        name='common_effects',
        patterns=(
            'actors/smoke/*',
            'actors/burn_smoke/*',
            'actors/sparkle/*',
            'actors/sparkle_animation/*',
            'actors/water_splash/*',
        ),
        exposure_score=0.91,
        renderer='effect',
        reason='Movement, collection, damage, and water effects recur frequently.',
    ),
    FrequentTextureSpec(
        name='trees',
        patterns=('actors/tree/*',),
        exposure_score=0.87,
        renderer='tree',
        reason='Tree billboards occupy large screen areas in several courses.',
    ),
    FrequentTextureSpec(
        name='doors',
        patterns=('actors/door/*',),
        exposure_score=0.86,
        renderer='door',
        reason='Castle and course transitions repeatedly show door textures up close.',
    ),
    FrequentTextureSpec(
        name='boxes_and_switches',
        patterns=(
            'actors/breakable_box/*',
            'actors/exclamation_box/*',
            'actors/exclamation_box_outline/*',
            'actors/metal_box/*',
            'actors/blue_coin_switch/*',
            'actors/capswitch/*',
            'actors/purple_switch/*',
        ),
        exposure_score=0.83,
        renderer='box_switch',
        reason='Interactive blocks and switches are common gameplay landmarks.',
    ),
    FrequentTextureSpec(
        name='signposts',
        patterns=('actors/wooden_signpost/*',),
        exposure_score=0.81,
        renderer='signpost',
        reason='Signposts are frequently inspected from close range.',
    ),
    FrequentTextureSpec(
        name='common_enemies',
        patterns=('actors/goomba/*', 'actors/koopa_shell/*'),
        exposure_score=0.80,
        renderer='enemy',
        reason='Goombas and Koopa shells recur across many stages.',
    ),
)


def classify_frequent_texture(fname: str) -> FrequentTextureSpec | None:
    for spec in FREQUENT_TEXTURE_SPECS:
        if any(fnmatch.fnmatch(fname, pattern) for pattern in spec.patterns):
            return spec
    return None


def supports_frequent_texture(identity, info) -> bool:
    return classify_frequent_texture(identity.fname) is not None


def _work_canvas(shape, scale=4):
    h, w = int(shape[0]), int(shape[1])
    img = Image.new('RGBA', (w * scale, h * scale), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img, 'RGBA'), scale


def _downsample(img: Image.Image, shape):
    h, w = int(shape[0]), int(shape[1])
    return img.resize((w, h), Image.Resampling.LANCZOS)


def _rgba_to_requested(rgba: np.ndarray, shape):
    channels = shape[2] if len(shape) == 3 else 1
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


def _finish(img, shape):
    img = _downsample(img, shape)
    rgba = np.asarray(img, dtype=np.uint8)
    return _rgba_to_requested(rgba, shape)


def _star_points(cx, cy, outer, inner, points=5, rotation=-math.pi / 2):
    result = []
    for idx in range(points * 2):
        radius = outer if idx % 2 == 0 else inner
        angle = rotation + idx * math.pi / points
        result.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    return result


def _draw_mario(fname, shape, rng):
    low = fname.lower()
    if 'eyes_' in low:
        # The general PIL implementation has a semantic Mario eye renderer.
        return pil_textures.render_pil_texture(fname, shape, rng)

    img, draw, s = _work_canvas(shape)
    w, h = img.size
    cx, cy = w / 2, h / 2

    if 'logo' in low:
        radius = min(w, h) * 0.40
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                     fill=(248, 245, 225, 255), outline=(96, 30, 26, 255), width=max(1, 2 * s))
        red = (194, 34, 42, 255)
        stroke = max(2, 3 * s)
        left = cx - radius * 0.48
        right = cx + radius * 0.48
        top = cy - radius * 0.45
        bottom = cy + radius * 0.48
        draw.line((left, bottom, left, top), fill=red, width=stroke)
        draw.line((left, top, cx, cy + radius * 0.02), fill=red, width=stroke)
        draw.line((cx, cy + radius * 0.02, right, top), fill=red, width=stroke)
        draw.line((right, top, right, bottom), fill=red, width=stroke)
    elif 'mustache' in low:
        dark = (45, 24, 18, 255)
        mid = (91, 50, 32, 255)
        y = cy + h * 0.05
        lobes = [(-0.34, 0.16), (-0.18, 0.22), (0.0, 0.18), (0.18, 0.22), (0.34, 0.16)]
        for pos, size in lobes:
            rx = w * size
            ry = h * (0.19 if abs(pos) < 0.1 else 0.16)
            x = cx + w * pos
            draw.ellipse((x - rx, y - ry, x + rx, y + ry), fill=dark)
        draw.arc((w * 0.12, h * 0.17, w * 0.88, h * 0.84), 190, 350,
                 fill=mid, width=max(1, 2 * s))
        draw.polygon([(w * 0.07, y), (w * 0.22, y - h * 0.06), (w * 0.18, y + h * 0.14)], fill=dark)
        draw.polygon([(w * 0.93, y), (w * 0.78, y - h * 0.06), (w * 0.82, y + h * 0.14)], fill=dark)
    elif 'sideburn' in low:
        dark = (61, 32, 20, 255)
        mid = (113, 66, 38, 255)
        pts = [
            (w * 0.20, h * 0.05), (w * 0.78, h * 0.10), (w * 0.87, h * 0.45),
            (w * 0.64, h * 0.91), (w * 0.34, h * 0.80), (w * 0.12, h * 0.42),
        ]
        draw.polygon(pts, fill=dark)
        for idx in range(7):
            x = w * (0.23 + idx * 0.08)
            draw.line((x, h * 0.15, x - w * 0.07, h * 0.72), fill=mid, width=max(1, s))
    elif 'overalls_button' in low:
        r = min(w, h) * 0.33
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(221, 166, 50, 255),
                     outline=(93, 61, 17, 255), width=max(1, 2*s))
        draw.ellipse((cx-r*0.70, cy-r*0.70, cx+r*0.70, cy+r*0.70),
                     fill=(246, 205, 91, 255), outline=(174, 113, 31, 255), width=max(1, s))
        for dx, dy in [(-0.22, -0.22), (0.22, -0.22), (-0.22, 0.22), (0.22, 0.22)]:
            rr = max(1, int(r * 0.10))
            px = cx + dx * r
            py = cy + dy * r
            draw.ellipse((px-rr, py-rr, px+rr, py+rr), fill=(121, 76, 22, 255))
        draw.arc((cx-r*0.7, cy-r*0.75, cx+r*0.65, cy+r*0.55), 205, 305,
                 fill=(255, 238, 160, 230), width=max(1, 2*s))
    elif 'wing' in low:
        outline = (55, 69, 91, 255)
        shade = (176, 205, 230, 255)
        white = (245, 249, 250, 255)
        root_x = w * 0.12
        mid_y = h * 0.62
        draw.line((root_x, mid_y, w * 0.84, h * 0.12), fill=outline, width=max(1, 2*s))
        feather_count = 7
        for idx in range(feather_count):
            t = idx / max(1, feather_count - 1)
            x0 = root_x + w * (0.08 + t * 0.58)
            y0 = mid_y - h * t * 0.40
            length = w * (0.30 - t * 0.10)
            height = h * (0.24 - t * 0.06)
            draw.ellipse((x0, y0-height, x0+length, y0+height), fill=white, outline=outline, width=max(1, s))
            draw.arc((x0+s, y0-height+s, x0+length-s, y0+height-s), 200, 330,
                     fill=shade, width=max(1, s))
        if 'tip' in low:
            draw.polygon([(w*0.72, h*0.16), (w*0.96, h*0.03), (w*0.86, h*0.34)], fill=white, outline=outline)
    elif 'metal' in low:
        for x in range(w):
            t = x / max(1, w - 1)
            band = 0.5 + 0.32 * math.sin(t * math.pi * 5)
            c = int(85 + band * 145)
            draw.line((x, 0, x, h), fill=(c, min(255, c+8), min(255, c+14), 255))
        for y in range(0, h, max(2, 4*s)):
            draw.line((0, y, w, y), fill=(255, 255, 255, 45), width=max(1, s))
    else:
        return pil_textures.render_pil_texture(fname, shape, rng)
    return _finish(img, shape)


def _draw_collectible(fname, shape, rng):
    low = fname.lower()
    if '/coin/' in low:
        # Keep the existing dedicated IA coin renderer.
        return pil_textures.render_pil_texture(fname, shape, rng)
    img, draw, s = _work_canvas(shape)
    w, h = img.size
    cx, cy = w/2, h/2
    if 'star_eye' in low:
        eye_w = w * 0.13
        eye_h = h * 0.27
        for x in (cx - w*0.18, cx + w*0.18):
            draw.ellipse((x-eye_w, cy-eye_h, x+eye_w, cy+eye_h), fill=(28, 25, 34, 255))
            draw.ellipse((x-eye_w*0.36, cy-eye_h*0.62, x+eye_w*0.05, cy-eye_h*0.18), fill=(255, 255, 255, 235))
    else:
        # A warm faceted gold material that reads clearly when wrapped over the star model.
        draw.rectangle((0, 0, w, h), fill=(228, 165, 39, 255))
        facets = [
            ([(0, 0), (w/2, h/2), (w, 0)], (255, 222, 105, 255)),
            ([(0, 0), (w/2, h/2), (0, h)], (211, 133, 27, 255)),
            ([(w, 0), (w/2, h/2), (w, h)], (239, 180, 48, 255)),
            ([(0, h), (w/2, h/2), (w, h)], (190, 107, 20, 255)),
        ]
        for pts, color in facets:
            draw.polygon(pts, fill=color)
        draw.arc((w*0.08, h*0.08, w*0.75, h*0.75), 205, 305, fill=(255, 248, 194, 220), width=max(1, 2*s))
        for px, py in [(0.20, 0.25), (0.73, 0.32), (0.58, 0.78)]:
            r = max(1, 2*s)
            draw.line((w*px-r*2, h*py, w*px+r*2, h*py), fill=(255, 246, 176, 180), width=max(1, s))
            draw.line((w*px, h*py-r*2, w*px, h*py+r*2), fill=(255, 246, 176, 180), width=max(1, s))
    return _finish(img, shape)


def _draw_shadow(fname, shape, rng):
    h, w = int(shape[0]), int(shape[1])
    yy, xx = np.mgrid[0:h, 0:w]
    if 'circle' in fname:
        radius = min(w, h) - 0.5
        dist = np.sqrt(xx.astype(float) ** 2 + yy.astype(float) ** 2)
        alpha = np.clip((radius + 0.8 - dist) * 255.0, 0, 255).astype(np.uint8)
    else:
        alpha = np.full((h, w), 255, dtype=np.uint8)
        alpha[-1, :] = 220
        alpha[:, -1] = 220
    intensity = np.zeros((h, w), dtype=np.uint8)
    if len(shape) == 3 and shape[2] == 2:
        return np.stack([intensity, alpha], axis=2)
    return alpha


def _frame_index(fname):
    stem = fname.rsplit('/', 1)[-1].split('.', 1)[0]
    matches = re.findall(r'(\d+)', stem)
    return int(matches[-1]) if matches else 0


def _draw_effect(fname, shape, rng):
    low = fname.lower()
    idx = _frame_index(low)
    img, draw, s = _work_canvas(shape)
    w, h = img.size
    cx, cy = w/2, h/2
    if 'sparkle' in low:
        phase = idx % 6
        radius = min(w, h) * (0.16 + 0.045 * min(phase, 5-phase))
        alpha = int(245 - abs(phase - 2.5) * 24)
        for angle in (0, math.pi/4, math.pi/2, 3*math.pi/4):
            dx = math.cos(angle) * radius
            dy = math.sin(angle) * radius
            draw.line((cx-dx, cy-dy, cx+dx, cy+dy), fill=(255, 247, 165, alpha), width=max(1, 2*s))
        draw.ellipse((cx-3*s, cy-3*s, cx+3*s, cy+3*s), fill=(255, 255, 255, 255))
    elif 'water_splash' in low:
        progress = (idx % 8) / 7.0
        ring_rx = w * (0.12 + 0.32 * progress)
        ring_ry = h * (0.06 + 0.12 * progress)
        alpha = int(245 * (1.0 - 0.65 * progress))
        draw.arc((cx-ring_rx, cy-ring_ry, cx+ring_rx, cy+ring_ry), 180, 360,
                 fill=(196, 235, 255, alpha), width=max(1, 2*s))
        droplets = 4 + idx
        for k in range(droplets):
            t = k / max(1, droplets-1)
            angle = math.pi * (0.12 + 0.76*t)
            distance = w * (0.10 + 0.30*progress)
            x = cx + math.cos(angle) * distance
            y = cy - math.sin(angle) * distance * (0.8 + progress)
            r = max(1, int((2.4 - 1.2*progress) * s))
            draw.ellipse((x-r, y-r*1.6, x+r, y+r*1.6), fill=(215, 244, 255, alpha))
    else:
        burn = 'burn_smoke' in low
        puff_count = 7 if burn else 6
        base = (72, 66, 64) if burn else (185, 190, 196)
        for k in range(puff_count):
            angle = 2 * math.pi * k / puff_count + rng.uniform(-0.18, 0.18)
            distance = min(w, h) * rng.uniform(0.05, 0.20)
            x = cx + math.cos(angle)*distance
            y = cy + math.sin(angle)*distance
            rx = min(w, h) * rng.uniform(0.16, 0.27)
            ry = rx * rng.uniform(0.75, 1.10)
            shade = int(rng.randint(-24, 25))
            color = tuple(max(0, min(255, c+shade)) for c in base) + (150 if burn else 125,)
            draw.ellipse((x-rx, y-ry, x+rx, y+ry), fill=color)
        draw.ellipse((cx-w*0.12, cy-h*0.12, cx+w*0.12, cy+h*0.12), fill=base+(155,))
    return _finish(img, shape)


def _draw_tree(fname, shape, rng):
    low = fname.lower()
    img, draw, s = _work_canvas(shape)
    w, h = img.size
    trunk = (105, 68, 38, 255)
    trunk_dark = (61, 39, 24, 255)
    if 'palm' in low:
        tw = max(3*s, int(w*0.10))
        draw.polygon([(w*0.46, h*0.96), (w*0.54, h*0.96), (w*0.57, h*0.26), (w*0.48, h*0.24)], fill=trunk, outline=trunk_dark)
        for k in range(9):
            angle = 2*math.pi*k/9
            length = w*(0.34 if k % 2 else 0.42)
            x2 = w*0.52 + math.cos(angle)*length
            y2 = h*0.25 + math.sin(angle)*length*0.45
            width = max(2*s, int(w*0.05))
            draw.line((w*0.52, h*0.25, x2, y2), fill=(48, 116, 58, 255), width=width)
            draw.ellipse((x2-width, y2-width*0.45, x2+width, y2+width*0.45), fill=(74, 151, 73, 255))
    elif 'pine' in low:
        snow = 'snowy' in low
        draw.rectangle((w*0.46, h*0.55, w*0.54, h*0.98), fill=trunk, outline=trunk_dark)
        for k, spread in enumerate((0.40, 0.34, 0.27, 0.20)):
            top = h*(0.05 + k*0.15)
            bottom = h*(0.40 + k*0.14)
            pts = [(w*0.50, top), (w*(0.50-spread), bottom), (w*(0.50+spread), bottom)]
            draw.polygon(pts, fill=(46, 112+8*k, 58, 255), outline=(28, 73, 39, 255))
            if snow:
                draw.line((w*(0.50-spread*0.82), bottom-h*0.04, w*(0.50+spread*0.82), bottom-h*0.04),
                          fill=(236, 245, 252, 235), width=max(2*s, int(h*0.04)))
    else:
        draw.rectangle((w*0.45, h*0.52, w*0.55, h*0.98), fill=trunk, outline=trunk_dark)
        centers = [
            (0.28, 0.42, 0.25), (0.48, 0.28, 0.31), (0.70, 0.42, 0.26),
            (0.38, 0.52, 0.25), (0.60, 0.53, 0.26),
        ]
        if 'left_side' in low:
            centers = [(x*0.88, y, r) for x, y, r in centers]
        elif 'right_side' in low:
            centers = [(0.12+x*0.88, y, r) for x, y, r in centers]
        for x, y, r in centers:
            color = (50+int(40*y), 126+int(55*(1-y)), 60, 245)
            draw.ellipse((w*(x-r), h*(y-r), w*(x+r), h*(y+r)), fill=color, outline=(31, 83, 41, 255))
        for _ in range(16):
            x = rng.uniform(w*0.18, w*0.82)
            y = rng.uniform(h*0.15, h*0.62)
            rr = max(1, 2*s)
            draw.ellipse((x-rr, y-rr, x+rr, y+rr), fill=(139, 185, 78, 160))
    return _finish(img, shape)


def _door_palette(low):
    if 'metal' in low:
        return 'metal', (97, 116, 130, 255), (180, 199, 209, 255), (49, 59, 67, 255)
    if 'bbh' in low:
        return 'haunted', (83, 54, 83, 255), (137, 91, 119, 255), (43, 28, 49, 255)
    if 'mural' in low:
        return 'mural', (99, 74, 111, 255), (195, 159, 177, 255), (49, 36, 60, 255)
    if 'rough' in low:
        return 'rough', (111, 68, 35, 255), (166, 108, 58, 255), (57, 32, 18, 255)
    return 'polished', (111, 67, 31, 255), (197, 135, 70, 255), (61, 34, 17, 255)


def _draw_door(fname, shape, rng):
    low = fname.lower()
    img, draw, s = _work_canvas(shape)
    w, h = img.size
    kind, base, light, dark = _door_palette(low)
    if 'overlay' in low:
        if kind == 'metal':
            draw.rectangle((w*0.12, h*0.12, w*0.88, h*0.88), outline=light, width=max(2*s, int(w*0.05)))
            for x, y in [(0.20,0.20),(0.80,0.20),(0.20,0.80),(0.80,0.80)]:
                r = min(w,h)*0.055
                draw.ellipse((w*x-r,h*y-r,w*x+r,h*y+r), fill=dark, outline=light)
        elif kind == 'mural':
            draw.ellipse((w*0.18, h*0.14, w*0.82, h*0.86), outline=(230, 201, 118, 230), width=max(2*s, int(w*0.05)))
            draw.polygon(_star_points(w*0.50, h*0.50, min(w,h)*0.24, min(w,h)*0.10), fill=(213, 172, 74, 210), outline=dark)
        else:
            draw.rectangle((w*0.10, h*0.08, w*0.90, h*0.92), outline=light, width=max(2*s, int(w*0.06)))
            draw.rectangle((w*0.22, h*0.18, w*0.78, h*0.45), outline=dark, width=max(1, 2*s))
            draw.rectangle((w*0.22, h*0.55, w*0.78, h*0.83), outline=dark, width=max(1, 2*s))
        return _finish(img, shape)
    if 'door_lock' in low:
        draw.rounded_rectangle((w*0.18,h*0.32,w*0.82,h*0.88), radius=max(1,4*s), fill=(184,143,52,255), outline=(78,53,15,255), width=max(1,2*s))
        draw.arc((w*0.27,h*0.06,w*0.73,h*0.56),180,360,fill=(184,143,52,255),width=max(2*s,int(w*0.12)))
        draw.ellipse((w*0.45,h*0.52,w*0.55,h*0.64),fill=(65,42,13,255))
        draw.rectangle((w*0.48,h*0.58,w*0.52,h*0.75),fill=(65,42,13,255))
        return _finish(img, shape)
    if '_star_door_sign' in low:
        count = 0 if 'zero_' in low else 1 if 'one_' in low else 3
        draw.ellipse((w*0.08,h*0.08,w*0.92,h*0.92),fill=(174,132,66,255),outline=(70,45,18,255),width=max(1,2*s))
        if count == 0:
            draw.ellipse((w*0.34,h*0.34,w*0.66,h*0.66),outline=(242,214,113,255),width=max(1,2*s))
        else:
            spacing = w*0.24
            start = cx = w/2 - spacing*(count-1)/2
            for k in range(count):
                x = start + spacing*k
                draw.polygon(_star_points(x,h/2,min(w,h)*0.15,min(w,h)*0.065),fill=(245,199,70,255),outline=(96,62,16,255))
        return _finish(img, shape)
    # Opaque door surface.
    draw.rectangle((0,0,w,h),fill=base)
    if kind == 'metal':
        for x in range(w):
            t=x/max(1,w-1)
            c=int(95+90*(0.5+0.5*math.sin(t*math.pi*3)))
            draw.line((x,0,x,h),fill=(c,c+8,min(255,c+14),255))
        margin=min(w,h)*0.08
        draw.rectangle((margin,margin,w-margin,h-margin),outline=dark,width=max(1,2*s))
        for x,y in [(0.16,0.10),(0.84,0.10),(0.16,0.90),(0.84,0.90)]:
            r=min(w,h)*0.035
            draw.ellipse((w*x-r,h*y-r,w*x+r,h*y+r),fill=dark,outline=light)
    else:
        for x in range(0,w,max(3*s,int(w*0.13))):
            draw.line((x,0,x,h),fill=dark,width=max(1,s))
            draw.line((x+2*s,0,x+2*s,h),fill=light,width=max(1,s))
        margin=min(w,h)*0.10
        draw.rectangle((margin,margin,w-margin,h-margin),outline=dark,width=max(1,2*s))
        draw.rectangle((margin*1.5,margin*1.5,w-margin*1.5,h*0.46),outline=light,width=max(1,s))
        draw.rectangle((margin*1.5,h*0.54,w-margin*1.5,h-margin*1.5),outline=light,width=max(1,s))
        for y in np.linspace(h*0.18,h*0.85,5):
            draw.arc((w*0.12,y-h*0.08,w*0.90,y+h*0.08),190,350,fill=(226,167,89,90),width=max(1,s))
    knob_r=min(w,h)*0.045
    draw.ellipse((w*0.75-knob_r,h*0.53-knob_r,w*0.75+knob_r,h*0.53+knob_r),fill=(215,171,66,255),outline=(76,49,14,255))
    return _finish(img, shape)


def _box_colors(low):
    if 'metal_cap' in low or 'metal_box' in low:
        return (92,107,121,255),(182,198,210,255),(47,56,64,255)
    if 'vanish_cap' in low:
        return (57,92,177,255),(112,160,232,255),(29,49,103,255)
    if 'wing_cap' in low:
        return (179,43,48,255),(238,93,83,255),(92,20,25,255)
    return (183,142,42,255),(238,195,73,255),(99,67,18,255)


def _draw_box_switch(fname, shape, rng):
    low = fname.lower()
    img, draw, s = _work_canvas(shape)
    w,h=img.size
    base,light,dark=_box_colors(low)
    if 'outline' in low:
        if 'exclamation_point' in low:
            draw.rectangle((w*0.42,h*0.12,w*0.58,h*0.66),fill=(245,220,90,255),outline=dark)
            draw.ellipse((w*0.41,h*0.76,w*0.59,h*0.94),fill=(245,220,90,255),outline=dark)
        else:
            draw.rectangle((w*0.08,h*0.08,w*0.92,h*0.92),outline=(246,228,116,230),width=max(2*s,int(w*0.07)))
        return _finish(img, shape)
    if 'switch' in low:
        if 'purple' in low:
            base,light,dark=(100,57,142,255),(172,113,205,255),(55,28,83,255)
        elif 'blue_coin' in low:
            base,light,dark=(42,92,180,255),(91,159,235,255),(22,50,105,255)
        draw.rectangle((0,0,w,h),fill=base)
        draw.rounded_rectangle((w*0.08,h*0.12,w*0.92,h*0.88),radius=max(1,4*s),fill=light,outline=dark,width=max(1,2*s))
        draw.polygon([(w*0.50,h*0.20),(w*0.70,h*0.52),(w*0.57,h*0.52),(w*0.57,h*0.78),(w*0.43,h*0.78),(w*0.43,h*0.52),(w*0.30,h*0.52)],fill=(245,227,104,255),outline=dark)
        return _finish(img, shape)
    if 'breakable_box' in low:
        draw.rectangle((0,0,w,h),fill=(160,104,54,255))
        for x in range(0,w,max(3*s,int(w*0.16))):
            draw.line((x,0,x,h),fill=(108,61,30,255),width=max(1,s))
        brace=(213,151,76,255)
        draw.line((0,0,w,h),fill=brace,width=max(2*s,int(w*0.10)))
        draw.line((w,0,0,h),fill=brace,width=max(2*s,int(w*0.10)))
        draw.rectangle((1*s,1*s,w-1*s,h-1*s),outline=(65,36,18,255),width=max(1,2*s))
        return _finish(img, shape)
    draw.rectangle((0,0,w,h),fill=base)
    margin=min(w,h)*0.06
    draw.rectangle((margin,margin,w-margin,h-margin),outline=dark,width=max(1,2*s))
    for x in range(int(margin),int(w-margin),max(4*s,int(w*0.18))):
        draw.line((x,margin,x,h-margin),fill=light,width=max(1,s))
    if 'front' in low:
        draw.rectangle((w*0.42,h*0.18,w*0.58,h*0.63),fill=(249,234,130,255),outline=dark)
        draw.ellipse((w*0.41,h*0.73,w*0.59,h*0.91),fill=(249,234,130,255),outline=dark)
    return _finish(img, shape)


def _draw_signpost(fname, shape, rng):
    low=fname.lower()
    img,draw,s=_work_canvas(shape)
    w,h=img.size
    draw.rectangle((0,0,w,h),fill=(143,91,45,255))
    for y in range(0,h,max(3*s,int(h*0.16))):
        draw.arc((w*0.05,y-h*0.06,w*0.95,y+h*0.08),190,350,fill=(205,143,73,180),width=max(1,s))
    draw.rectangle((s,s,w-s,h-s),outline=(70,39,19,255),width=max(1,2*s))
    if 'front' in low:
        for k,width in enumerate((0.62,0.76,0.52)):
            y=h*(0.28+k*0.20)
            draw.line((w*0.16,y,w*(0.16+width),y),fill=(65,38,21,255),width=max(1,2*s))
        draw.polygon([(w*0.70,h*0.70),(w*0.90,h*0.80),(w*0.70,h*0.90)],fill=(235,199,105,255),outline=(65,38,21,255))
    else:
        draw.line((w*0.18,h*0.20,w*0.82,h*0.80),fill=(86,48,22,255),width=max(2*s,int(w*0.08)))
        draw.line((w*0.82,h*0.20,w*0.18,h*0.80),fill=(86,48,22,255),width=max(2*s,int(w*0.08)))
    return _finish(img, shape)


def _draw_enemy(fname, shape, rng):
    low=fname.lower()
    img,draw,s=_work_canvas(shape)
    w,h=img.size
    if 'goomba_body' in low:
        # Warm mushroom leather with a pale lower rim and subtle pores.
        for y in range(h):
            t=y/max(1,h-1)
            color=(int(164-55*t),int(105-42*t),int(54-22*t),255)
            draw.line((0,y,w,y),fill=color)
        draw.arc((w*0.08,h*0.05,w*0.92,h*0.90),205,335,fill=(230,165,91,180),width=max(1,2*s))
        draw.rectangle((0,h*0.78,w,h),fill=(205,157,105,255))
        for _ in range(18):
            x=rng.uniform(0,w); y=rng.uniform(0,h*0.76); r=max(1,rng.uniform(1,2.2)*s)
            draw.ellipse((x-r,y-r,x+r,y+r),fill=(91,52,27,80))
    elif 'goomba_face' in low:
        blink='blink' in low
        brow=(48,26,15,255)
        eye=(245,237,215,255)
        for x in (w*0.30,w*0.70):
            if blink:
                draw.line((x-w*0.12,h*0.40,x+w*0.12,h*0.40),fill=brow,width=max(2*s,int(h*0.08)))
            else:
                draw.ellipse((x-w*0.11,h*0.22,x+w*0.11,h*0.58),fill=eye,outline=brow,width=max(1,s))
                draw.ellipse((x-w*0.035,h*0.34,x+w*0.035,h*0.51),fill=(21,16,13,255))
            direction=1 if x<w/2 else -1
            draw.line((x-direction*w*0.14,h*0.18,x+direction*w*0.08,h*0.27),fill=brow,width=max(1,2*s))
        draw.arc((w*0.27,h*0.50,w*0.73,h*0.84),15,165,fill=brow,width=max(1,2*s))
        draw.polygon([(w*0.34,h*0.62),(w*0.42,h*0.62),(w*0.38,h*0.76)],fill=(250,244,225,255),outline=brow)
        draw.polygon([(w*0.58,h*0.62),(w*0.66,h*0.62),(w*0.62,h*0.76)],fill=(250,244,225,255),outline=brow)
    elif 'koopa_shell' in low:
        draw.rectangle((0,0,w,h),fill=(31,101,45,255))
        cx,cy=w/2,h/2
        outer=min(w,h)*0.44
        draw.ellipse((cx-outer,cy-outer,cx+outer,cy+outer),fill=(68,153,69,255),outline=(25,69,29,255),width=max(1,2*s))
        inner=outer*0.73
        points=[]
        for k in range(6):
            ang=-math.pi/2+k*math.pi/3
            points.append((cx+math.cos(ang)*inner,cy+math.sin(ang)*inner))
        draw.polygon(points,fill=(144,192,78,255),outline=(36,92,35,255))
        for x,y in points:
            draw.line((cx,cy,x,y),fill=(47,113,43,255),width=max(1,s))
        if 'back' in low:
            draw.ellipse((cx-inner*0.28,cy-inner*0.28,cx+inner*0.28,cy+inner*0.28),fill=(225,213,148,255),outline=(36,92,35,255))
    else:
        return pil_textures.render_pil_texture(fname, shape, rng)
    return _finish(img, shape)


_RENDERERS: dict[str, Callable] = {
    'mario': _draw_mario,
    'collectible': _draw_collectible,
    'shadow': _draw_shadow,
    'effect': _draw_effect,
    'tree': _draw_tree,
    'door': _draw_door,
    'box_switch': _draw_box_switch,
    'signpost': _draw_signpost,
    'enemy': _draw_enemy,
}


def render_frequent_texture(fname, shape, rng, identity=None):
    spec = classify_frequent_texture(fname)
    if spec is None:
        return pil_textures.render_pil_texture(fname, shape, rng, identity)
    return _RENDERERS[spec.renderer](fname, shape, rng)


__all__ = [
    'FREQUENT_TEXTURE_SPECS',
    'FrequentTextureSpec',
    'classify_frequent_texture',
    'render_frequent_texture',
    'supports_frequent_texture',
]
