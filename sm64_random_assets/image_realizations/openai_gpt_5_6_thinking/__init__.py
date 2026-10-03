from .bowser_peach_textures import (
    FAKEOUT_PORTRAIT_FILES,
    render_bowser_peach_texture,
    supports_bowser_peach_texture,
)
from .castle_inside_textures import (
    CASTLE_INSIDE_TEXTURE_SPECS,
    render_castle_inside_texture,
    supports_castle_inside_texture,
)
from .debug_texture_ids import (
    render_debug_texture_id,
    supports_debug_texture_id,
)
from .differentiated_textures import (
    DIFFERENTIATED_ACTOR_FAMILIES,
    DIFFERENTIATED_ANIMATION_FAMILIES,
    actor_family_from_fname,
    render_differentiated_texture,
    supports_differentiated_texture,
)
from .environment_textures import (
    can_generate as environment_can_generate,
    render_environment_texture,
    resolve_environment_motif,
)
from .file_select_textures import (
    FILE_SELECT_TEXTURE_SPECS,
    render_file_select_texture,
    supports_file_select_texture,
)
from .frequent_textures import (
    FREQUENT_TEXTURE_SPECS,
    classify_frequent_texture,
    render_frequent_texture,
    supports_frequent_texture,
)
from .intro_textures import (
    INTRO_TEXTURE_FILES,
    TITLE_BACKGROUND_FILES,
    render_intro_texture,
    supports_intro_texture,
)
from .menu_pointers import (
    MENU_POINTER_FILES,
    render_menu_pointer,
    supports_menu_pointer,
)
from .pil_textures import (
    TextureIntent,
    analyze_texture_intent,
    classify_texture_role,
    classify_texture_subject,
    render_pil_texture,
)
from .transparency_masks import (
    render_transparency_mask,
    supports_transparency_mask,
)

__all__ = [
    'CASTLE_INSIDE_TEXTURE_SPECS',
    'DIFFERENTIATED_ACTOR_FAMILIES',
    'DIFFERENTIATED_ANIMATION_FAMILIES',
    'FAKEOUT_PORTRAIT_FILES',
    'FILE_SELECT_TEXTURE_SPECS',
    'FREQUENT_TEXTURE_SPECS',
    'INTRO_TEXTURE_FILES',
    'MENU_POINTER_FILES',
    'TITLE_BACKGROUND_FILES',
    'TextureIntent',
    'actor_family_from_fname',
    'analyze_texture_intent',
    'classify_frequent_texture',
    'classify_texture_role',
    'classify_texture_subject',
    'environment_can_generate',
    'render_bowser_peach_texture',
    'render_castle_inside_texture',
    'render_debug_texture_id',
    'render_differentiated_texture',
    'render_environment_texture',
    'render_file_select_texture',
    'render_frequent_texture',
    'render_intro_texture',
    'render_menu_pointer',
    'render_pil_texture',
    'render_transparency_mask',
    'resolve_environment_motif',
    'supports_bowser_peach_texture',
    'supports_castle_inside_texture',
    'supports_debug_texture_id',
    'supports_differentiated_texture',
    'supports_file_select_texture',
    'supports_frequent_texture',
    'supports_intro_texture',
    'supports_menu_pointer',
    'supports_transparency_mask',
]
