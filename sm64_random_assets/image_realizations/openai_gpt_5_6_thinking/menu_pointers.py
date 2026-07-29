from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw


MENU_POINTER_FILES = {
    'levels/menu/main_menu_seg7.06328.rgba16.png': 'open',
    'levels/menu/main_menu_seg7.06B28.rgba16.png': 'pressed',
    'textures/intro_raw/hand_open.rgba16.png': 'open',
    'textures/intro_raw/hand_closed.rgba16.png': 'pressed',
}


def supports_menu_pointer(identity, info):
    return str(identity.fname) in MENU_POINTER_FILES


def _rounded(draw, box, radius, fill, outline=None, width=1):
    box = tuple(int(round(v)) for v in box)
    radius = max(1, int(round(radius)))
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=max(1, int(width)))


def _finish(img, shape):
    h, w = int(shape[0]), int(shape[1])
    img = img.resize((w, h), Image.Resampling.LANCZOS)
    rgba = np.asarray(img, dtype=np.uint8)
    # Keep very faint antialiasing from creating a dirty full-image halo.
    rgba = rgba.copy()
    rgba[rgba[..., 3] < 5] = 0
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


def _draw_open_pointer(draw, W, H, scale):
    outline = (29, 35, 52, 255)
    deep_outline = (12, 17, 29, 255)
    glove = (250, 250, 242, 255)
    glove_light = (255, 255, 253, 255)
    glove_mid = (196, 220, 235, 255)
    glove_shadow = (132, 174, 203, 255)
    cuff = (225, 235, 242, 255)

    # Wrist/cuff, angled slightly toward the lower-right.
    _rounded(draw, (W * 0.42, H * 0.69, W * 0.78, H * 0.95), W * 0.07,
             cuff, deep_outline, width=scale * 1.2)
    draw.line((W * 0.47, H * 0.80, W * 0.72, H * 0.84), fill=glove_shadow, width=scale)

    # Main palm.
    _rounded(draw, (W * 0.27, H * 0.32, W * 0.76, H * 0.78), W * 0.13,
             glove, deep_outline, width=scale * 1.4)

    # Extended index finger: unmistakable pointing silhouette.
    _rounded(draw, (W * 0.08, H * 0.18, W * 0.59, H * 0.39), W * 0.09,
             glove_light, deep_outline, width=scale * 1.4)
    draw.arc((W * 0.10, H * 0.19, W * 0.52, H * 0.40), 205, 330,
             fill=glove_mid, width=scale)

    # Curled middle/ring/pinky fingers.
    finger_boxes = [
        (0.42, 0.20, 0.65, 0.49),
        (0.55, 0.25, 0.77, 0.54),
        (0.63, 0.35, 0.83, 0.61),
    ]
    for x1, y1, x2, y2 in finger_boxes:
        _rounded(draw, (W * x1, H * y1, W * x2, H * y2), W * 0.08,
                 glove, outline, width=scale)

    # Thumb wrapped across the palm.
    draw.ellipse((W * 0.18, H * 0.45, W * 0.57, H * 0.73),
                 fill=glove, outline=deep_outline, width=scale)
    draw.arc((W * 0.24, H * 0.49, W * 0.62, H * 0.74), 185, 335,
             fill=glove_shadow, width=scale)

    # Palm creases and specular highlight.
    draw.arc((W * 0.35, H * 0.42, W * 0.68, H * 0.70), 125, 245,
             fill=glove_mid, width=scale)
    draw.line((W * 0.19, H * 0.24, W * 0.38, H * 0.23),
              fill=(255, 255, 255, 210), width=max(1, scale // 2))


def _draw_pressed_pointer(draw, W, H, scale):
    outline = (29, 35, 52, 255)
    deep_outline = (12, 17, 29, 255)
    glove = (248, 249, 241, 255)
    glove_light = (255, 255, 251, 255)
    glove_mid = (190, 215, 232, 255)
    glove_shadow = (126, 166, 198, 255)
    cuff = (219, 232, 241, 255)

    # Pressed state sits lower and is more compact so motion is visible in-game.
    _rounded(draw, (W * 0.36, H * 0.70, W * 0.76, H * 0.95), W * 0.07,
             cuff, deep_outline, width=scale * 1.2)
    draw.line((W * 0.42, H * 0.81, W * 0.70, H * 0.84),
              fill=glove_shadow, width=scale)

    # Fist body.
    _rounded(draw, (W * 0.18, H * 0.26, W * 0.79, H * 0.76), W * 0.15,
             glove, deep_outline, width=scale * 1.4)

    # Four knuckles with distinct lobes.
    knuckles = [
        (0.18, 0.19, 0.39, 0.46),
        (0.33, 0.15, 0.53, 0.43),
        (0.48, 0.17, 0.68, 0.45),
        (0.62, 0.23, 0.80, 0.50),
    ]
    for x1, y1, x2, y2 in knuckles:
        _rounded(draw, (W * x1, H * y1, W * x2, H * y2), W * 0.08,
                 glove_light, outline, width=scale)

    # Thumb presses across the curled fingers.
    draw.ellipse((W * 0.22, H * 0.43, W * 0.72, H * 0.72),
                 fill=glove, outline=deep_outline, width=scale)
    draw.arc((W * 0.29, H * 0.46, W * 0.70, H * 0.70), 180, 345,
             fill=glove_shadow, width=scale)

    # Knuckle seams make the state legible at 32x32.
    for x in (0.36, 0.51, 0.65):
        draw.line((W * x, H * 0.25, W * (x - 0.025), H * 0.45),
                  fill=glove_mid, width=scale)
    draw.arc((W * 0.28, H * 0.42, W * 0.60, H * 0.67), 105, 240,
             fill=glove_mid, width=scale)


def render_menu_pointer(fname, shape, rng=None, identity=None):
    state = MENU_POINTER_FILES.get(str(fname), None)
    if state is None:
        return None
    h, w = int(shape[0]), int(shape[1])
    scale = 8
    W, H = w * scale, h * scale
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, 'RGBA')
    if state == 'open':
        _draw_open_pointer(draw, W, H, scale)
    else:
        _draw_pressed_pointer(draw, W, H, scale)
    return _finish(img, shape)


__all__ = [
    'MENU_POINTER_FILES',
    'render_menu_pointer',
    'supports_menu_pointer',
]
