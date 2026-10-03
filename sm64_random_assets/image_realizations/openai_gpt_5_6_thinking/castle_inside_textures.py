from __future__ import annotations

import hashlib
import math

import numpy as np
from PIL import Image, ImageDraw


CASTLE_INSIDE_TEXTURE_SPECS = {
    'levels/castle_inside/1.rgba16.png': 'wall_blocks',
    'levels/castle_inside/2.ia16.png': 'iron_railing_mask',
    'levels/castle_inside/3.rgba16.png': 'checker_marble_floor',
    'levels/castle_inside/4.rgba16.png': 'red_carpet_runner',
    'levels/castle_inside/7.rgba16.png': 'carpet_border',
    'levels/castle_inside/8.rgba16.png': 'parquet_floor',
    'levels/castle_inside/9.rgba16.png': 'wall_plaster_panel',
    'levels/castle_inside/10.rgba16.png': 'stone_column',
    'levels/castle_inside/11.rgba16.png': 'ceiling_panel',
    'levels/castle_inside/12.rgba16.png': 'wood_wainscot',
    'levels/castle_inside/13.rgba16.png': 'blue_diamond_wallpaper',
    'levels/castle_inside/14.rgba16.png': 'star_medallion_tile',
    'levels/castle_inside/15.rgba16.png': 'bronze_door_plate',
    'levels/castle_inside/16.ia16.png': 'window_glow_mask',
    'levels/castle_inside/castle_light.ia16.png': 'castle_light_glow',
}


def supports_castle_inside_texture(identity, info):
    return str(identity.fname) in CASTLE_INSIDE_TEXTURE_SPECS


def _stable_rng(fname):
    seed = int(hashlib.sha256(str(fname).encode('utf8')).hexdigest()[:16], 16)
    return np.random.RandomState(seed & 0x7FFFFFFF)


def _mix(a, b, t):
    return tuple(int(round((1 - t) * x + t * y)) for x, y in zip(a, b))


def _finish(img, shape):
    h, w = int(shape[0]), int(shape[1])
    img = img.resize((w, h), Image.Resampling.LANCZOS)
    rgba = np.asarray(img, dtype=np.uint8).copy()
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
    alpha = rgba[..., 3]
    if len(shape) == 3 and shape[2] == 2:
        return np.stack([intensity, alpha], axis=2)
    return intensity


def _base_rgba(W, H, color):
    arr = np.empty((H, W, 4), dtype=np.uint8)
    arr[..., :3] = color
    arr[..., 3] = 255
    return Image.fromarray(arr, mode='RGBA')


def _add_noise(img, rng, strength=8.0, chroma=0.3):
    arr = np.asarray(img, dtype=np.int16).copy()
    H, W = arr.shape[:2]
    noise = rng.normal(0, strength, size=(H, W, 1))
    color_noise = rng.normal(0, strength * chroma, size=(H, W, 3))
    x = np.linspace(-1.0, 1.0, W, dtype=np.float32)[None, :, None]
    y = np.linspace(-1.0, 1.0, H, dtype=np.float32)[:, None, None]
    vignette = -strength * 0.18 * (x * x + y * y)
    arr[..., :3] = np.clip(arr[..., :3] + noise + color_noise + vignette, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), mode='RGBA')


def _draw_bevel(draw, box, *, fill, highlight, shadow, width=1):
    x1, y1, x2, y2 = box
    draw.rectangle(box, fill=fill)
    draw.line((x1, y1, x2, y1), fill=highlight, width=width)
    draw.line((x1, y1, x1, y2), fill=highlight, width=width)
    draw.line((x1, y2, x2, y2), fill=shadow, width=width)
    draw.line((x2, y1, x2, y2), fill=shadow, width=width)


# Material renderers

def _render_wall_blocks(W, H, rng):
    img = _base_rgba(W, H, (203, 188, 171))
    img = _add_noise(img, rng, 4.0, 0.18)
    draw = ImageDraw.Draw(img, 'RGBA')
    block_h = max(5, H // 4)
    block_w = max(9, W // 3)
    mortar = (126, 110, 96, 255)
    for row, y in enumerate(range(0, H, block_h)):
        offset = (block_w // 2) if (row % 2) else 0
        for x in range(-offset, W, block_w):
            x1 = x
            y1 = y
            x2 = min(W - 1, x + block_w - 2)
            y2 = min(H - 1, y + block_h - 2)
            fill = _mix((205, 192, 175), (188, 171, 154), rng.uniform(0.0, 1.0)) + (255,)
            _draw_bevel(draw, (x1, y1, x2, y2), fill=fill,
                        highlight=(236, 225, 210, 255), shadow=(154, 137, 120, 255))
        draw.line((0, y, W, y), fill=mortar, width=1)
    return img


def _render_checker_marble(W, H, rng):
    img = _base_rgba(W, H, (170, 164, 159))
    draw = ImageDraw.Draw(img, 'RGBA')
    cells_y = 4
    cell = max(4, H // cells_y)
    palette = [(182, 177, 171), (140, 138, 140)]
    for y in range(0, H, cell):
        for x in range(0, W, cell):
            idx = ((x // cell) + (y // cell)) % 2
            base = palette[idx]
            fill = _mix(base, (210, 206, 201), 0.15 if idx == 0 else 0.05) + (255,)
            draw.rectangle((x, y, min(W - 1, x + cell - 1), min(H - 1, y + cell - 1)), fill=fill)
    # marble veins
    for _ in range(8):
        pts = []
        cx = int(rng.randint(0, W))
        for yi in np.linspace(0, H - 1, 5):
            cx = int(np.clip(cx + rng.randint(-6, 7), 0, W - 1))
            pts.append((cx, int(yi)))
        draw.line(pts, fill=(226, 224, 222, 80), width=1)
    img = _add_noise(img, rng, 3.0, 0.12)
    return img


def _render_red_carpet(W, H, rng, *, border=False):
    img = _base_rgba(W, H, (116, 24, 37))
    arr = np.asarray(img, dtype=np.int16).copy()
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    nap = (np.sin(np.linspace(0, math.pi * 6, H, dtype=np.float32))[:, None] * 10.0)
    arr[..., 0] = np.clip(arr[..., 0] + nap + y * 14, 0, 255)
    arr[..., 1] = np.clip(arr[..., 1] + nap * 0.4, 0, 255)
    arr[..., 2] = np.clip(arr[..., 2] + nap * 0.25, 0, 255)
    img = Image.fromarray(arr.astype(np.uint8), mode='RGBA')
    img = _add_noise(img, rng, 4.2, 0.15)
    draw = ImageDraw.Draw(img, 'RGBA')
    gold = (220, 181, 73, 255)
    dark_gold = (117, 84, 23, 255)
    if border:
        margin = max(2, min(W, H) // 10)
        draw.rectangle((margin, margin, W - margin - 1, H - margin - 1), outline=gold, width=max(1, margin // 3))
        draw.rectangle((margin + 2, margin + 2, W - margin - 3, H - margin - 3), outline=dark_gold, width=1)
        for frac in (0.22, 0.50, 0.78):
            cy = int(H * frac)
            r = max(1, H // 12)
            draw.ellipse((W // 2 - r, cy - r, W // 2 + r, cy + r), fill=(239, 218, 134, 120))
    else:
        draw.line((0, H // 2, W, H // 2), fill=(175, 49, 59, 70), width=max(1, H // 8))
        edge = max(1, W // 16)
        draw.rectangle((0, 0, edge, H), fill=(147, 41, 47, 88))
        draw.rectangle((W - edge, 0, W, H), fill=(92, 13, 20, 110))
    return img


def _render_parquet(W, H, rng):
    img = _base_rgba(W, H, (126, 89, 44))
    draw = ImageDraw.Draw(img, 'RGBA')
    plank_h = max(4, H // 6)
    colors = [(141, 103, 56), (127, 90, 45), (112, 79, 39)]
    for row, y in enumerate(range(0, H, plank_h)):
        seg = max(8, W // 3)
        shift = (seg // 2) if row % 2 else 0
        for x in range(-shift, W, seg):
            color = colors[(row + x // max(seg, 1)) % len(colors)]
            rect = (x, y, min(W - 1, x + seg - 1), min(H - 1, y + plank_h - 1))
            _draw_bevel(draw, rect, fill=color + (255,),
                        highlight=(183, 142, 86, 255), shadow=(87, 58, 24, 255))
            draw.line((x + seg // 2, y + 1, x + seg // 2, min(H - 1, y + plank_h - 2)), fill=(81, 52, 21, 90), width=1)
    img = _add_noise(img, rng, 4.5, 0.18)
    return img


def _render_wall_panel(W, H, rng):
    img = _base_rgba(W, H, (219, 210, 189))
    img = _add_noise(img, rng, 3.5, 0.08)
    draw = ImageDraw.Draw(img, 'RGBA')
    margin = max(3, min(W, H) // 8)
    _draw_bevel(draw, (margin, margin, W - margin - 1, H - margin - 1),
                fill=(228, 221, 202, 255),
                highlight=(244, 238, 224, 255), shadow=(171, 152, 126, 255),
                width=max(1, margin // 3))
    inner = margin + max(2, margin // 2)
    draw.rectangle((inner, inner, W - inner - 1, H - inner - 1), outline=(196, 176, 143, 255), width=1)
    return img


def _render_stone_column(W, H, rng):
    img = _base_rgba(W, H, (164, 158, 156))
    arr = np.asarray(img, dtype=np.int16).copy()
    x = np.linspace(-1.0, 1.0, W, dtype=np.float32)[None, :]
    shade = 28 * np.cos(x * math.pi)
    arr[..., 0] = np.clip(arr[..., 0] + shade, 0, 255)
    arr[..., 1] = np.clip(arr[..., 1] + shade, 0, 255)
    arr[..., 2] = np.clip(arr[..., 2] + shade, 0, 255)
    img = Image.fromarray(arr.astype(np.uint8), mode='RGBA')
    img = _add_noise(img, rng, 2.8, 0.08)
    draw = ImageDraw.Draw(img, 'RGBA')
    for y in [0, H // 3, 2 * H // 3, H - max(2, H // 8)]:
        draw.line((0, y, W, y), fill=(117, 112, 111, 255), width=max(1, H // 12))
        draw.line((0, min(H - 1, y + 1), W, min(H - 1, y + 1)), fill=(216, 211, 208, 120), width=1)
    return img


def _render_ceiling_panel(W, H, rng):
    img = _base_rgba(W, H, (231, 225, 210))
    img = _add_noise(img, rng, 2.7, 0.08)
    draw = ImageDraw.Draw(img, 'RGBA')
    margin = max(3, min(W, H) // 7)
    _draw_bevel(draw, (margin, margin, W - margin - 1, H - margin - 1),
                fill=(236, 232, 222, 255),
                highlight=(251, 249, 240, 255), shadow=(183, 172, 151, 255),
                width=max(1, margin // 4))
    rosette_r = max(2, min(W, H) // 10)
    cx, cy = W // 2, H // 2
    draw.ellipse((cx - rosette_r, cy - rosette_r, cx + rosette_r, cy + rosette_r),
                 fill=(221, 198, 128, 255), outline=(159, 125, 46, 255), width=1)
    return img


def _render_wainscot(W, H, rng):
    img = _base_rgba(W, H, (110, 73, 34))
    img = _add_noise(img, rng, 4.0, 0.15)
    draw = ImageDraw.Draw(img, 'RGBA')
    panel_w = max(7, W // 4)
    for x in range(0, W, panel_w):
        _draw_bevel(draw, (x, 0, min(W - 1, x + panel_w - 1), H - 1),
                    fill=(118, 79, 38, 255),
                    highlight=(166, 123, 72, 255), shadow=(70, 41, 15, 255),
                    width=1)
    cap_h = max(3, H // 6)
    draw.rectangle((0, 0, W, cap_h), fill=(90, 56, 24, 180))
    draw.line((0, cap_h, W, cap_h), fill=(189, 149, 90, 120), width=1)
    return img


def _render_wallpaper(W, H, rng):
    img = _base_rgba(W, H, (82, 106, 142))
    img = _add_noise(img, rng, 3.0, 0.12)
    draw = ImageDraw.Draw(img, 'RGBA')
    sx = max(8, W // 4)
    sy = max(8, H // 4)
    for cy in range(sy // 2, H + sy, sy):
        for cx in range(sx // 2, W + sx, sx):
            diamond = [(cx, cy - sy // 2), (cx + sx // 2, cy), (cx, cy + sy // 2), (cx - sx // 2, cy)]
            draw.polygon(diamond, outline=(214, 223, 235, 170), fill=(99, 125, 164, 60))
            draw.ellipse((cx - 1, cy - 1, cx + 1, cy + 1), fill=(230, 195, 105, 160))
    return img


def _render_star_medallion(W, H, rng):
    img = _render_checker_marble(W, H, rng)
    draw = ImageDraw.Draw(img, 'RGBA')
    cx, cy = W // 2, H // 2
    r = max(6, min(W, H) // 3)
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(222, 208, 161, 220), outline=(124, 100, 52, 255), width=1)
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r * (0.95 if i % 2 == 0 else 0.42)
        pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
    draw.polygon(pts, fill=(233, 191, 69, 255), outline=(125, 82, 20, 255))
    return img


def _render_bronze_plate(W, H, rng):
    img = _base_rgba(W, H, (139, 106, 54))
    img = _add_noise(img, rng, 4.0, 0.18)
    draw = ImageDraw.Draw(img, 'RGBA')
    margin = max(3, min(W, H) // 8)
    _draw_bevel(draw, (margin, margin, W - margin - 1, H - margin - 1),
                fill=(150, 114, 58, 255),
                highlight=(209, 173, 102, 255), shadow=(84, 58, 23, 255),
                width=max(1, margin // 3))
    for frac in (0.25, 0.5, 0.75):
        y = int(H * frac)
        draw.line((margin + 3, y, W - margin - 3, y), fill=(214, 178, 107, 100), width=1)
    bolt_r = max(1, min(W, H) // 18)
    for px, py in [(margin + 5, margin + 5), (W - margin - 5, margin + 5), (margin + 5, H - margin - 5), (W - margin - 5, H - margin - 5)]:
        draw.ellipse((px - bolt_r, py - bolt_r, px + bolt_r, py + bolt_r), fill=(235, 205, 138, 255), outline=(88, 61, 18, 255), width=1)
    return img


def _render_iron_railing_mask(W, H, rng):
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    arr[..., :3] = (176, 184, 196)
    img = Image.fromarray(arr, mode='RGBA')
    draw = ImageDraw.Draw(img, 'RGBA')
    # Fill background transparent, then draw opaque iron bars.
    spacing = max(6, W // 6)
    bar_w = max(2, spacing // 4)
    for x in range(spacing // 2, W, spacing):
        draw.rectangle((x - bar_w // 2, 0, x + (bar_w - 1) // 2, H - 1), fill=(181, 188, 199, 255))
        knop_r = max(1, H // 10)
        draw.ellipse((x - knop_r, H // 5 - knop_r, x + knop_r, H // 5 + knop_r), fill=(208, 214, 222, 255))
    rail_h = max(3, H // 7)
    draw.rectangle((0, rail_h, W - 1, rail_h + max(1, bar_w)), fill=(160, 166, 176, 255))
    draw.rectangle((0, H - rail_h - max(1, bar_w), W - 1, H - rail_h), fill=(124, 129, 139, 255))
    return img


def _render_glow_mask(W, H, rng, *, warm=False):
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]
    dx = (xx - (W - 1) / 2) / max(W * 0.5, 1)
    dy = (yy - (H - 1) / 2) / max(H * 0.5, 1)
    dist = np.sqrt(dx * dx + dy * dy)
    alpha = np.clip(np.maximum(0.0, 1.0 - dist) ** 2.2 * 255, 0, 255).astype(np.uint8)
    if warm:
        rgb = np.dstack([
            np.full((H, W), 255, dtype=np.uint8),
            np.full((H, W), 227, dtype=np.uint8),
            np.full((H, W), 161, dtype=np.uint8),
        ])
    else:
        rgb = np.dstack([
            np.full((H, W), 214, dtype=np.uint8),
            np.full((H, W), 230, dtype=np.uint8),
            np.full((H, W), 255, dtype=np.uint8),
        ])
    arr[..., :3] = rgb
    arr[..., 3] = alpha
    return Image.fromarray(arr, mode='RGBA')


_RENDERERS = {
    'wall_blocks': _render_wall_blocks,
    'checker_marble_floor': _render_checker_marble,
    'red_carpet_runner': _render_red_carpet,
    'carpet_border': lambda W, H, rng: _render_red_carpet(W, H, rng, border=True),
    'parquet_floor': _render_parquet,
    'wall_plaster_panel': _render_wall_panel,
    'stone_column': _render_stone_column,
    'ceiling_panel': _render_ceiling_panel,
    'wood_wainscot': _render_wainscot,
    'blue_diamond_wallpaper': _render_wallpaper,
    'star_medallion_tile': _render_star_medallion,
    'bronze_door_plate': _render_bronze_plate,
    'iron_railing_mask': _render_iron_railing_mask,
    'window_glow_mask': lambda W, H, rng: _render_glow_mask(W, H, rng, warm=False),
    'castle_light_glow': lambda W, H, rng: _render_glow_mask(W, H, rng, warm=True),
}


def render_castle_inside_texture(fname, shape, rng=None, identity=None):
    kind = CASTLE_INSIDE_TEXTURE_SPECS[str(fname)]
    if rng is None:
        rng = _stable_rng(fname)
    H, W = 64, 64
    renderer = _RENDERERS[kind]
    img = renderer(W, H, rng)
    return _finish(img, shape)


__all__ = [
    'CASTLE_INSIDE_TEXTURE_SPECS',
    'render_castle_inside_texture',
    'supports_castle_inside_texture',
]
