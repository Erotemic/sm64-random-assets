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


def test_steamframe_preset_prefers_sm64ex():
    result = resolve_config(PRESET="steamframe")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "steamframe\tsm64ex\tsteamrt3-aarch64"


def test_steamframe_allows_variant_override():
    result = resolve_config(PRESET="steamframe", VARIANT="sm64-port")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "steamframe\tsm64-port\tsteamrt3-aarch64"


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
    assert result.stdout.strip() == "steamframe\tsm64ex\tsteamrt3-aarch64"


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

def test_steamrt_dockerfile_installs_sm64ex_hexdump_dependency():
    dockerfile = (
        REPO_DPATH / "dockerfiles" / "steamrt_sm64_random_assets.Dockerfile"
    ).read_text()
    assert "bsdextrautils" in dockerfile


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


def resolve_asset_config(**env_updates):
    env = os.environ.copy()
    for key in ["ASSET_MODE", "BASEROM_FPATH", "EXTERNAL_ROM_FPATH"]:
        env.pop(key, None)
    env.update(env_updates)
    command = f'''
        source {CONFIG_FPATH!s}
        sm64ra_resolve_asset_config || exit $?
        printf '%s\t%s\n' "$ASSET_MODE" "${{BASEROM_FPATH:-}}"
    '''
    return subprocess.run(
        ["bash", "-c", command],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_asset_mode_defaults_to_generate():
    result = resolve_asset_config()
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "generate"


def test_asset_mode_reuse_aliases():
    for alias in ["reuse", "existing", "skip"]:
        result = resolve_asset_config(ASSET_MODE=alias)
        assert result.returncode == 0, result.stderr
        assert result.stdout.split("\t", 1)[0].strip() == "reuse"


def test_asset_mode_rejects_unknown_value():
    result = resolve_asset_config(ASSET_MODE="magic")
    assert result.returncode != 0
    assert "Expected generate, reuse, or baserom" in result.stderr


def test_external_rom_path_preserves_legacy_generate_default(tmp_path):
    rom = tmp_path / "baserom.us.z64"
    result = resolve_asset_config(EXTERNAL_ROM_FPATH=str(rom))
    assert result.returncode == 0, result.stderr
    mode, _, path = result.stdout.rstrip("\n").partition("\t")
    assert mode == "generate"
    assert path == ""


def test_explicit_baserom_path_implies_baserom_mode(tmp_path):
    rom = tmp_path / "baserom.us.z64"
    result = resolve_asset_config(BASEROM_FPATH=str(rom))
    assert result.returncode == 0, result.stderr
    mode, path = result.stdout.strip().split("\t")
    assert mode == "baserom"
    assert path == str(rom)


def test_build_script_resolves_asset_mode_after_baserom_input_initialization():
    build_script = (REPO_DPATH / "build.sh").read_text()
    baserom_init = build_script.index('BASEROM_FPATH=${BASEROM_FPATH:=""}')
    resolve = build_script.index('sm64ra_resolve_asset_config')
    generator = build_script.index('"$SM64RA_PYTHON" -m sm64_random_assets generate')
    assert baserom_init < resolve < generator


def test_baserom_path_cannot_fall_through_to_generator(tmp_path):
    rom = tmp_path / "baserom.us.z64"
    result = resolve_asset_config(BASEROM_FPATH=str(rom), ASSET_MODE="generate")
    assert result.returncode != 0
    assert "BASEROM_FPATH selects ASSET_MODE=baserom" in result.stderr


def test_baserom_path_cannot_be_combined_with_reuse(tmp_path):
    rom = tmp_path / "baserom.us.z64"
    result = resolve_asset_config(BASEROM_FPATH=str(rom), ASSET_MODE="reuse")
    assert result.returncode != 0
    assert "BASEROM_FPATH selects ASSET_MODE=baserom" in result.stderr


def test_conflicting_baserom_aliases_are_rejected(tmp_path):
    result = resolve_asset_config(
        BASEROM_FPATH=str(tmp_path / "one.z64"),
        EXTERNAL_ROM_FPATH=str(tmp_path / "two.z64"),
    )
    assert result.returncode != 0
    assert "different files" in result.stderr


def test_build_script_has_explicit_asset_modes_and_cache_preservation():
    build_script = (REPO_DPATH / "build.sh").read_text()
    assert 'if [[ "$ASSET_MODE" == "generate" ]]' in build_script
    assert '"$SM64RA_PYTHON" -m sm64_random_assets generate' in build_script
    assert "Skipping asset generation/extraction" in build_script
    assert "Skipping the random asset generator" in build_script
    # An explicit baserom is guarded immediately next to the generator branch.
    assert 'BASEROM_FPATH is set but ASSET_MODE=' in build_script
    assert 'generator branch reached with BASEROM_FPATH set' in build_script
    # Baseline assets live in their own persistent checkout: no destructive
    # extract_assets --clean when switching provenance.
    assert 'BASEROM_REPO_DPATH="${VARIANT_REPO_DPATH}-baserom"' in build_script
    assert 'extract_assets.py --clean' not in build_script
    assert '"$SM64RA_PYTHON" extract_assets.py us' in build_script
    assert '.assets-local.txt' in build_script
    assert 'extract_assets.py --clean' not in build_script
    # Native helper cleanup is conditional on an ISA mismatch.
    assert "Cleaning native SM64 helper tools for target environment" in build_script
    assert 'make -s -C "$tools_dpath" clean' in build_script
    assert 'host_arch=$(sm64ra_host_arch)' in build_script
    assert 'NOEXTRACT=1' in build_script
    assert 'SM64RA_MAKE_ARGS' in build_script


def test_steamframe_sm64ex_uses_explicit_sdl2_arm_build_flags():
    build_script = (REPO_DPATH / "build.sh").read_text()
    assert '"$VARIANT" == "sm64ex" && "$TARGET" == "steamrt3-aarch64"' in build_script
    assert "TARGET_ARCH=armv8-a" in build_script
    assert "RENDER_API=GL" in build_script
    assert "WINDOW_API=SDL2" in build_script
    assert "AUDIO_API=SDL2" in build_script
    assert "CONTROLLER_API=SDL2" in build_script


def test_build_script_preserves_original_presentation_and_control_flow():
    build_script = (REPO_DPATH / "build.sh").read_text()
    assert "____ _  _  _   _ _    ____ ____ _  _ ___" in build_script
    assert r"[__  |\/|  |_  |_|" in build_script
    assert "Run Asset Generator" in build_script
    assert "Compile the ROM" in build_script
    assert "Finalize" in build_script
    assert "ub.color_text" in build_script
    assert "ub.highlight_code" in build_script
    assert 'NUM_CPUS=${NUM_CPUS:=}' in build_script
    assert 'if [[ ${BASH_SOURCE[0]} == "$0" ]]' in build_script
    assert 'echo "To execute locally use: "' in build_script


def test_steamrt_helper_forwards_asset_mode_and_baserom_fail_closed():
    helper = (REPO_DPATH / "dev" / "build_steamrt_target.sh").read_text()
    assert 'sm64ra_resolve_asset_config' in helper
    assert '--env "ASSET_MODE=$ASSET_MODE"' in helper
    assert 'BASEROM_ABS=$(realpath -e -- "$BASEROM_FPATH"' in helper
    assert 'SM64RA_EXPECT_BASEROM=1' in helper
    assert '--env "SM64RA_EXPECT_BASEROM=$SM64RA_EXPECT_BASEROM"' in helper
    assert 'CONTAINER_BASEROM_FPATH="/work/$BASEROM_REL"' in helper
    assert 'CONTAINER_BASEROM_FPATH=/inputs/baserom.us.z64' in helper
    assert '--env "BASEROM_FPATH=$CONTAINER_BASEROM_FPATH"' in helper
    assert '--env EXTERNAL_ROM_FPATH=/inputs/baserom.us.z64' not in helper

    # Resolve/validate the host file before paying the Docker image-build cost.
    assert helper.index('BASEROM_ABS=$(realpath -e -- "$BASEROM_FPATH"') < helper.index('docker buildx build')


def test_inner_build_refuses_to_fall_back_if_baserom_handoff_is_lost():
    build_script = (REPO_DPATH / "build.sh").read_text()
    marker_guard = build_script.index('if [[ "$SM64RA_EXPECT_BASEROM" == "1" ]]')
    resolve = build_script.index('sm64ra_resolve_asset_config')
    generator = build_script.index('"$SM64RA_PYTHON" -m sm64_random_assets generate')
    assert marker_guard < resolve < generator
    assert 'expected a baserom, but BASEROM_FPATH was not forwarded' in build_script
    assert 'expected a mounted baserom, but it is not visible' in build_script


def test_baserom_examples_are_executable_relative_paths():
    readme = (REPO_DPATH / "README.rst").read_text()
    frame_docs = (REPO_DPATH / "docs/source/manual/install_docs/install_on_steamframe.rst").read_text()
    assert "BASEROM_FPATH=baserom.us.z64" in readme
    assert "BASEROM_FPATH=baserom.us.z64" in frame_docs
    assert "BASEROM_FPATH=/path/to" not in readme
    assert "BASEROM_FPATH=/path/to" not in frame_docs


def test_baserom_checkout_is_ignored_by_superproject():
    gitignore = (REPO_DPATH / ".gitignore").read_text()
    assert "tpl/*-baserom" in gitignore


def test_steamrt_relative_baserom_maps_into_work_mount(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    docker_log = tmp_path / "docker.log"
    docker = fake_bin / "docker"
    docker.write_text(
        """#!/usr/bin/env bash
set -eu
printf '<%s>' \"$@\" >> \"$FAKE_DOCKER_LOG\"
printf '\\n' >> \"$FAKE_DOCKER_LOG\"
if [[ \"${1:-} ${2:-}\" == \"buildx version\" ]]; then
    exit 0
elif [[ \"${1:-} ${2:-}\" == \"buildx inspect\" ]]; then
    echo 'Platforms: linux/amd64, linux/arm64'
    exit 0
elif [[ \"${1:-} ${2:-}\" == \"buildx build\" ]]; then
    exit 0
elif [[ \"${1:-}\" == \"run\" ]]; then
    exit 0
fi
exit 0
"""
    )
    docker.chmod(0o755)

    rom = REPO_DPATH / "baserom.us.z64"
    try:
        rom.write_bytes(b"test-rom")
        env = os.environ.copy()
        env.update(
            {
                "PATH": f"{fake_bin}:{env['PATH']}",
                "FAKE_DOCKER_LOG": str(docker_log),
                "PRESET": "steamframe",
                "BASEROM_FPATH": "baserom.us.z64",
            }
        )
        for key in ["VARIANT", "TARGET", "ASSET_MODE", "EXTERNAL_ROM_FPATH"]:
            env.pop(key, None)
        result = subprocess.run(
            ["bash", "dev/build_steamrt_target.sh"],
            cwd=REPO_DPATH,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "ASSET_MODE=baserom" in result.stdout
        assert f"BASEROM_HOST_FPATH={rom}" in result.stdout
        assert "BASEROM_CONTAINER_FPATH=/work/baserom.us.z64" in result.stdout
        log = docker_log.read_text()
        assert "<ASSET_MODE=baserom>" in log
        assert "<SM64RA_EXPECT_BASEROM=1>" in log
        assert "<BASEROM_FPATH=/work/baserom.us.z64>" in log
        # A repo-local baserom is already visible through the /work bind mount;
        # don't make a redundant /inputs mount.
        assert "dst=/inputs/baserom.us.z64" not in log
    finally:
        rom.unlink(missing_ok=True)


def test_steamrt_missing_explicit_baserom_fails_before_docker_build(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    docker_log = tmp_path / "docker.log"
    docker = fake_bin / "docker"
    docker.write_text(
        """#!/usr/bin/env bash
printf '<%s>' \"$@\" >> \"$FAKE_DOCKER_LOG\"
printf '\\n' >> \"$FAKE_DOCKER_LOG\"
exit 0
"""
    )
    docker.chmod(0o755)
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{fake_bin}:{env['PATH']}",
            "FAKE_DOCKER_LOG": str(docker_log),
            "PRESET": "steamframe",
            "BASEROM_FPATH": "baserom.us.z64",
        }
    )
    for key in ["VARIANT", "TARGET", "ASSET_MODE", "EXTERNAL_ROM_FPATH"]:
        env.pop(key, None)
    result = subprocess.run(
        ["bash", "dev/build_steamrt_target.sh"],
        cwd=REPO_DPATH,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "BASEROM_FPATH does not exist: baserom.us.z64" in result.stderr
    assert not docker_log.exists() or "buildx build" not in docker_log.read_text()
