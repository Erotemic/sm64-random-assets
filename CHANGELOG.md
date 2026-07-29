# Changelog
We [keep a changelog](https://keepachangelog.com/en/1.0.0/).
We aim to adhere to [semantic versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
* broadened the clean-room castle portrait generator to cover every castle portrait / portal texture, including Tiny-Huge Island's two standalone square paintings.
* A clean-room `openai.simple-music` M64 realization with compact two-voice melodies and bass lines.
* Target sound-bank inspection to choose suitable pitched instruments when available.
* Structural tests for every US sequence in the bundled manifest.
* A versioned `openai.semantic-synth` audio realization that replaces full-range white noise with deterministic filename-aware synthesized instruments, percussion, vocal-like chirps, and softened effects at higher quality settings.
* Versioned image realizations with `author`, `version`, and `estimated_quality` metadata.
* A quality-based realization selector with author filtering.
* An incremental semantic asset catalog with family/member identities.
* Regression tests for realization selection and deterministic human realizations.

### Changed
* routed all supported castle portrait textures through the dedicated portrait realization and expanded tests to cover the full mapped portrait set.
* `build.sh` now defaults `TARGET_QUALITY` to `1`, selecting semantic samples and simple music.
* Binary generation now participates in author/version/quality realization selection.
* Encode generated 16-bit AIFF PCM in the required big-endian byte order.
* Preserved the original image generators as frozen `human.random` and `human.semantic` realizations.
* Reorganized image generation so the top-level generator is now a thin orchestrator.
* Default `build.sh` target is now the playable `sm64-port`.

## [Version 0.0.1] -

### Added
* Initial version* The PIL texture generator now uses a methodical semantic-intent system (family + role + motif + subject) to render more interesting clean-room art for actor parts, surfaces, overlays, and VFX sprites.
* Raise the human semantic glyph / HUD realization quality so it wins for character sets and the life bar; also improve procedural coin textures, Bob-omb body textures, and Bob-omb Battlefield grass classification.
* Restrict the human semantic realization to glyph/HUD-style assets so semantic character-part textures like eyes use the PIL renderer; improve Mario eye rendering, add richer water and grass variants, and keep the human glyph/life-bar work preferred where it belongs.
* Correct Bob-omb Battlefield portrait routing: the actual castle painting is `levels/castle_inside/17.rgba16.png` plus `18.rgba16.png`; render those as a coherent 64x64 scenic painting and restore `levels/bob/*` to battlefield textures.
