from __future__ import annotations

from sm64_random_assets.realizations import AssetIdentity


def determine_asset_identity(info_or_fname, *, name_to_text_lut=None) -> AssetIdentity:
    """Incrementally classifies assets into semantic families."""
    if isinstance(info_or_fname, dict):
        fname = str(info_or_fname['fname'])
    else:
        fname = str(info_or_fname)

    if fname.startswith('actors/power_meter/power_meter_'):
        member = fname.rsplit('power_meter_', 1)[1].split('.', 1)[0]
        return AssetIdentity(fname=fname, family='hud.power_meter', member=member)

    if fname in (name_to_text_lut or {}):
        if fname.startswith('textures/ipl3_raw/'):
            family = 'glyph.ipl3'
        elif fname.startswith('textures/segment2/font_graphics.'):
            family = 'glyph.font_graphics'
        elif fname.startswith('textures/segment2/segment2.'):
            family = 'glyph.segment2'
        elif fname.startswith('levels/menu/main_menu_seg7_us.'):
            family = 'glyph.main_menu'
        elif fname.startswith('levels/castle_grounds/'):
            family = 'glyph.signage'
        else:
            family = 'glyph.misc'
        return AssetIdentity(fname=fname, family=family, member=fname.rsplit('/', 1)[-1])

    if 'goomba_face_blink' in fname:
        return AssetIdentity(fname=fname, family='actor.goomba.face', member='blink')
    if 'goomba_face' in fname:
        return AssetIdentity(fname=fname, family='actor.goomba.face', member='open')

    eye_tokens = [
        'eyes_center', 'eyes_closed', 'eyes_dead',
        'eye_mostly_open', 'iris_mostly_open',
        'eye_mostly_closed', 'iris_mostly_closed',
        'eye_closed', 'iris_closed', 'eye_angry', 'eye_half_closed',
    ]
    for token in eye_tokens:
        if token in fname:
            return AssetIdentity(fname=fname, family='face.generic_eyes', member=token)
    if 'mips_eyes' in fname:
        return AssetIdentity(fname=fname, family='face.generic_eyes', member='mips')

    return AssetIdentity(fname=fname, family=fname, member='default')


__all__ = ['determine_asset_identity']
