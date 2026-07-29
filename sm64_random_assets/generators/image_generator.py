from __future__ import annotations

import numpy as np
import kwimage

from sm64_random_assets.util import util_random
from sm64_random_assets.realizations import (
    AssetRealization,
    RealizationPolicy,
    RealizationRegistry,
)
from sm64_random_assets.image_catalog import determine_asset_identity
from sm64_random_assets.image_realizations.human_joncrall import random as human_random
from sm64_random_assets.image_realizations.human_joncrall import semantic as human_semantic
from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking import pil_textures
from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking import environment_textures
from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking import frequent_textures
from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking import bowser_peach_textures
from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking import differentiated_textures
from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking import intro_textures
from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking import transparency_masks
from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking import menu_pointers
from sm64_random_assets.image_realizations.openai_gpt_5_6_thinking import file_select_textures


def _intro_texture_supports(identity, info):
    return intro_textures.supports_intro_texture(identity, info)


def _menu_pointer_supports(identity, info):
    return menu_pointers.supports_menu_pointer(identity, info)


def _file_select_texture_supports(identity, info):
    return file_select_textures.supports_file_select_texture(identity, info)


def _transparency_mask_supports(identity, info):
    return transparency_masks.supports_transparency_mask(identity, info)


def _semantic_supports(identity, info):
    # Restrict the human semantic realization to the families it is best at.
    preferred_families = {
        'hud.power_meter',
    }
    if identity.family in preferred_families or identity.family.startswith('glyph.'):
        return human_semantic.can_generate(identity.fname, info.get('shape', None))
    preferred_fnames = {
        'levels/intro/2_copyright.rgba16.png',
        'levels/intro/3_tm.rgba16.png',
    }
    if identity.fname in preferred_fnames:
        return human_semantic.can_generate(identity.fname, info.get('shape', None))
    return False



def _early_environment_supports(identity, info):
    return environment_textures.can_generate(identity.fname, info.get('shape', None))


def _differentiated_texture_supports(identity, info):
    return differentiated_textures.supports_differentiated_texture(identity, info)


def _bowser_peach_supports(identity, info):
    return bowser_peach_textures.supports_bowser_peach_texture(identity, info)


def _castle_portrait_supports(identity, info):
    return identity.fname in pil_textures._CASTLE_PORTRAIT_LAYOUTS


_DEFAULT_IMAGE_REALIZATION_REGISTRY = None


def default_image_realization_registry():
    global _DEFAULT_IMAGE_REALIZATION_REGISTRY
    if _DEFAULT_IMAGE_REALIZATION_REGISTRY is None:
        registry = RealizationRegistry()
        registry.register(AssetRealization(
            id='human.random',
            author='human:joncrall',
            version=1,
            estimated_quality=0.0,
            generator=human_random.generate_random_image_data,
            families=frozenset({'*'}),
            notes='Original fully random fallback generator.',
        ))
        registry.register(AssetRealization(
            id='human.semantic',
            author='human:joncrall',
            version=1,
            estimated_quality=0.70,
            generator=human_semantic.generate_semantic_image_data,
            supports=_semantic_supports,
            notes='Original human-authored semantic, glyph, and HUD generator; preferred for text glyph sets and the power meter/life bar, but not for semantic character-part textures like eyes.',
        ))
        registry.register(AssetRealization(
            id='openai.pil-textures',
            author='openai:gpt-5.6-thinking',
            version=8,
            estimated_quality=0.69,
            generator=pil_textures.render_pil_texture,
            families=frozenset({'*'}),
            notes='Deterministic PIL-authored procedural textures with methodical family, role, motif, and material inference for broad clean-room asset coverage, including improved coins, bob-ombs, Mario eyes, water textures, grass textures, and broader clean-room castle portrait routing.',
        ))
        registry.register(AssetRealization(
            id='openai.early-environment',
            author='openai:gpt-5.6-thinking',
            version=3,
            estimated_quality=0.79,
            generator=environment_textures.render_environment_texture,
            supports=_early_environment_supports,
            notes='Focused semantic environment textures for early-game levels and shared banks, including blue water, grassy castle grounds, stronger stone / wood material differentiation, alpha-aware hedge / fence / icy mask tiles, and screenshot-verified Castle Grounds routing so the lawn stays grass, the castle stays masonry, water stays blue, and the fence keeps a transparent iron mask.',
        ))
        registry.register(AssetRealization(
            id='openai.frequent-textures',
            author='openai:gpt-5.6-thinking',
            version=2,
            estimated_quality=0.80,
            generator=frequent_textures.render_frequent_texture,
            supports=frequent_textures.supports_frequent_texture,
            notes='Restored focused high-exposure texture pass for Mario details, recurring collectibles, shadows, effects, trees, doors, boxes, switches, signposts, Goombas, and Koopa shells after later environment overlays replaced the registry file.',
        ))
        registry.register(AssetRealization(
            id='openai.transparency-masks',
            author='openai:gpt-5.6-thinking',
            version=1,
            estimated_quality=0.88,
            generator=transparency_masks.render_transparency_mask,
            supports=_transparency_mask_supports,
            notes='Dedicated code-authored IA/alpha-mask pass for transparent textures: actor effects, coin silhouettes, smoke, flames, shadows, foliage masks, fences, cobwebs, cloud cutouts, and other assets where alpha definition matters more than color detail.',
        ))
        registry.register(AssetRealization(
            id='openai.differentiated-textures',
            author='openai:gpt-5.6-thinking',
            version=1,
            estimated_quality=0.83,
            generator=differentiated_textures.render_differentiated_texture,
            supports=_differentiated_texture_supports,
            notes='Code-authored differentiation pass for multi-part actors and frame animations that previously collapsed to samey generic materials. Distinguishes eyes, mouths, shells, scales, fur, foliage, machinery, locks, bars, effects, waves, smoke, explosions, and rotating egg frames.',
        ))
        registry.register(AssetRealization(
            id='openai.file-select-textures',
            author='openai:gpt-5.6-thinking',
            version=1,
            estimated_quality=0.91,
            generator=file_select_textures.render_file_select_texture,
            supports=_file_select_texture_supports,
            notes='Dedicated code-authored file-select presentation: sapphire menu backdrops, separate occupied and empty save-slot plaques, and differentiated Score, Copy, Erase, Sound, and auxiliary action-button materials while preserving human-rendered labels and the dedicated glove pointer.',
        ))
        registry.register(AssetRealization(
            id='openai.menu-pointers',
            author='openai:gpt-5.6-thinking',
            version=1,
            estimated_quality=0.90,
            generator=menu_pointers.render_menu_pointer,
            supports=_menu_pointer_supports,
            notes='Dedicated transparent menu cursors with strongly differentiated pointing and pressed glove silhouettes for the file-select/main-menu pair and title-screen hand states.',
        ))
        registry.register(AssetRealization(
            id='openai.intro-textures',
            author='openai:gpt-5.6-thinking',
            version=1,
            estimated_quality=0.86,
            generator=intro_textures.render_intro_texture,
            supports=_intro_texture_supports,
            notes='Dedicated code-authored startup and title-screen textures: coherent title background strips, glossy intro-logo materials, animated stars and sparkles, Mario-face shine, and distinct open/closed glove cursors.',
        ))
        registry.register(AssetRealization(
            id='openai.bowser-peach-textures',
            author='openai:gpt-5.6-thinking',
            version=1,
            estimated_quality=0.84,
            generator=bowser_peach_textures.render_bowser_peach_texture,
            supports=_bowser_peach_supports,
            notes='Dedicated code-authored Bowser/Peach fake-out portraits plus differentiated Bowser, Peach, and Bowser-flame actor textures based on descriptive asset names.',
        ))
        registry.register(AssetRealization(
            id='openai.castle-portraits',
            author='openai:gpt-5.6-thinking',
            version=2,
            estimated_quality=0.82,
            generator=pil_textures.render_pil_texture,
            supports=_castle_portrait_supports,
            notes='Dedicated clean-room scenic textures for every castle portrait and portal painting texture, including multi-part course portraits and the Tiny-Huge Island pair.',
        ))
        _DEFAULT_IMAGE_REALIZATION_REGISTRY = registry
    return _DEFAULT_IMAGE_REALIZATION_REGISTRY


def build_realization_policy(target_quality=0.0, include_authors=None,
                             exclude_authors=None, registry=None):
    registry = default_image_realization_registry() if registry is None else registry
    include_authors = ('*',) if include_authors is None else tuple(include_authors)
    exclude_authors = () if exclude_authors is None else tuple(exclude_authors)
    return RealizationPolicy(
        registry=registry,
        target_quality=float(target_quality),
        include_authors=include_authors,
        exclude_authors=exclude_authors,
    )


def validate_generated_image(generated, requested_shape):
    if generated is None:
        raise ValueError('Generated image is None')
    generated = np.asarray(generated)
    requested_shape = tuple(requested_shape)

    if generated.ndim not in {2, 3}:
        raise ValueError(f'Generated image has invalid ndim={generated.ndim}')

    if generated.dtype != np.uint8:
        if generated.dtype.kind == 'f':
            generated = kwimage.ensure_uint255(generated.clip(0, 1))
        else:
            generated = generated.astype(np.uint8)

    if len(requested_shape) == 2:
        target_dsize = requested_shape[::-1]
    else:
        target_dsize = requested_shape[0:2][::-1]
    generated = kwimage.imresize(generated, dsize=target_dsize, interpolation='nearest')

    if len(requested_shape) == 3:
        req_channels = requested_shape[2]
        if generated.ndim == 2:
            generated = generated[:, :, None]
        gen_channels = generated.shape[2]
        if gen_channels > req_channels:
            generated = generated[:, :, -req_channels:]
        elif gen_channels < req_channels:
            if gen_channels == 1:
                generated = np.repeat(generated, req_channels, axis=2)
            else:
                pad = np.zeros(generated.shape[0:2] + (req_channels - gen_channels,), dtype=generated.dtype)
                generated = np.concatenate([generated, pad], axis=2)
        if generated.shape != requested_shape:
            raise ValueError(f'Generated image shape {generated.shape!r} does not match requested {requested_shape!r}')
    else:
        if generated.shape != requested_shape:
            raise ValueError(f'Generated image shape {generated.shape!r} does not match requested {requested_shape!r}')
    return np.ascontiguousarray(generated)


def generate_image(output_dpath, info, realization_policy=None):
    """Thin orchestrator for versioned image realizations."""
    if info.get('shape', None) is None:
        return {'status': 'value-error: image has no shape'}
    shape = tuple(info['shape'])
    fname = str(info['fname'])

    realization_policy = build_realization_policy() if realization_policy is None else realization_policy
    identity = determine_asset_identity(info, name_to_text_lut=human_semantic.name_to_text_lut)
    rng = util_random.ensure_rng(fname)

    out_fpath = output_dpath / info['fname']
    out_fpath.parent.ensuredir()

    tried = set()
    generated = None
    chosen_realization = None
    while True:
        realization = realization_policy.resolve(identity, info, exclude_keys=tried)
        if realization is None:
            break
        chosen_realization = realization
        generated = realization.generator(fname, shape, rng, identity)
        if generated is not None:
            break
        tried.add(realization.registry_key())

    if generated is None or chosen_realization is None:
        return {
            'status': 'value-error: no compatible image realization',
            'identity_family': identity.family,
            'identity_member': identity.member,
        }

    generated = validate_generated_image(generated, shape)
    kwimage.imwrite(out_fpath, generated, backend='pil')
    return {
        'status': 'generated',
        'out_fpath': out_fpath,
        'identity_family': identity.family,
        'identity_member': identity.member,
        'realization_id': chosen_realization.id,
        'realization_author': chosen_realization.author,
        'realization_version': chosen_realization.version,
        'realization_estimated_quality': chosen_realization.estimated_quality,
    }


__all__ = [
    'build_realization_policy',
    'default_image_realization_registry',
    'generate_image',
    'validate_generated_image',
]
