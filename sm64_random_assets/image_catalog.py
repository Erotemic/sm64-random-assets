from __future__ import annotations

from sm64_random_assets.realizations import AssetIdentity


_CASTLE_INSIDE_MATERIAL_MEMBERS = {
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


def determine_asset_identity(info_or_fname, *, name_to_text_lut=None) -> AssetIdentity:
    """Incrementally classifies assets into semantic families."""
    if isinstance(info_or_fname, dict):
        fname = str(info_or_fname['fname'])
    else:
        fname = str(info_or_fname)

    file_select_members = {
        'levels/menu/main_menu_seg7.00018.rgba16.png': 'backdrop_deep',
        'levels/menu/main_menu_seg7.00818.rgba16.png': 'backdrop_light',
        'levels/menu/main_menu_seg7.01018.rgba16.png': 'save_slot_occupied',
        'levels/menu/main_menu_seg7.02018.rgba16.png': 'save_slot_empty',
        'levels/menu/main_menu_seg7.03468.rgba16.png': 'action_score',
        'levels/menu/main_menu_seg7.03C68.rgba16.png': 'action_copy',
        'levels/menu/main_menu_seg7.04468.rgba16.png': 'action_erase',
        'levels/menu/main_menu_seg7.04C68.rgba16.png': 'action_sound',
        'levels/menu/main_menu_seg7.05468.rgba16.png': 'action_auxiliary',
        'levels/menu/main_menu_seg7.0D1A8.rgba16.png': 'backdrop_upper',
        'levels/menu/main_menu_seg7.0E1A8.rgba16.png': 'backdrop_lower',
    }
    if fname in file_select_members:
        return AssetIdentity(
            fname=fname, family='menu.file_select', member=file_select_members[fname])

    if fname in {
        'levels/menu/main_menu_seg7.06328.rgba16.png',
        'levels/menu/main_menu_seg7.06B28.rgba16.png',
    }:
        member = 'open' if '.06328.' in fname else 'pressed'
        return AssetIdentity(fname=fname, family='menu.pointer', member=member)

    if fname.startswith('textures/title_screen_bg/title_screen_bg.'):
        member = fname.split('.')[-3]
        return AssetIdentity(fname=fname, family='intro.title_background', member=member)

    if fname in {
        'levels/intro/0.rgba16.png',
        'levels/intro/1.rgba16.png',
    }:
        member = fname.rsplit('/', 1)[1].split('.', 1)[0]
        return AssetIdentity(fname=fname, family='intro.logo_material', member=member)

    if fname.startswith('textures/intro_raw/red_star_'):
        member = fname.rsplit('red_star_', 1)[1].split('.', 1)[0]
        return AssetIdentity(fname=fname, family='intro.red_star', member=member)

    if fname.startswith('textures/intro_raw/white_star_'):
        member = fname.rsplit('white_star_', 1)[1].split('.', 1)[0]
        return AssetIdentity(fname=fname, family='intro.white_star', member=member)

    if fname.startswith('textures/intro_raw/sparkle_'):
        member = fname.rsplit('sparkle_', 1)[1].split('.', 1)[0]
        return AssetIdentity(fname=fname, family='intro.sparkle', member=member)

    if fname in {
        'textures/intro_raw/hand_open.rgba16.png',
        'textures/intro_raw/hand_closed.rgba16.png',
    }:
        member = 'open' if 'hand_open' in fname else 'closed'
        return AssetIdentity(fname=fname, family='intro.glove', member=member)

    if fname == 'textures/intro_raw/mario_face_shine.ia8.png':
        return AssetIdentity(fname=fname, family='intro.face_shine', member='default')

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

    if fname in _CASTLE_INSIDE_MATERIAL_MEMBERS:
        return AssetIdentity(
            fname=fname, family='castle.interior.material', member=_CASTLE_INSIDE_MATERIAL_MEMBERS[fname])

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
