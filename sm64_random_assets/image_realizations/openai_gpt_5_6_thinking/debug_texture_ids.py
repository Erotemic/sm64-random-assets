from __future__ import annotations

import hashlib
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFont


_HEX_RE = re.compile(r'^[0-9A-F]{3,}$')


def _is_debuggable_fname(fname: str) -> bool:
    if not fname.endswith('.png'):
        return False
    if fname.startswith('actors/') or fname.startswith('textures/segment2/') or fname.startswith('textures/ipl3_raw/'):
        return False
    tokens = re.split(r'[/. _-]+', fname)
    for tok in tokens:
        if tok.isdigit() or _HEX_RE.match(tok):
            return True
    return False


def supports_debug_texture_id(identity, info):
    return _is_debuggable_fname(str(identity.fname))


def _stable_seed(text: str) -> int:
    return int(hashlib.sha256(text.encode('utf8')).hexdigest()[:16], 16) & 0x7FFFFFFF


def _short_label(fname: str) -> str:
    parts = fname.split('/')
    stem_parts = parts[-1].split('.')
    numeric = None
    for tok in stem_parts + parts:
        tok = tok.upper()
        if tok.isdigit() or _HEX_RE.match(tok):
            numeric = tok
            break
    group = ''.join(c for c in (parts[-2] if len(parts) >= 2 else 'GEN').upper() if c.isalnum())[:3] or 'GEN'
    if numeric is None:
        numeric = hashlib.sha256(fname.encode('utf8')).hexdigest()[:4].upper()
    return f'{group}-{numeric}'


def _finish(img, shape):
    h, w = int(shape[0]), int(shape[1])
    img = img.resize((w, h), Image.Resampling.NEAREST)
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
    if len(shape) == 3 and shape[2] == 2:
        return np.stack([intensity, rgba[..., 3]], axis=2)
    return intensity


def render_debug_texture_id(fname, shape, rng=None, identity=None):
    seed = _stable_seed(str(fname))
    if rng is None:
        rng = np.random.RandomState(seed)
    H = max(48, int(shape[0]) * 2)
    W = max(48, int(shape[1]) * 2)
    label = _short_label(str(fname))
    bg = np.array([
        40 + (seed >> 0) % 150,
        40 + (seed >> 8) % 150,
        40 + (seed >> 16) % 150,
        255,
    ], dtype=np.uint8)
    stripe = np.array([
        255 - bg[0] // 2,
        255 - bg[1] // 2,
        255 - bg[2] // 2,
        255,
    ], dtype=np.uint8)
    arr = np.empty((H, W, 4), dtype=np.uint8)
    arr[:] = bg
    yy, xx = np.mgrid[0:H, 0:W]
    mask = ((xx + yy) // max(6, min(H, W) // 8)) % 2 == 0
    arr[mask, :3] = ((arr[mask, :3].astype(np.int16) + stripe[:3].astype(np.int16)) // 2).astype(np.uint8)
    img = Image.fromarray(arr, mode='RGBA')
    draw = ImageDraw.Draw(img, 'RGBA')
    font = ImageFont.load_default()

    # bold outer frame and orientation arrows
    frame = max(2, min(H, W) // 16)
    draw.rectangle((0, 0, W - 1, H - 1), outline=(255, 255, 255, 255), width=frame)
    draw.polygon([(W * 0.18, H * 0.16), (W * 0.33, H * 0.07), (W * 0.33, H * 0.25)], fill=(255, 255, 255, 220))
    draw.polygon([(W * 0.82, H * 0.84), (W * 0.67, H * 0.75), (W * 0.67, H * 0.93)], fill=(0, 0, 0, 150))

    # Distinct corners help identify flips and rotations in screenshots.
    corner = max(6, min(H, W) // 6)
    draw.rectangle((0, 0, corner, corner), fill=(255, 255, 255, 220))
    draw.rectangle((W - corner - 1, 0, W - 1, corner), fill=(0, 0, 0, 200))
    draw.rectangle((0, H - corner - 1, corner, H - 1), fill=(255, 210, 0, 220))
    draw.rectangle((W - corner - 1, H - corner - 1, W - 1, H - 1), fill=(40, 220, 255, 220))

    # Crosshair and label blocks
    draw.line((W // 2, 0, W // 2, H), fill=(255, 255, 255, 120), width=1)
    draw.line((0, H // 2, W, H // 2), fill=(255, 255, 255, 120), width=1)
    draw.rounded_rectangle((frame + 1, H * 0.34, W - frame - 1, H * 0.68), radius=4, fill=(8, 8, 8, 170))
    # large label scaled by repetition for readability at tiny resolutions
    tw = max(1, W // max(1, len(label) * 6))
    text = label
    tx = int(W * 0.08)
    ty = int(H * 0.42)
    for ox in range(tw):
        for oy in range(tw):
            draw.text((tx + ox, ty + oy), text, font=font, fill=(255, 255, 255, 255))
    draw.text((frame + 2, frame + 2), str(fname).split('/')[-2][:8], font=font, fill=(0, 0, 0, 255))
    draw.text((frame + 3, H - 10 - frame), str(fname).split('/')[-1][:18], font=font, fill=(255, 255, 255, 255))

    # If the output expects alpha, preserve an opaque center and soft transparent edges.
    if len(shape) == 3 and shape[2] == 2:
        alpha = np.full((H, W), 255, dtype=np.uint8)
        alpha[:frame] = 0
        alpha[-frame:] = 0
        alpha[:, :frame] = 0
        alpha[:, -frame:] = 0
        rgba = np.asarray(img, dtype=np.uint8).copy()
        rgba[..., 3] = alpha
        img = Image.fromarray(rgba, mode='RGBA')
    return _finish(img, shape)


__all__ = [
    'render_debug_texture_id',
    'supports_debug_texture_id',
]
