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

    if fname.startswith('actors/mario/mario_eyes_'):
        member = fname.rsplit('mario_eyes_', 1)[1].split('.', 1)[0]
        return AssetIdentity(fname=fname, family='actor.mario.eyes', member=member)

    if fname in {
        'levels/castle_inside/5.rgba16.png',
        'levels/castle_inside/6.rgba16.png',
    }:
        member = 'peach' if '/5.' in fname else 'bowser'
        return AssetIdentity(fname=fname, family='castle.fakeout_portrait', member=member)

    if fname.startswith('actors/bowser/bowser_eye'):
        member = fname.rsplit('bowser_eye', 1)[1].split('.', 1)[0].lstrip('_') or 'default'
        return AssetIdentity(fname=fname, family='actor.bowser.eyes', member=member)

    if fname.startswith('actors/peach/peach_eye'):
        member = fname.rsplit('peach_eye_', 1)[1].split('.', 1)[0]
        return AssetIdentity(fname=fname, family='actor.peach.eyes', member=member)

    if 'goomba_face_blink' in fname:
        return AssetIdentity(fname=fname, family='actor.goomba.face', member='blink')
    if 'goomba_face' in fname:
        return AssetIdentity(fname=fname, family='actor.goomba.face', member='open')


    differentiated_actor_families = {
        'amp', 'bobomb', 'bookend', 'bully', 'chain_chomp', 'chillychief',
        'dorrie', 'eyerok', 'flyguy', 'haunted_cage', 'heave_ho',
        'king_bobomb', 'klepto', 'koopa', 'lakitu_cameraman', 'lakitu_enemy',
        'mad_piano', 'monty_mole', 'penguin', 'piranha_plant', 'scuttlebug',
        'seaweed', 'snowman', 'spindrift', 'treasure_chest', 'ukiki', 'unagi',
        'whomp', 'wiggler', 'yoshi',
    }
    differentiated_animation_families = {
        'explosion', 'flame', 'impact_smoke', 'stomp_smoke', 'walk_smoke',
        'water_wave', 'yoshi_egg',
    }
    if fname.startswith('actors/'):
        parts = fname.split('/', 2)
        if len(parts) == 3:
            actor_family = parts[1]
            if actor_family in differentiated_actor_families:
                member = parts[2].split('.', 1)[0]
                return AssetIdentity(fname=fname, family=f'actor.{actor_family}', member=member)
            if actor_family in differentiated_animation_families:
                member = parts[2].split('.', 1)[0]
                return AssetIdentity(fname=fname, family=f'animation.{actor_family}', member=member)

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
