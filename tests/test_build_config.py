import os
import pathlib
import subprocess


REPO_DPATH = pathlib.Path(__file__).parents[1]
CONFIG_FPATH = REPO_DPATH / "dev" / "build_config.sh"


def resolve_config(**env_updates):
    env = os.environ.copy()
    for key in ["PRESET", "VARIANT", "TARGET"]:
        env.pop(key, None)
    env.update(env_updates)
    command = f'''
        source {CONFIG_FPATH!s}
        sm64ra_resolve_build_config || exit $?
        printf '%s\\t%s\\t%s\\n' "${{PRESET:-}}" "$VARIANT" "$TARGET"
    '''
    return subprocess.run(
        ["bash", "-c", command],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_default_build_config():
    result = resolve_config()
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "sm64-port\thost"


def test_steamframe_preset():
    result = resolve_config(PRESET="steamframe")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "steamframe\tsm64-port\tsteamrt3-aarch64"


def test_steamframe_allows_variant_override():
    result = resolve_config(PRESET="steamframe", VARIANT="sm64ex")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "steamframe\tsm64ex\tsteamrt3-aarch64"


def test_steamdeck_preset():
    result = resolve_config(PRESET="steamdeck")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "steamdeck\tsm64-port\tsteamrt3-x86_64"


def test_n64_preset():
    result = resolve_config(PRESET="n64")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "n64\tsm64\tn64"


def test_legacy_pc_target_is_translated():
    result = resolve_config(TARGET="pc")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "sm64-port\thost"
    assert "legacy syntax" in result.stderr


def test_legacy_variant_target_is_translated():
    result = resolve_config(TARGET="sm64ex")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "sm64ex\thost"
    assert "legacy syntax" in result.stderr


def test_preset_owns_target_selection():
    result = resolve_config(PRESET="steamframe", TARGET="steamrt3-x86_64")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "steamframe\tsm64-port\tsteamrt3-aarch64"


def test_n64_target_rejects_pc_variant():
    result = resolve_config(VARIANT="sm64-port", TARGET="n64")
    assert result.returncode != 0
    assert "requires VARIANT=sm64" in result.stderr


def test_variant_metadata_sm64ex_path_has_directory_separator():
    command = f'''
        source {CONFIG_FPATH!s}
        sm64ra_variant_binary_relpath sm64ex
    '''
    result = subprocess.run(
        ["bash", "-c", command], text=True, capture_output=True, check=True
    )
    assert result.stdout.strip() == "build/us_pc/sm64.us.f3dex2e"
