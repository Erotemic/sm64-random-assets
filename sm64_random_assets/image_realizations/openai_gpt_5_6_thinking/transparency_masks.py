
from __future__ import annotations

import math
import numpy as np

from sm64_random_assets.util import util_random

_EXCLUDED_PREFIXES = (
    'textures/ipl3_raw/',
    'textures/segment2/font_graphics.',
    'levels/menu/main_menu_seg7',
)

_EXCLUDED_EXACT = {
    'textures/intro_raw/mario_face_shine.ia8.png',
}

_EXPLICIT_LEVEL_MASKS = {
    'levels/castle_grounds/5.ia8.png',
    'levels/castle_inside/2.ia16.png',
    'levels/castle_inside/16.ia16.png',
    'levels/castle_inside/castle_light.ia16.png',
    'levels/ccm/8.ia16.png',
    'levels/ccm/9.ia16.png',
    'levels/lll/27.ia16.png',
    'levels/pss/1.ia16.png',
    'levels/ssl/1.ia16.png',
    'levels/totwc/3.ia16.png',
    'levels/ttm/0.ia16.png',
    'levels/wf/5.ia8.png',
}

_EXPLICIT_TEXTURE_MASKS = {
    'textures/cave/hmc_textures.0B800.ia16.png',
    'textures/cave/hmc_textures.0C000.ia16.png',
    'textures/generic/bob_textures.0B000.ia16.png',
    'textures/grass/wf_textures.0B000.ia16.png',
    'textures/grass/wf_textures.0B800.ia16.png',
    'textures/outside/castle_grounds_textures.0BC00.ia16.png',
    'textures/segment2/shadow_quarter_circle.ia8.png',
    'textures/segment2/shadow_quarter_square.ia8.png',
    'textures/snow/ccm_textures.09000.ia16.png',
    'textures/snow/ccm_textures.09800.ia16.png',
    'textures/spooky/bbh_textures.0A800.ia16.png',
    'textures/spooky/bbh_textures.0B000.ia16.png',
    'textures/spooky/bbh_textures.0B800.ia16.png',
}


def supports_transparency_mask(identity, info):
    shape = info.get('shape', None)
    if shape is None or len(shape) != 3 or shape[2] != 2:
        return False
    fname = str(identity.fname)
    if fname in _EXCLUDED_EXACT:
        return False
    if any(fname.startswith(prefix) for prefix in _EXCLUDED_PREFIXES):
        return False
    if fname in _EXPLICIT_LEVEL_MASKS or fname in _EXPLICIT_TEXTURE_MASKS:
        return True
    if fname.startswith('actors/') and fname.endswith(('.ia8.png', '.ia16.png', '.ia4.png', '.ia1.png')):
        return True
    return False


def _grid(shape):
    h, w = shape[0:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    xx = (xx + 0.5) / w * 2 - 1
    yy = (yy + 0.5) / h * 2 - 1
    return xx, yy


def _normalize(arr):
    arr = np.asarray(arr, dtype=np.float32)
    amin = float(arr.min())
    amax = float(arr.max())
    if amax - amin < 1e-6:
        return np.zeros_like(arr)
    return (arr - amin) / (amax - amin)


def _uint8_mask(intensity, alpha):
    intensity = np.clip(np.asarray(intensity, dtype=np.float32), 0, 1)
    alpha = np.clip(np.asarray(alpha, dtype=np.float32), 0, 1)
    out = np.stack([intensity, alpha], axis=2)
    return np.round(out * 255).astype(np.uint8)


def _ellipse(xx, yy, cx, cy, rx, ry, angle=0.0):
    ca, sa = math.cos(angle), math.sin(angle)
    x = xx - cx
    y = yy - cy
    xr = ca * x + sa * y
    yr = -sa * x + ca * y
    return (xr / max(rx, 1e-6)) ** 2 + (yr / max(ry, 1e-6)) ** 2 <= 1.0


def _soft_shadow(shape, kind='circle'):
    xx, yy = _grid(shape)
    if kind == 'circle':
        rr = np.sqrt((xx + 0.05) ** 2 + (yy + 0.05) ** 2)
        alpha = np.clip(1 - rr / 1.05, 0, 1) ** 2.0
    else:
        box = np.maximum(np.abs(xx), np.abs(yy))
        alpha = np.clip(1 - box / 0.98, 0, 1) ** 2.1
        alpha *= np.clip(1 - 0.25 * (xx + yy), 0.6, 1.0)
    intensity = 0.18 + 0.24 * alpha
    return _uint8_mask(intensity, alpha * 0.9)


def _fence_mask(shape, style='iron'):
    h, w = shape[0:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    bars = np.zeros((h, w), dtype=np.float32)
    spacing = max(5, int(round(w / 8)))
    thickness = max(1.0, spacing * 0.22)
    offset = spacing / 2
    for x0 in np.arange(offset, w, spacing):
        bars += np.exp(-((xx - x0) / thickness) ** 2 * 2.8)
    rails = np.exp(-((yy - h * 0.25) / max(1.2, h * 0.06)) ** 2 * 2.5)
    rails += np.exp(-((yy - h * 0.73) / max(1.2, h * 0.06)) ** 2 * 2.5)
    top_caps = np.zeros((h, w), dtype=np.float32)
    for x0 in np.arange(offset, w, spacing):
        top_caps += np.exp(-(((xx - x0) / max(1.2, thickness * 1.4)) ** 2 + ((yy - h * 0.08) / max(1.2, h * 0.09)) ** 2) * 3.5)
    alpha = _normalize(bars * 0.9 + rails * 0.7 + top_caps * (0.9 if style == 'iron' else 0.4))
    if style == 'chain':
        diag1 = np.exp(-((np.mod(xx + yy, spacing) - spacing / 2) / max(1.0, thickness * 0.9)) ** 2 * 1.6)
        diag2 = np.exp(-((np.mod(xx - yy, spacing) - spacing / 2) / max(1.0, thickness * 0.9)) ** 2 * 1.6)
        alpha = _normalize(0.85 * diag1 + 0.85 * diag2 + rails * 0.25)
    intensity = 0.55 + 0.35 * alpha
    return _uint8_mask(intensity, np.clip(alpha * 1.05, 0, 1))


def _hedge_mask(shape):
    xx, yy = _grid(shape)
    alpha = np.zeros(shape[0:2], dtype=np.float32)
    centers = [(-0.72, 0.20, 0.34, 0.48), (-0.36, 0.05, 0.32, 0.44),
               (0.00, 0.18, 0.36, 0.50), (0.38, 0.10, 0.34, 0.46), (0.72, 0.24, 0.32, 0.44)]
    for cx, cy, rx, ry in centers:
        inside = 1 - ((xx - cx) / rx) ** 2 - ((yy - cy) / ry) ** 2
        alpha += np.clip(inside, 0, 1) ** 1.8
    alpha *= np.clip(1.0 - np.maximum(yy * 0.8 + 0.1, 0), 0.2, 1.0)
    leaf = 0.5 + 0.5 * np.sin((xx * 9.7 + yy * 6.2) * math.pi)
    alpha = _normalize(alpha * (0.76 + 0.24 * leaf))
    intensity = 0.38 + 0.40 * alpha
    return _uint8_mask(intensity, alpha)


def _sparkle_mask(shape, points=4):
    xx, yy = _grid(shape)
    rr = np.hypot(xx, yy)
    theta = np.arctan2(yy, xx)
    arm = np.cos(points * theta) ** 2
    alpha = np.clip(1 - rr / 1.05, 0, 1) ** 2.2
    alpha = np.maximum(alpha, np.clip((arm * 1.2 - rr * 0.7), 0, 1))
    intensity = 0.7 + 0.3 * np.clip(alpha + (1 - rr), 0, 1)
    return _uint8_mask(intensity, np.clip(alpha * 1.1, 0, 1))


def _coin_mask(shape, view='front'):
    xx, yy = _grid(shape)
    if view == 'front':
        rr = np.hypot(xx, yy / 0.96)
        alpha = np.clip(1 - (rr - 0.82) / 0.16, 0, 1)
        rim = np.exp(-((rr - 0.78) / 0.07) ** 2)
        emboss = np.exp(-(((xx) / 0.16) ** 2 + ((yy + 0.05) / 0.45) ** 2) * 2.0)
        intensity = 0.45 + 0.4 * rim + 0.15 * emboss
    elif view == 'side':
        rr = np.hypot(xx / 0.42, yy / 0.92)
        alpha = np.clip(1 - (rr - 0.95) / 0.08, 0, 1)
        stripe = 0.6 + 0.4 * np.sin(xx * 16 * math.pi) ** 2
        intensity = (0.42 + 0.45 * stripe) * alpha
    else:
        rr = np.hypot(xx / 0.65, yy / 0.88)
        alpha = np.clip(1 - (rr - 0.88) / 0.12, 0, 1)
        highlight = np.exp(-(((xx + 0.22) / 0.25) ** 2 + ((yy + 0.18) / 0.22) ** 2) * 3.0)
        intensity = (0.48 + 0.28 * (1 - rr) + 0.22 * highlight) * alpha
    return _uint8_mask(intensity, alpha)


def _flame_mask(shape, phase=0):
    xx, yy = _grid(shape)
    yy2 = yy + 0.15
    width = 0.35 + 0.08 * np.sin((yy2 + 1.0) * math.pi * 1.7 + phase * 0.6)
    body = 1 - (np.abs(xx) / np.maximum(width, 1e-3)) ** 1.7 - ((yy2 - 0.15) / 1.05) ** 2
    alpha = np.clip(body, 0, 1) ** 1.8
    tip = np.exp(-(((xx) / 0.18) ** 2 + ((yy + 0.75) / 0.22) ** 2) * 2.5)
    alpha = np.maximum(alpha, tip * 0.75)
    flicker = 0.78 + 0.22 * np.sin((xx * 3.7 + yy * 2.1 + phase * 0.15) * math.pi)
    alpha *= flicker
    intensity = np.clip(0.35 + 0.65 * (1 - np.clip(yy + 0.55, 0, 1)), 0, 1)
    intensity = np.maximum(intensity, 0.92 * tip)
    return _uint8_mask(intensity, np.clip(alpha, 0, 1))


def _smoke_mask(shape, rng, soft=True):
    xx, yy = _grid(shape)
    alpha = np.zeros(shape[0:2], dtype=np.float32)
    count = 7 if soft else 5
    for _ in range(count):
        cx = rng.uniform(-0.7, 0.7)
        cy = rng.uniform(-0.5, 0.7)
        rx = rng.uniform(0.18, 0.46)
        ry = rng.uniform(0.16, 0.42)
        blob = np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2) * 1.8)
        alpha += blob
    alpha = _normalize(alpha)
    if soft:
        alpha *= np.clip(1 - 0.15 * yy, 0.65, 1.0)
    intensity = 0.42 + 0.38 * alpha
    return _uint8_mask(intensity, alpha * (0.75 if soft else 0.95))


def _wave_mask(shape, phase=0):
    xx, yy = _grid(shape)
    rr = np.hypot(xx, yy)
    ring = np.exp(-((rr - (0.38 + 0.09 * phase)) / 0.09) ** 2)
    ring += 0.75 * np.exp(-((rr - (0.70 - 0.05 * phase)) / 0.08) ** 2)
    crest = 0.55 + 0.45 * np.cos(np.arctan2(yy, xx) * 3 + phase * 0.7)
    alpha = _normalize(ring * crest)
    intensity = 0.55 + 0.32 * alpha
    return _uint8_mask(intensity, alpha)


def _swirl_mask(shape, turns=2.5):
    xx, yy = _grid(shape)
    rr = np.hypot(xx / 1.1, yy / 0.92)
    theta = np.arctan2(yy, xx)
    spiral = np.cos(theta * turns - rr * 8.5)
    alpha = np.clip((spiral + 1) * 0.5 - rr * 0.25, 0, 1)
    alpha *= np.clip(1 - (rr - 0.92) / 0.1, 0, 1)
    intensity = 0.38 + 0.45 * alpha
    return _uint8_mask(intensity, alpha)


def _snowflake_mask(shape):
    xx, yy = _grid(shape)
    rr = np.hypot(xx, yy)
    theta = np.arctan2(yy, xx)
    arms = np.cos(theta * 6) ** 10
    alpha = np.clip(arms * (1.05 - rr), 0, 1)
    alpha = np.maximum(alpha, np.exp(-((xx / 0.08) ** 2 + (yy / 0.62) ** 2) * 2.0))
    alpha = np.maximum(alpha, np.exp(-((yy / 0.08) ** 2 + (xx / 0.62) ** 2) * 2.0))
    intensity = 0.72 + 0.28 * alpha
    return _uint8_mask(intensity, alpha)


def _leaf_mask(shape, kind='leafy'):
    xx, yy = _grid(shape)
    alpha = np.zeros(shape[0:2], dtype=np.float32)
    if kind == 'palm':
        for angle in np.linspace(-1.2, 1.2, 7):
            mask = _ellipse(xx, yy, 0, 0.15, 0.12, 0.78, angle)
            alpha = np.maximum(alpha, mask.astype(np.float32))
        stem = _ellipse(xx, yy, 0, 0.55, 0.08, 0.36, 0)
        alpha = np.maximum(alpha, stem.astype(np.float32) * 0.7)
    elif kind == 'pine':
        for i, scale in enumerate([0.72, 0.58, 0.46, 0.34]):
            cy = 0.58 - i * 0.34
            tri = np.clip(1 - np.abs(xx) / scale - np.maximum(yy - cy, 0) / max(scale, 1e-3), 0, 1)
            alpha = np.maximum(alpha, tri)
        trunk = _ellipse(xx, yy, 0, 0.78, 0.10, 0.20, 0)
        alpha = np.maximum(alpha, trunk.astype(np.float32) * 0.45)
    else:
        ellipses = [(-0.38, 0.15, 0.28, 0.52, -0.55), (-0.08, -0.02, 0.26, 0.56, -0.18),
                    (0.24, 0.12, 0.28, 0.54, 0.32), (0.52, 0.26, 0.22, 0.44, 0.60)]
        for cx, cy, rx, ry, ang in ellipses:
            alpha = np.maximum(alpha, _ellipse(xx, yy, cx, cy, rx, ry, ang).astype(np.float32))
    vein = 0.55 + 0.45 * np.cos((xx * 10 + yy * 7) * math.pi) ** 2
    alpha = np.clip(alpha * vein, 0, 1)
    intensity = 0.42 + 0.38 * alpha
    return _uint8_mask(intensity, alpha)


def _cobweb_mask(shape):
    xx, yy = _grid(shape)
    rr = np.hypot(xx, yy)
    theta = np.arctan2(yy, xx)
    spokes = np.cos(theta * 8) ** 18
    rings = np.cos(rr * 18) ** 24
    alpha = np.clip(spokes * 0.9 + rings * 0.45 - rr * 0.45, 0, 1)
    intensity = 0.78 + 0.2 * alpha
    return _uint8_mask(intensity, alpha * 0.9)


def _light_mask(shape):
    xx, yy = _grid(shape)
    rr = np.hypot(xx, yy)
    alpha = np.clip(1 - rr / 1.0, 0, 1) ** 1.8
    halo = np.exp(-((rr - 0.58) / 0.17) ** 2)
    alpha = np.clip(alpha + halo * 0.35, 0, 1)
    intensity = np.clip(0.72 + 0.28 * np.exp(-(rr / 0.42) ** 2), 0, 1)
    return _uint8_mask(intensity, alpha)


def _propeller_mask(shape):
    xx, yy = _grid(shape)
    alpha = np.zeros(shape[0:2], dtype=np.float32)
    for angle in [0.0, 2.0 * math.pi / 3, 4.0 * math.pi / 3]:
        alpha = np.maximum(alpha, _ellipse(xx, yy, 0.0, 0.0, 0.18, 0.72, angle).astype(np.float32))
    hub = _ellipse(xx, yy, 0.0, 0.0, 0.18, 0.18, 0).astype(np.float32)
    alpha = np.maximum(alpha, hub)
    streak = 0.7 + 0.3 * np.sin((xx * 8 - yy * 4) * math.pi) ** 2
    alpha = np.clip(alpha * streak, 0, 1)
    intensity = 0.45 + 0.42 * alpha
    return _uint8_mask(intensity, alpha)


def _ring_mask(shape, side='left'):
    xx, yy = _grid(shape)
    rr = np.hypot(xx / 1.08, yy / 0.82)
    alpha = np.exp(-((rr - 0.68) / 0.12) ** 2)
    if side == 'left':
        alpha *= (xx <= 0.25)
    elif side == 'right':
        alpha *= (xx >= -0.25)
    intensity = 0.52 + 0.34 * alpha
    return _uint8_mask(intensity, alpha)


def _monty_hole_mask(shape):
    xx, yy = _grid(shape)
    rr = np.hypot(xx / 0.9, yy / 0.72)
    alpha = np.clip(1 - (rr - 0.78) / 0.14, 0, 1)
    rim = np.exp(-((rr - 0.72) / 0.08) ** 2)
    intensity = np.clip(0.18 + 0.55 * rim, 0, 1)
    return _uint8_mask(intensity, alpha)


def _cloud_mask(shape):
    xx, yy = _grid(shape)
    alpha = np.zeros(shape[0:2], dtype=np.float32)
    for cx, cy, rx, ry in [(-0.55, 0.12, 0.35, 0.26), (-0.2, -0.05, 0.32, 0.28),
                           (0.15, 0.02, 0.36, 0.30), (0.5, 0.10, 0.30, 0.24)]:
        inside = 1 - ((xx - cx) / rx) ** 2 - ((yy - cy) / ry) ** 2
        alpha += np.clip(inside, 0, 1) ** 1.5
    alpha += np.clip(1 - ((xx / 0.95) ** 2 + ((yy - 0.25) / 0.45) ** 2), 0, 1) * 0.7
    alpha = _normalize(alpha)
    intensity = 0.75 + 0.22 * alpha
    return _uint8_mask(intensity, alpha)


def render_transparency_mask(fname, shape, rng=None, identity=None):
    rng = util_random.ensure_rng(fname) if rng is None else rng
    shape = tuple(shape)
    fname = str(fname)

    if fname.endswith('shadow_quarter_circle.ia8.png'):
        return _soft_shadow(shape, kind='circle')
    if fname.endswith('shadow_quarter_square.ia8.png'):
        return _soft_shadow(shape, kind='square')
    if 'coin_front' in fname:
        return _coin_mask(shape, 'front')
    if 'coin_side' in fname:
        return _coin_mask(shape, 'side')
    if 'coin_tilt' in fname:
        return _coin_mask(shape, 'tilt')
    if 'flame_' in fname:
        phase = int(fname.rsplit('_', 1)[1].split('.', 1)[0])
        return _flame_mask(shape, phase=phase)
    if 'sparkle_animation' in fname:
        frame = int(fname.rsplit('_', 1)[1].split('.', 1)[0])
        return _sparkle_mask(shape, points=4 + (frame % 2))
    if 'impact_ring_left_side' in fname:
        return _ring_mask(shape, 'left')
    if 'impact_ring_right_side' in fname:
        return _ring_mask(shape, 'right')
    if 'impact_smoke_' in fname or 'stomp_smoke_' in fname or 'walk_smoke_' in fname:
        return _smoke_mask(shape, rng, soft=False)
    if fname.endswith('burn_smoke.ia16.png') or fname.endswith('mist.ia16.png') or fname.endswith('smoke.ia16.png'):
        return _smoke_mask(shape, rng, soft=True)
    if 'water_wave_' in fname:
        frame = int(fname.rsplit('_', 1)[1].split('.', 1)[0])
        return _wave_mask(shape, phase=frame / 6.0)
    if fname.endswith('whirlpool.ia16.png') or fname.endswith('tornado.ia16.png'):
        return _swirl_mask(shape)
    if fname.endswith('flyguy_propeller.ia16.png'):
        return _propeller_mask(shape)
    if fname.endswith('castle_light.ia16.png'):
        return _light_mask(shape)
    if fname.endswith('monty_mole_hole.ia16.png'):
        return _monty_hole_mask(shape)
    if 'fwoosh_face' in fname:
        return _cloud_mask(shape)

    # Environment and bank-specific masks.
    if fname in {'levels/wf/5.ia8.png', 'textures/grass/wf_textures.0B000.ia16.png'}:
        return _fence_mask(shape, style='chain')
    if fname in {'levels/castle_grounds/5.ia8.png', 'textures/outside/castle_grounds_textures.0BC00.ia16.png'}:
        return _fence_mask(shape, style='iron')
    if fname in {'textures/grass/wf_textures.0B800.ia16.png', 'textures/generic/bob_textures.0B000.ia16.png'}:
        return _hedge_mask(shape)
    if fname in {'levels/ssl/1.ia16.png'}:
        return _leaf_mask(shape, kind='palm')
    if fname in {'levels/ccm/8.ia16.png', 'textures/snow/ccm_textures.09000.ia16.png'}:
        return _snowflake_mask(shape)
    if fname in {'levels/ccm/9.ia16.png', 'textures/snow/ccm_textures.09800.ia16.png'}:
        return _leaf_mask(shape, kind='pine')
    if fname in {'levels/totwc/3.ia16.png', 'levels/ttm/0.ia16.png', 'levels/pss/1.ia16.png'}:
        return _cloud_mask(shape)
    if fname in {'levels/castle_inside/2.ia16.png', 'levels/castle_inside/16.ia16.png'}:
        return _fence_mask(shape, style='iron')
    if fname in {'textures/spooky/bbh_textures.0A800.ia16.png', 'textures/spooky/bbh_textures.0B000.ia16.png'}:
        return _cobweb_mask(shape)
    if fname in {'textures/spooky/bbh_textures.0B800.ia16.png'}:
        return _fence_mask(shape, style='iron')
    if fname in {'textures/cave/hmc_textures.0B800.ia16.png'}:
        return _leaf_mask(shape, kind='leafy')
    if fname in {'textures/cave/hmc_textures.0C000.ia16.png'}:
        return _sparkle_mask(shape, points=6)
    if fname in {'levels/lll/27.ia16.png'}:
        return _sparkle_mask(shape, points=5)

    # Broad actor fallback.
    if fname.startswith('actors/'):
        return _sparkle_mask(shape, points=4)
    # Broad environment fallback for remaining 2-channel masks.
    return _hedge_mask(shape)
