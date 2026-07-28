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
