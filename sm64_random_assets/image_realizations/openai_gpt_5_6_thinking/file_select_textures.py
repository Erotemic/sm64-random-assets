from __future__ import annotations

import hashlib
import math

import numpy as np
from PIL import Image, ImageDraw


FILE_SELECT_TEXTURE_SPECS = {
    # Background material tiles used by the file-select menu family.
    'levels/menu/main_menu_seg7.00018.rgba16.png': 'backdrop_deep',
    'levels/menu/main_menu_seg7.00818.rgba16.png': 'backdrop_light',

    # The screenshot and contiguous asset layout identify these as the two
    # rectangular save-file plate states.
    'levels/menu/main_menu_seg7.01018.rgba16.png': 'save_slot_occupied',
    'levels/menu/main_menu_seg7.02018.rgba16.png': 'save_slot_empty',

    # Contiguous square action-button material group. Keep the labels in the
    # existing human-authored glyph renderer; these provide differentiated
    # button surfaces and unobtrusive semantic iconography.
    'levels/menu/main_menu_seg7.03468.rgba16.png': 'action_score',
    'levels/menu/main_menu_seg7.03C68.rgba16.png': 'action_copy',
    'levels/menu/main_menu_seg7.04468.rgba16.png': 'action_erase',
    'levels/menu/main_menu_seg7.04C68.rgba16.png': 'action_sound',
    'levels/menu/main_menu_seg7.05468.rgba16.png': 'action_auxiliary',

    # Additional wide menu-background tiles from the same segment. Render them
    # in the same palette so transitions and secondary file screens no longer
    # fall back to the gray generic material.
    'levels/menu/main_menu_seg7.0D1A8.rgba16.png': 'backdrop_upper',
    'levels/menu/main_menu_seg7.0E1A8.rgba16.png': 'backdrop_lower',
}


def supports_file_select_texture(identity, info):
    return str(identity.fname) in FILE_SELECT_TEXTURE_SPECS


def _stable_rng(fname):
    seed = int(hashlib.sha256(str(fname).encode('utf8')).hexdigest()[:16], 16)
    return np.random.RandomState(seed & 0x7FFFFFFF)


def _mix(a, b, t):
    return tuple(int(round((1 - t) * x + t * y)) for x, y in zip(a, b))


def _finish(img, shape):
    h, w = int(shape[0]), int(shape[1])
    img = img.resize((w, h), Image.Resampling.LANCZOS)
    rgba = np.asarray(img, dtype=np.uint8).copy()
    # These menu materials are opaque surfaces. Drawing with RGBA lets us use
    # translucent highlights, but the stored texture alpha itself must remain
    # fully opaque or the menu geometry becomes see-through.
    rgba[..., 3] = 255
    if len(shape) == 3 and shape[2] == 4:
        return rgba
    if len(shape) == 3 and shape[2] == 3:
        return rgba[..., :3]
    intensity = np.clip(
        rgba[..., 0].astype(np.float32) * 0.299
        + rgba[..., 1].astype(np.float32) * 0.587
        + rgba[..., 2].astype(np.float32) * 0.114,
        0,
        255,
    ).astype(np.uint8)
    if len(shape) == 3 and shape[2] == 2:
        return np.stack([intensity, rgba[..., 3]], axis=2)
    return intensity


def _gradient_image(W, H, top, bottom):
    arr = np.empty((H, W, 4), dtype=np.uint8)
    for y in range(H):
        t = y / max(H - 1, 1)
        color = _mix(top, bottom, t)
        arr[y, :, :3] = color
        arr[y, :, 3] = 255
    return Image.fromarray(arr, mode='RGBA')


def _add_fine_texture(img, rng, strength=8, star_count=0):
    arr = np.asarray(img, dtype=np.int16).copy()
    H, W = arr.shape[:2]
    noise = rng.normal(0, strength, size=(H, W, 1))
    # Low-frequency vertical illumination variation plus restrained dither.
    x = np.linspace(-1, 1, W, dtype=np.float32)[None, :, None]
    y = np.linspace(-1, 1, H, dtype=np.float32)[:, None, None]
    glow = 8 * np.exp(-(x * x * 1.2 + y * y * 0.7))
    arr[..., :3] = np.clip(arr[..., :3] + noise + glow, 0, 255)
    img = Image.fromarray(arr.astype(np.uint8), mode='RGBA')
    if star_count:
        draw = ImageDraw.Draw(img, 'RGBA')
        for _ in range(star_count):
            px = int(rng.randint(2, max(3, W - 2)))
            py = int(rng.randint(2, max(3, H - 2)))
            radius = 1 if rng.rand() < 0.82 else 2
            alpha = int(rng.randint(38, 105))
            draw.ellipse((px - radius, py - radius, px + radius, py + radius),
                         fill=(238, 232, 181, alpha))
    return img


def _draw_bevel(draw, box, radius, outer, inner, highlight, shadow, scale):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=radius, fill=outer)
    inset = max(2, scale * 2)
    inner_box = (x1 + inset, y1 + inset, x2 - inset, y2 - inset)
    draw.rounded_rectangle(inner_box, radius=max(1, radius - inset), fill=inner)
    draw.line((x1 + radius, y1 + 1, x2 - radius, y1 + 1), fill=highlight, width=max(1, scale))
    draw.line((x1 + 1, y1 + radius, x1 + 1, y2 - radius), fill=highlight, width=max(1, scale))
    draw.line((x1 + radius, y2 - 1, x2 - radius, y2 - 1), fill=shadow, width=max(1, scale))
    draw.line((x2 - 1, y1 + radius, x2 - 1, y2 - radius), fill=shadow, width=max(1, scale))
    return inner_box


def _render_backdrop(kind, W, H, rng, scale):
    if kind in {'backdrop_deep', 'backdrop_upper'}:
        top = (24, 29, 67)
        bottom = (57, 70, 123)
    else:
        top = (57, 66, 121)
        bottom = (86, 103, 156)
    if kind == 'backdrop_lower':
        top, bottom = (66, 78, 137), (29, 35, 77)
    img = _gradient_image(W, H, top, bottom)
    img = _add_fine_texture(img, rng, strength=3.5, star_count=max(4, (W * H) // 12000))
    draw = ImageDraw.Draw(img, 'RGBA')

    # Broad soft bands read as polished castle-menu material without the
    # repetitive scanlines and random dark holes visible in the old fallback.
    draw.rectangle((0, 0, W, max(2, H * 0.07)), fill=(235, 226, 255, 34))
    draw.rectangle((0, H * 0.80, W, H), fill=(9, 14, 39, 46))
    for frac, alpha in [(0.24, 18), (0.55, 12)]:
        y = int(H * frac)
        draw.line((0, y, W, y), fill=(218, 226, 255, alpha), width=max(1, scale))

    # Subtle corner filigree. It remains abstract when tiled or stretched.
    corner = max(5 * scale, min(W, H) // 5)
    gold = (226, 181, 72, 46)
    draw.arc((scale, scale, corner * 2, corner * 2), 180, 270, fill=gold, width=max(1, scale))
    draw.arc((W - corner * 2, H - corner * 2, W - scale, H - scale), 0, 90,
             fill=gold, width=max(1, scale))
    return img


def _render_save_slot(kind, W, H, rng, scale):
    occupied = kind == 'save_slot_occupied'
    if occupied:
        base_top, base_bottom = (38, 67, 122), (18, 35, 77)
        trim = (232, 181, 56, 255)
        trim_shadow = (104, 69, 19, 255)
        inset_top, inset_bottom = (63, 96, 151), (31, 54, 104)
    else:
        base_top, base_bottom = (113, 148, 183), (55, 88, 128)
        trim = (210, 225, 239, 255)
        trim_shadow = (45, 62, 91, 255)
        inset_top, inset_bottom = (126, 165, 196), (67, 106, 145)

    img = _gradient_image(W, H, base_top, base_bottom)
    img = _add_fine_texture(img, rng, strength=2.8)
    draw = ImageDraw.Draw(img, 'RGBA')
    margin = max(2 * scale, min(W, H) // 15)
    box = (margin, margin, W - margin - 1, H - margin - 1)
    inner = _draw_bevel(
        draw,
        box,
        radius=max(3 * scale, min(W, H) // 8),
        outer=trim_shadow,
        inner=(inset_top[0], inset_top[1], inset_top[2], 255),
        highlight=(255, 249, 211, 180) if occupied else (244, 251, 255, 180),
        shadow=(4, 10, 30, 210),
        scale=scale,
    )
    x1, y1, x2, y2 = inner
    # Vertical gradient inside the plaque.
    for y in range(int(y1), int(y2) + 1):
        t = (y - y1) / max(y2 - y1, 1)
        color = _mix(inset_top, inset_bottom, t) + (255,)
        draw.line((x1 + scale, y, x2 - scale, y), fill=color, width=1)

    # Corner fasteners and restrained horizontal separators.
    fastener = (249, 208, 83, 230) if occupied else (217, 235, 246, 210)
    r = max(scale, min(W, H) // 24)
    for px, py in [(x1 + 3 * r, y1 + 3 * r), (x2 - 3 * r, y1 + 3 * r),
                   (x1 + 3 * r, y2 - 3 * r), (x2 - 3 * r, y2 - 3 * r)]:
        draw.ellipse((px - r, py - r, px + r, py + r), fill=fastener,
                     outline=(18, 26, 54, 190), width=max(1, scale))
    for frac in (0.40, 0.68):
        y = int(y1 + (y2 - y1) * frac)
        draw.line((x1 + 5 * r, y, x2 - 5 * r, y),
                  fill=(226, 236, 255, 34), width=max(1, scale))

    if occupied:
        # Gold star medallion at the left. The game text remains separate.
        cx = int(x1 + (x2 - x1) * 0.18)
        cy = int((y1 + y2) / 2)
        outer = max(4 * scale, int((y2 - y1) * 0.18))
        points = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rr = outer if i % 2 == 0 else outer * 0.43
            points.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
        draw.polygon(points, fill=(250, 204, 52, 238), outline=(94, 55, 8, 255))
        draw.ellipse((cx - outer * 0.18, cy - outer * 0.28,
                      cx + outer * 0.05, cy - outer * 0.05), fill=(255, 252, 205, 210))
    else:
        # Empty slot gets a quiet dotted registration motif rather than random holes.
        dot = max(scale, int((y2 - y1) * 0.035))
        for row in range(2):
            for col in range(3):
                px = int(x1 + (x2 - x1) * (0.30 + col * 0.20))
                py = int(y1 + (y2 - y1) * (0.40 + row * 0.22))
                draw.ellipse((px - dot, py - dot, px + dot, py + dot),
                             fill=(215, 234, 246, 92))
    return img


def _draw_star(draw, cx, cy, outer, fill, outline, width):
    pts = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        radius = outer if i % 2 == 0 else outer * 0.43
        pts.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    draw.polygon(pts, fill=fill, outline=outline)


def _render_action(kind, W, H, rng, scale):
    palette = {
        'action_score': ((30, 81, 145), (15, 43, 93), (241, 192, 60)),
        'action_copy': ((34, 126, 126), (14, 69, 82), (146, 237, 215)),
        'action_erase': ((151, 50, 64), (83, 20, 39), (255, 170, 151)),
        'action_sound': ((93, 62, 154), (43, 27, 94), (223, 188, 255)),
        'action_auxiliary': ((161, 111, 39), (83, 52, 17), (255, 222, 131)),
    }
    top, bottom, accent = palette[kind]
    img = _gradient_image(W, H, _mix(top, (255, 255, 255), 0.12), bottom)
    img = _add_fine_texture(img, rng, strength=2.2)
    draw = ImageDraw.Draw(img, 'RGBA')
    margin = max(2 * scale, min(W, H) // 14)
    box = (margin, margin, W - margin - 1, H - margin - 1)
    inner = _draw_bevel(
        draw,
        box,
        radius=max(3 * scale, min(W, H) // 7),
        outer=(10, 17, 39, 255),
        inner=top + (255,),
        highlight=_mix(accent, (255, 255, 255), 0.40) + (210,),
        shadow=(5, 8, 24, 235),
        scale=scale,
    )
    x1, y1, x2, y2 = inner
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    size = min(x2 - x1, y2 - y1) * 0.27
    icon_fill = accent + (198,)
    icon_outline = _mix(bottom, (0, 0, 0), 0.35) + (245,)

    if kind == 'action_score':
        _draw_star(draw, cx, cy, size, icon_fill, icon_outline, max(1, scale))
        draw.arc((cx - size * 1.35, cy - size * 1.35,
                  cx + size * 1.35, cy + size * 1.35), 18, 162,
                 fill=(255, 246, 193, 145), width=max(1, scale))
    elif kind == 'action_copy':
        off = max(2 * scale, int(size * 0.38))
        draw.rounded_rectangle((cx - size * 0.70 - off, cy - size * 0.65,
                                cx + size * 0.55 - off, cy + size * 0.68),
                               radius=max(2, 2 * scale), fill=(188, 240, 225, 126),
                               outline=icon_outline, width=max(1, scale))
        draw.rounded_rectangle((cx - size * 0.55 + off, cy - size * 0.70,
                                cx + size * 0.70 + off, cy + size * 0.63),
                               radius=max(2, 2 * scale), fill=icon_fill,
                               outline=icon_outline, width=max(1, scale))
    elif kind == 'action_erase':
        width = max(3 * scale, int(size * 0.34))
        draw.line((cx - size * 0.72, cy - size * 0.72,
                   cx + size * 0.72, cy + size * 0.72), fill=icon_outline, width=width + scale)
        draw.line((cx + size * 0.72, cy - size * 0.72,
                   cx - size * 0.72, cy + size * 0.72), fill=icon_outline, width=width + scale)
        draw.line((cx - size * 0.72, cy - size * 0.72,
                   cx + size * 0.72, cy + size * 0.72), fill=icon_fill, width=width)
        draw.line((cx + size * 0.72, cy - size * 0.72,
                   cx - size * 0.72, cy + size * 0.72), fill=icon_fill, width=width)
    elif kind == 'action_sound':
        draw.polygon([(cx - size * 0.75, cy - size * 0.28),
                      (cx - size * 0.35, cy - size * 0.28),
                      (cx + size * 0.04, cy - size * 0.65),
                      (cx + size * 0.04, cy + size * 0.65),
                      (cx - size * 0.35, cy + size * 0.28),
                      (cx - size * 0.75, cy + size * 0.28)],
                     fill=icon_fill, outline=icon_outline)
        for mul in (0.48, 0.82):
            draw.arc((cx - size * 0.20, cy - size * mul,
                      cx + size * 1.20, cy + size * mul), -52, 52,
                     fill=icon_fill, width=max(2 * scale, 1))
    else:
        draw.rounded_rectangle((cx - size * 0.72, cy - size * 0.72,
                                cx + size * 0.72, cy + size * 0.72),
                               radius=max(2, int(size * 0.25)), fill=icon_fill,
                               outline=icon_outline, width=max(1, scale))
        draw.line((cx - size * 0.42, cy, cx + size * 0.42, cy),
                  fill=(255, 249, 211, 220), width=max(2, scale))

    # A faint lower shine keeps every button readable under the white labels.
    draw.arc((x1 + scale, y1 + scale, x2 - scale, y2 - scale), 195, 345,
             fill=(255, 255, 255, 38), width=max(1, scale))
    return img


def render_file_select_texture(fname, shape, rng=None, identity=None):
    kind = FILE_SELECT_TEXTURE_SPECS.get(str(fname), None)
    if kind is None:
        return None
    h, w = int(shape[0]), int(shape[1])
    scale = 8
    W, H = w * scale, h * scale
    local_rng = _stable_rng(fname)
    if kind.startswith('backdrop_'):
        img = _render_backdrop(kind, W, H, local_rng, scale)
    elif kind.startswith('save_slot_'):
        img = _render_save_slot(kind, W, H, local_rng, scale)
    else:
        img = _render_action(kind, W, H, local_rng, scale)
    return _finish(img, shape)


__all__ = [
    'FILE_SELECT_TEXTURE_SPECS',
    'render_file_select_texture',
    'supports_file_select_texture',
]
