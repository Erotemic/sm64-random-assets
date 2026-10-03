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



def test_steamrt_dockerfile_preserves_sdk_sdl_stack():
    dockerfile = (
        REPO_DPATH / "dockerfiles" / "steamrt_sm64_random_assets.Dockerfile"
    ).read_text()
    install_block = dockerfile.split("COPY requirements/runtime.txt", 1)[0]
    assert "libsdl2-compat-dev" in install_block
    # Installing Bullseye's classic libsdl2-dev into current Steam Runtime
    # ARM64 SDK images conflicts with the SDK-provided sdl2-compat shim.
    active_lines = [
        line.strip()
        for line in install_block.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert not any(line == "libsdl2-dev \\" for line in active_lines)
    assert "command -v sdl2-config" in install_block

def test_steamrt_dockerfile_pins_eol_bullseye_security_snapshot():
    dockerfile = (
        REPO_DPATH / "dockerfiles" / "steamrt_sm64_random_assets.Dockerfile"
    ).read_text()
    assert "ARG DEBIAN_SECURITY_SNAPSHOT=20260903T220410Z" in dockerfile
    assert "snapshot.debian.org/archive" in dockerfile
    assert "debian-security/$DEBIAN_SECURITY_SNAPSHOT" in dockerfile
    assert 'Acquire::Check-Valid-Until "false";' in dockerfile
    # The source rewrite must happen before apt reads package indexes.
    assert dockerfile.index("snapshot_base=") < dockerfile.index("apt-get update")


def test_steamrt_helper_passes_security_snapshot_build_arg():
    helper = (REPO_DPATH / "dev" / "build_steamrt_target.sh").read_text()
    assert (
        "DEBIAN_SECURITY_SNAPSHOT=${STEAMRT_DEBIAN_SECURITY_SNAPSHOT:-20260903T220410Z}"
        in helper
    )
    assert '--build-arg "DEBIAN_SECURITY_SNAPSHOT=$DEBIAN_SECURITY_SNAPSHOT"' in helper


def test_steamrt_dockerfile_uses_uv_managed_modern_python():
    dockerfile = (
        REPO_DPATH / "dockerfiles" / "steamrt_sm64_random_assets.Dockerfile"
    ).read_text()
    assert "ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.12.22" in dockerfile
    assert "COPY --from=uv /uv /uvx /bin/" in dockerfile
    assert "ARG PYTHON_VERSION=3.12" in dockerfile
    assert 'uv python install "$PYTHON_VERSION"' in dockerfile
    assert 'uv venv --python "$PYTHON_VERSION" /opt/sm64ra-venv' in dockerfile
    assert "python3 -m venv /opt/sm64ra-venv" not in dockerfile

    apt_block = dockerfile.split("COPY requirements/runtime.txt", 1)[0]
    active_lines = [
        line.strip()
        for line in apt_block.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert not any(line == "python3 \\" for line in active_lines)
    assert not any(line == "python3-pip \\" for line in active_lines)
    assert not any(line == "python3-venv; \\" for line in active_lines)


def test_steamrt_helper_passes_managed_python_version():
    helper = (REPO_DPATH / "dev" / "build_steamrt_target.sh").read_text()
    assert "STEAMRT_PYTHON_VERSION=${STEAMRT_PYTHON_VERSION:-3.12}" in helper
    assert '--build-arg "PYTHON_VERSION=$STEAMRT_PYTHON_VERSION"' in helper


def test_build_script_uses_explicit_python_interpreter():
    build_script = (REPO_DPATH / "build.sh").read_text()
    assert "SM64RA_PYTHON=${SM64RA_PYTHON:-python3}" in build_script
    assert '"$SM64RA_PYTHON" -m sm64_random_assets generate' in build_script
    assert 'PYTHON="$SM64RA_PYTHON"' in build_script
    assert "python3 -m sm64_random_assets generate" not in build_script


def test_steamrt_image_exports_managed_python_explicitly():
    dockerfile = (
        REPO_DPATH / "dockerfiles" / "steamrt_sm64_random_assets.Dockerfile"
    ).read_text()
    assert "ENV SM64RA_PYTHON=/opt/sm64ra-venv/bin/python" in dockerfile


def test_steamrt_helper_does_not_start_login_shell():
    helper = (REPO_DPATH / "dev" / "build_steamrt_target.sh").read_text()
    assert "bash -c 'mkdir -p" in helper
    assert "bash -lc 'mkdir -p" not in helper
