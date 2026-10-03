#!/usr/bin/env bash
# Shared build configuration for build.sh and target-container helpers.

sm64ra_warn() {
    printf 'WARNING: %s\n' "$*" >&2
}

sm64ra_die() {
    printf 'ERROR: %s\n' "$*" >&2
    return 1
}

sm64ra_normalize_arch() {
    case "$1" in
        x86_64|amd64) printf '%s\n' x86_64 ;;
        aarch64|arm64) printf '%s\n' aarch64 ;;
        *) return 1 ;;
    esac
}

sm64ra_host_arch() {
    local arch
    arch=$(uname -m)
    sm64ra_normalize_arch "$arch" || {
        printf '%s\n' "$arch"
    }
}

sm64ra_target_arch() {
    case "$1" in
        steamrt3-x86_64) printf '%s\n' x86_64 ;;
        steamrt3-aarch64) printf '%s\n' aarch64 ;;
        host) sm64ra_host_arch ;;
        n64) printf '%s\n' mips ;;
        *) return 1 ;;
    esac
}

sm64ra_canonical_variant() {
    case "$1" in
        sm64) printf '%s\n' sm64 ;;
        sm64-port|pc) printf '%s\n' sm64-port ;;
        sm64ex) printf '%s\n' sm64ex ;;
        Render96ex|render96ex) printf '%s\n' Render96ex ;;
        SM64CoopDX|sm64coopdx) printf '%s\n' SM64CoopDX ;;
        *) return 1 ;;
    esac
}

sm64ra_variant_repo_relpath() {
    case "$1" in
        sm64) printf '%s\n' tpl/sm64 ;;
        sm64-port) printf '%s\n' tpl/sm64-port ;;
        sm64ex) printf '%s\n' tpl/sm64ex ;;
        Render96ex) printf '%s\n' tpl/Render96ex ;;
        SM64CoopDX) printf '%s\n' tpl/sm64coopdx ;;
        *) return 1 ;;
    esac
}

sm64ra_variant_binary_relpath() {
    case "$1" in
        sm64) printf '%s\n' build/us/sm64.us.z64 ;;
        sm64-port) printf '%s\n' build/us_pc/sm64.us ;;
        sm64ex|Render96ex) printf '%s\n' build/us_pc/sm64.us.f3dex2e ;;
        SM64CoopDX) printf '%s\n' build/us_pc/sm64.us ;;
        *) return 1 ;;
    esac
}

sm64ra_variant_binary_type() {
    case "$1" in
        sm64) printf '%s\n' ROM ;;
        sm64-port|sm64ex|Render96ex|SM64CoopDX) printf '%s\n' executable ;;
        *) return 1 ;;
    esac
}

sm64ra_legacy_target_to_variant() {
    case "$1" in
        rom|sm64) printf '%s\t%s\n' sm64 n64 ;;
        pc|sm64-port) printf '%s\t%s\n' sm64-port host ;;
        sm64ex) printf '%s\t%s\n' sm64ex host ;;
        Render96ex|render96ex) printf '%s\t%s\n' Render96ex host ;;
        SM64CoopDX|sm64coopdx) printf '%s\t%s\n' SM64CoopDX host ;;
        *) return 1 ;;
    esac
}

sm64ra_apply_preset() {
    case "${PRESET:-}" in
        '') ;;
        host)
            TARGET=host
            ;;
        n64)
            if [[ -n ${VARIANT:-} && ${VARIANT} != sm64 ]]; then
                sm64ra_die "PRESET=n64 requires VARIANT=sm64, not VARIANT=$VARIANT"
                return 1
            fi
            VARIANT=sm64
            TARGET=n64
            ;;
        steamdeck)
            TARGET=steamrt3-x86_64
            ;;
        steamframe)
            TARGET=steamrt3-aarch64
            ;;
        *)
            sm64ra_die "Unknown PRESET=${PRESET}. Expected host, n64, steamdeck, or steamframe."
            return 1
            ;;
    esac
}

sm64ra_resolve_build_config() {
    local legacy_pair legacy_variant legacy_target canonical_variant

    # Before this refactor TARGET selected the SM64 codebase. Accept those old
    # spellings when they are unambiguous, but immediately translate them into
    # the new VARIANT + TARGET model.
    if [[ -n ${TARGET:-} ]] && legacy_pair=$(sm64ra_legacy_target_to_variant "$TARGET" 2>/dev/null); then
        IFS=$'\t' read -r legacy_variant legacy_target <<< "$legacy_pair"
        if [[ -n ${VARIANT:-} ]]; then
            canonical_variant=$(sm64ra_canonical_variant "$VARIANT") || {
                sm64ra_die "Unknown VARIANT=$VARIANT"
                return 1
            }
            if [[ $canonical_variant != "$legacy_variant" ]]; then
                sm64ra_die "Legacy TARGET=$TARGET selects VARIANT=$legacy_variant, conflicting with VARIANT=$VARIANT"
                return 1
            fi
        fi
        sm64ra_warn "TARGET=$TARGET is legacy syntax; use VARIANT=$legacy_variant TARGET=$legacy_target"
        VARIANT=$legacy_variant
        TARGET=$legacy_target
    fi

    sm64ra_apply_preset || return 1

    VARIANT=${VARIANT:-sm64-port}
    TARGET=${TARGET:-host}

    canonical_variant=$(sm64ra_canonical_variant "$VARIANT") || {
        sm64ra_die "Unknown VARIANT=$VARIANT"
        return 1
    }
    VARIANT=$canonical_variant

    case "$TARGET" in
        host|n64|steamrt3-x86_64|steamrt3-aarch64) ;;
        *)
            sm64ra_die "Unknown TARGET=$TARGET. Expected host, n64, steamrt3-x86_64, or steamrt3-aarch64."
            return 1
            ;;
    esac

    if [[ $VARIANT == sm64 && $TARGET != n64 ]]; then
        sm64ra_die "VARIANT=sm64 builds the N64 ROM and requires TARGET=n64"
        return 1
    fi
    if [[ $VARIANT != sm64 && $TARGET == n64 ]]; then
        sm64ra_die "TARGET=n64 requires VARIANT=sm64"
        return 1
    fi

    export PRESET VARIANT TARGET
}

sm64ra_resolve_asset_config() {
    local asset_mode_was_explicit=0
    local baserom_was_explicit=0
    local old_rom new_rom

    if [[ -n ${ASSET_MODE+x} && -n ${ASSET_MODE:-} ]]; then
        asset_mode_was_explicit=1
    fi
    if [[ -n ${BASEROM_FPATH+x} && -n ${BASEROM_FPATH:-} ]]; then
        baserom_was_explicit=1
    fi

    # EXTERNAL_ROM_FPATH is the historical spelling used by build.sh. Keep it
    # working with its old semantics. BASEROM_FPATH is the clearer spelling for
    # explicitly selecting baserom assets.
    EXTERNAL_ROM_FPATH=${EXTERNAL_ROM_FPATH:-}
    BASEROM_FPATH=${BASEROM_FPATH:-}

    if [[ -n $EXTERNAL_ROM_FPATH && -n $BASEROM_FPATH ]]; then
        old_rom=$(readlink -m "$EXTERNAL_ROM_FPATH")
        new_rom=$(readlink -m "$BASEROM_FPATH")
        if [[ $old_rom != "$new_rom" ]]; then
            sm64ra_die "BASEROM_FPATH and EXTERNAL_ROM_FPATH name different files"
            return 1
        fi
    elif [[ -n $EXTERNAL_ROM_FPATH ]]; then
        BASEROM_FPATH=$EXTERNAL_ROM_FPATH
    elif [[ -n $BASEROM_FPATH ]]; then
        # Reference builds historically consume EXTERNAL_ROM_FPATH. Mirroring
        # the new spelling into it preserves that path without changing the old
        # EXTERNAL_ROM_FPATH default behavior below.
        EXTERNAL_ROM_FPATH=$BASEROM_FPATH
    fi

    if [[ $asset_mode_was_explicit == 0 ]]; then
        if [[ $baserom_was_explicit == 1 ]]; then
            ASSET_MODE=baserom
        else
            ASSET_MODE=generate
        fi
    fi

    case "$ASSET_MODE" in
        generate|reuse|baserom) ;;
        existing|skip)
            sm64ra_warn "ASSET_MODE=$ASSET_MODE is an alias; use ASSET_MODE=reuse"
            ASSET_MODE=reuse
            ;;
        *)
            sm64ra_die "Unknown ASSET_MODE=$ASSET_MODE. Expected generate, reuse, or baserom."
            return 1
            ;;
    esac

    export ASSET_MODE BASEROM_FPATH EXTERNAL_ROM_FPATH
}

sm64ra_is_container_target() {
    case "$1" in
        steamrt3-x86_64|steamrt3-aarch64) return 0 ;;
        *) return 1 ;;
    esac
}
