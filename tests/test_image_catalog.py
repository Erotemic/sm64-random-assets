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


def test_castle_inside_materials_share_family_but_keep_member_specificity():
    a = determine_asset_identity('levels/castle_inside/3.rgba16.png')
    b = determine_asset_identity('levels/castle_inside/14.rgba16.png')
    assert a.family == b.family == 'castle.interior.material'
    assert a.member == 'checker_marble_floor'
    assert b.member == 'star_medallion_tile'
