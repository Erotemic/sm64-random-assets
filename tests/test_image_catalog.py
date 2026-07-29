from sm64_random_assets.image_catalog import determine_asset_identity


def test_power_meter_identity_groups_family_members():
    a = determine_asset_identity('actors/power_meter/power_meter_full.rgba16.png')
    b = determine_asset_identity('actors/power_meter/power_meter_two_segments.rgba16.png')
    assert a.family == b.family == 'hud.power_meter'
    assert a.member == 'full'
    assert b.member == 'two_segments'


def test_unknown_assets_remain_asset_scoped():
    a = determine_asset_identity('textures/misc/example.rgba16.png')
    assert a.family == 'textures/misc/example.rgba16.png'
    assert a.member == 'default'


def test_mario_eye_variants_are_a_coherent_family():
    center = determine_asset_identity('actors/mario/mario_eyes_center.rgba16.png')
    closed = determine_asset_identity('actors/mario/mario_eyes_closed.rgba16.png')
    assert center.family == closed.family == 'actor.mario.eyes'
    assert center.member == 'center'
    assert closed.member == 'closed'


def test_bowser_peach_eye_and_fakeout_families_are_separate():
    peach_fakeout = determine_asset_identity('levels/castle_inside/5.rgba16.png')
    bowser_fakeout = determine_asset_identity('levels/castle_inside/6.rgba16.png')
    bowser_eye = determine_asset_identity('actors/bowser/bowser_eye_left_0.rgba16.png')
    peach_eye = determine_asset_identity('actors/peach/peach_eye_open.rgba16.png')
    assert peach_fakeout.family == bowser_fakeout.family == 'castle.fakeout_portrait'
    assert bowser_eye.family == 'actor.bowser.eyes'
    assert peach_eye.family == 'actor.peach.eyes'


def test_differentiated_actor_and_animation_identities_are_grouped_coherently():
    koopa_eye = determine_asset_identity('actors/koopa/koopa_eyes_open.rgba16.png')
    koopa_shell = determine_asset_identity('actors/koopa/koopa_shell_back.rgba16.png')
    explosion0 = determine_asset_identity('actors/explosion/explosion_0.rgba16.png')
    explosion6 = determine_asset_identity('actors/explosion/explosion_6.rgba16.png')
    assert koopa_eye.family == 'actor.koopa'
    assert koopa_shell.family == 'actor.koopa'
    assert koopa_eye.member != koopa_shell.member
    assert explosion0.family == 'animation.explosion'
    assert explosion6.family == 'animation.explosion'
    assert explosion0.member != explosion6.member
