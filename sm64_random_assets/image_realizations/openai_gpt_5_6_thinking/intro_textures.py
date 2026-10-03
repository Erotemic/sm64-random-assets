from __future__ import annotations

import hashlib
import math
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


TITLE_BACKGROUND_FILES = (
    'textures/title_screen_bg/title_screen_bg.001C0.rgba16.png',
    'textures/title_screen_bg/title_screen_bg.00E40.rgba16.png',
    'textures/title_screen_bg/title_screen_bg.01AC0.rgba16.png',
    'textures/title_screen_bg/title_screen_bg.02740.rgba16.png',
    'textures/title_screen_bg/title_screen_bg.033C0.rgba16.png',
    'textures/title_screen_bg/title_screen_bg.04040.rgba16.png',
    'textures/title_screen_bg/title_screen_bg.04CC0.rgba16.png',
    'textures/title_screen_bg/title_screen_bg.05940.rgba16.png',
)

INTRO_LEVEL_FILES = frozenset({
    'levels/intro/0.rgba16.png',
    'levels/intro/1.rgba16.png',
})

INTRO_RAW_FILES = frozenset({
    'textures/intro_raw/hand_closed.rgba16.png',
    'textures/intro_raw/hand_open.rgba16.png',
    'textures/intro_raw/mario_face_shine.ia8.png',
    *[f'textures/intro_raw/red_star_{i}.rgba16.png' for i in range(8)],
    *[f'textures/intro_raw/white_star_{i}.rgba16.png' for i in range(8)],
    *[f'textures/intro_raw/sparkle_{i}.rgba16.png' for i in range(6)],
})

INTRO_TEXTURE_FILES = frozenset(TITLE_BACKGROUND_FILES) | INTRO_LEVEL_FILES | INTRO_RAW_FILES


def _stable_seed(text: str) -> int:
    return int(hashlib.sha256(text.encode('utf8')).hexdigest()[:16], 16) & 0x7FFFFFFF


def _local_rng(rng, fname: str):
    if rng is None:
        return np.random.RandomState(_stable_seed(fname))
    return np.random.RandomState(int(rng.randint(0, 2 ** 31 - 1)) ^ _stable_seed(fname))


def supports_intro_texture(identity, info) -> bool:
    return identity.fname in INTRO_TEXTURE_FILES


def _mix(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def _finish_rgba(img: Image.Image, shape):
    h, w = int(shape[0]), int(shape[1])
    if img.size != (w, h):
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


def _rounded_rect(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _render_intro_material(fname: str, shape, rng):
    h, w = int(shape[0]), int(shape[1])
    scale = 4
    W, H = w * scale, h * scale
    img = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img, 'RGBA')

    is_face = fname.endswith('/0.rgba16.png')
    if is_face:
        top = (255, 89, 35)
        bottom = (179, 21, 31)
        accent = (255, 218, 72)
        dark = (87, 10, 25)
    else:
        top = (40, 128, 237)
        bottom = (22, 45, 142)
        accent = (115, 232, 255)
        dark = (8, 19, 70)

    for y in range(H):
        t = y / max(1, H - 1)
        color = _mix(top, bottom, t)
        draw.line((0, y, W, y), fill=color + (255,))

    # Chunky beveled tiles read well when mapped over 3D title geometry.
    cell = max(8 * scale, W // 4)
    for row, y in enumerate(range(-cell // 2, H + cell, cell)):
        offset = cell // 2 if row % 2 else 0
        for x in range(-cell + offset, W + cell, cell):
            jitter = int(rng.randint(-12, 13))
            fill = tuple(int(np.clip(c + jitter, 0, 255)) for c in _mix(top, bottom, 0.45)) + (210,)
            _rounded_rect(
                draw,
                (x + scale, y + scale, x + cell - scale, y + cell - scale),
                radius=max(2 * scale, cell // 7),
                fill=fill,
                outline=dark + (180,),
                width=max(1, scale),
            )
            draw.line(
                (x + 3 * scale, y + 3 * scale, x + cell - 4 * scale, y + 3 * scale),
                fill=accent + (150,),
                width=max(1, scale),
            )

    # Add a strong diagonal shine and sparse glints so the two materials are not flat.
    shine = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shine, 'RGBA')
    band = max(5 * scale, W // 8)
    sdraw.polygon(
        [(-band, H), (W // 3, 0), (W // 3 + band, 0), (band, H)],
        fill=(255, 255, 255, 65),
    )
    for _ in range(5):
        x = int(rng.randint(0, W))
        y = int(rng.randint(0, H))
        r = int(rng.randint(scale, 3 * scale + 1))
        sdraw.line((x - r * 2, y, x + r * 2, y), fill=(255, 255, 255, 150), width=max(1, scale // 2))
        sdraw.line((x, y - r * 2, x, y + r * 2), fill=(255, 255, 255, 150), width=max(1, scale // 2))
    img = Image.alpha_composite(img, shine)
    return _finish_rgba(img, shape)


def _make_title_background_canvas():
    # The eight source files are equal 80x20 strips. Author one coherent 80x160
    # image and return the matching strip for each filename.
    W, H = 80, 160
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]

    cx, cy = 39.5, 65.0
    dx = (xx - cx) / W
    dy = (yy - cy) / H
    radius = np.sqrt(dx * dx + dy * dy)
    angle = np.arctan2(dy, dx)

    # Saturated midnight-blue field with radial title rays.
    ray = 0.5 + 0.5 * np.cos(angle * 12.0 + radius * 15.0)
    vignette = np.clip(1.15 - radius * 1.35, 0.0, 1.0)
    vertical = yy / max(1, H - 1)
    arr[..., 0] = np.clip(16 + 20 * ray + 13 * vignette + 18 * vertical, 0, 255)
    arr[..., 1] = np.clip(42 + 55 * ray + 52 * vignette + 16 * vertical, 0, 255)
    arr[..., 2] = np.clip(112 + 75 * ray + 66 * vignette, 0, 255)
    arr[..., 3] = 255

    img = Image.fromarray(arr, 'RGBA')
    draw = ImageDraw.Draw(img, 'RGBA')

    # Broad translucent arcs imply motion without competing with the title logo.
    for i, box in enumerate([
        (-32, 20, 112, 150),
        (-18, 36, 98, 136),
        (-5, 50, 85, 124),
    ]):
        draw.arc(box, 198, 342, fill=(104, 224, 255, 58 - i * 11), width=2)

    # Deterministic stars distributed over the assembled background, not per strip.
    rng = np.random.RandomState(728160)
    for i in range(54):
        x = int(rng.randint(2, W - 2))
        y = int(rng.randint(2, H - 2))
        r = 1 if i < 43 else 2
        alpha = int(rng.randint(100, 225))
        draw.point((x, y), fill=(235, 248, 255, alpha))
        if r == 2:
            draw.line((x - 2, y, x + 2, y), fill=(240, 251, 255, alpha), width=1)
            draw.line((x, y - 2, x, y + 2), fill=(240, 251, 255, alpha), width=1)

    # Warm glow behind the title area.
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    g = np.zeros((H, W), dtype=np.uint8)
    gx, gy = 39.5, 72.0
    gd = np.sqrt(((xx - gx) / 36.0) ** 2 + ((yy - gy) / 48.0) ** 2)
    g[:] = np.clip((1.0 - gd) * 62, 0, 62).astype(np.uint8)
    glow_arr = np.zeros((H, W, 4), dtype=np.uint8)
    glow_arr[..., 0] = 255
    glow_arr[..., 1] = 174
    glow_arr[..., 2] = 72
    glow_arr[..., 3] = g
    img = Image.alpha_composite(img, Image.fromarray(glow_arr, 'RGBA'))
    # Background strips are opaque screen tiles; decorative drawing must not
    # accidentally punch semi-transparent bands into the backdrop.
    img.putalpha(255)
    return img


_TITLE_BACKGROUND_CANVAS = _make_title_background_canvas()


def _render_title_background(fname: str, shape):
    index = TITLE_BACKGROUND_FILES.index(fname)
    strip = _TITLE_BACKGROUND_CANVAS.crop((0, index * 20, 80, (index + 1) * 20))
    return _finish_rgba(strip, shape)


def _star_points(cx, cy, outer, inner, rotation=-math.pi / 2):
    points = []
    for i in range(10):
        radius = outer if i % 2 == 0 else inner
        angle = rotation + i * math.pi / 5.0
        points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    return points


def _render_spinning_star(fname: str, shape, rng):
    h, w = int(shape[0]), int(shape[1])
    scale = 5
    W, H = w * scale, h * scale
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, 'RGBA')
    match = re.search(r'_(\d+)\.', fname)
    frame = int(match.group(1)) if match else 0
    phase = frame / 8.0 * math.tau
    horizontal = 0.24 + 0.76 * abs(math.cos(phase))
    tilt = math.sin(phase) * 0.16
    cx, cy = W / 2.0, H / 2.0
    outer = min(W, H) * 0.39
    inner = outer * 0.43

    red = '/red_star_' in fname
    face = (232, 49, 50) if red else (244, 249, 255)
    face2 = (255, 143, 56) if red else (171, 224, 255)
    edge = (109, 12, 27) if red else (69, 120, 180)

    raw = _star_points(0.0, 0.0, outer, inner, -math.pi / 2 + tilt)
    points = [(cx + x * horizontal, cy + y) for x, y in raw]
    shadow = [(x + 2 * scale, y + 2 * scale) for x, y in points]
    draw.polygon(shadow, fill=edge + (120,))
    draw.polygon(points, fill=face + (255,), outline=edge + (255,))

    # Half-face shading changes side over the rotation.
    shade_left = math.cos(phase) >= 0
    clip_box = (0, 0, int(cx), H) if shade_left else (int(cx), 0, W, H)
    shade = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shade, 'RGBA')
    sdraw.rectangle(clip_box, fill=face2 + (95,))
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    shade.putalpha(Image.composite(shade.getchannel('A'), Image.new('L', (W, H), 0), mask))
    img = Image.alpha_composite(img, shade)

    draw = ImageDraw.Draw(img, 'RGBA')
    glint_x = cx - outer * horizontal * 0.25 * math.cos(phase)
    glint_y = cy - outer * 0.28
    r = max(scale, int(outer * 0.08))
    draw.line((glint_x - r, glint_y, glint_x + r, glint_y), fill=(255, 255, 255, 220), width=max(1, scale // 2))
    draw.line((glint_x, glint_y - r, glint_x, glint_y + r), fill=(255, 255, 255, 220), width=max(1, scale // 2))
    return _finish_rgba(img, shape)


def _render_sparkle(fname: str, shape):
    h, w = int(shape[0]), int(shape[1])
    scale = 5
    W, H = w * scale, h * scale
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, 'RGBA')
    m = re.search(r'_(\d+)\.', fname)
    frame = int(m.group(1)) if m is not None else 0
    envelope = [0.18, 0.45, 0.78, 1.0, 0.70, 0.32][frame % 6]
    cx, cy = W // 2, H // 2
    long_r = int(min(W, H) * 0.43 * envelope)
    short_r = max(scale, int(long_r * 0.28))
    alpha = int(130 + 125 * envelope)

    # Soft halo.
    halo = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(halo, 'RGBA')
    hr = max(scale, int(long_r * 0.55))
    hdraw.ellipse((cx - hr, cy - hr, cx + hr, cy + hr), fill=(114, 215, 255, int(55 * envelope)))
    halo = halo.filter(ImageFilter.GaussianBlur(max(1, scale * 2)))
    img = Image.alpha_composite(img, halo)
    draw = ImageDraw.Draw(img, 'RGBA')

    draw.polygon(
        [(cx, cy - long_r), (cx + short_r, cy - short_r),
         (cx + long_r, cy), (cx + short_r, cy + short_r),
         (cx, cy + long_r), (cx - short_r, cy + short_r),
         (cx - long_r, cy), (cx - short_r, cy - short_r)],
        fill=(247, 253, 255, alpha),
    )
    core = max(scale, int(short_r * 0.55))
    draw.ellipse((cx - core, cy - core, cx + core, cy + core), fill=(255, 247, 163, 255))
    return _finish_rgba(img, shape)


def _render_face_shine(shape):
    h, w = int(shape[0]), int(shape[1])
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w * 0.38, h * 0.32
    dist = np.sqrt(((xx - cx) / max(w * 0.44, 1)) ** 2 + ((yy - cy) / max(h * 0.34, 1)) ** 2)
    alpha = np.clip((1.0 - dist) * 235, 0, 235)
    # Add a narrow diagonal highlight streak.
    line = np.exp(-((yy - (0.55 * xx + h * 0.03)) ** 2) / max(1.0, (h * 0.08) ** 2))
    alpha = np.maximum(alpha, line * 120)
    intensity = np.clip(175 + alpha * 0.34, 0, 255)
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., :3] = intensity[..., None].astype(np.uint8)
    rgba[..., 3] = alpha.astype(np.uint8)
    return _finish_rgba(Image.fromarray(rgba, 'RGBA'), shape)


def _render_glove(fname: str, shape):
    h, w = int(shape[0]), int(shape[1])
    scale = 6
    W, H = w * scale, h * scale
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, 'RGBA')
    outline = (34, 44, 66, 255)
    white = (249, 250, 244, 255)
    shade = (159, 197, 224, 220)
    cuff = (224, 233, 240, 255)

    if 'hand_open' in fname:
        # Palm.
        _rounded_rect(draw, (W * 0.27, H * 0.36, W * 0.78, H * 0.82), W * 0.13,
                      white, outline, width=scale)
        # Four spread fingers.
        finger_boxes = [
            (0.18, 0.10, 0.36, 0.55),
            (0.34, 0.03, 0.51, 0.49),
            (0.50, 0.05, 0.67, 0.51),
            (0.64, 0.13, 0.81, 0.58),
        ]
        for box in finger_boxes:
            b = tuple(int(v * (W if i % 2 == 0 else H)) for i, v in enumerate(box))
            _rounded_rect(draw, b, W * 0.08, white, outline, width=scale)
        # Thumb angled outward.
        draw.ellipse((W * 0.08, H * 0.46, W * 0.43, H * 0.76), fill=white, outline=outline, width=scale)
        draw.arc((W * 0.23, H * 0.48, W * 0.60, H * 0.84), 205, 320, fill=shade, width=scale)
    else:
        # Closed fist with distinct knuckles and thumb wrap.
        _rounded_rect(draw, (W * 0.18, H * 0.19, W * 0.82, H * 0.77), W * 0.16,
                      white, outline, width=scale)
        for i in range(3):
            x = W * (0.31 + 0.17 * i)
            draw.line((x, H * 0.22, x - W * 0.03, H * 0.48), fill=shade, width=scale)
        draw.ellipse((W * 0.23, H * 0.45, W * 0.76, H * 0.75), fill=white, outline=outline, width=scale)
        draw.arc((W * 0.29, H * 0.49, W * 0.73, H * 0.73), 185, 345, fill=shade, width=scale)

    # Cuff shared by both poses.
    _rounded_rect(draw, (W * 0.31, H * 0.73, W * 0.72, H * 0.96), W * 0.08,
                  cuff, outline, width=scale)
    draw.line((W * 0.36, H * 0.83, W * 0.67, H * 0.83), fill=shade, width=scale)
    return _finish_rgba(img, shape)


def render_intro_texture(fname: str, shape, rng=None, identity=None):
    if fname not in INTRO_TEXTURE_FILES:
        return None
    local_rng = _local_rng(rng, fname)
    if fname in TITLE_BACKGROUND_FILES:
        return _render_title_background(fname, shape)
    if fname in INTRO_LEVEL_FILES:
        return _render_intro_material(fname, shape, local_rng)
    if fname.endswith('hand_open.rgba16.png') or fname.endswith('hand_closed.rgba16.png'):
        return _render_glove(fname, shape)
    if fname.endswith('mario_face_shine.ia8.png'):
        return _render_face_shine(shape)
    if '/red_star_' in fname or '/white_star_' in fname:
        return _render_spinning_star(fname, shape, local_rng)
    if '/sparkle_' in fname:
        return _render_sparkle(fname, shape)
    return None


__all__ = [
    'INTRO_TEXTURE_FILES',
    'TITLE_BACKGROUND_FILES',
    'render_intro_texture',
    'supports_intro_texture',
]
