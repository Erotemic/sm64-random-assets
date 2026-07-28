# Changelog
We [keep a changelog](https://keepachangelog.com/en/1.0.0/).
We aim to adhere to [semantic versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
* A clean-room `openai.simple-music` M64 realization with compact two-voice melodies and bass lines.
* Target sound-bank inspection to choose suitable pitched instruments when available.
* Structural tests for every US sequence in the bundled manifest.
* A versioned `openai.semantic-synth` audio realization that replaces full-range white noise with deterministic filename-aware synthesized instruments, percussion, vocal-like chirps, and softened effects at higher quality settings.
* Versioned image realizations with `author`, `version`, and `estimated_quality` metadata.
* A quality-based realization selector with author filtering.
* An incremental semantic asset catalog with family/member identities.
* Regression tests for realization selection and deterministic human realizations.

### Changed
* `build.sh` now defaults `TARGET_QUALITY` to `1`, selecting semantic samples and simple music.
* Binary generation now participates in author/version/quality realization selection.
* Encode generated 16-bit AIFF PCM in the required big-endian byte order.
* Preserved the original image generators as frozen `human.random` and `human.semantic` realizations.
* Reorganized image generation so the top-level generator is now a thin orchestrator.
* Default `build.sh` target is now the playable `sm64-port`.

## [Version 0.0.1] -

### Added
* Initial version* The PIL texture generator now uses a methodical semantic-intent system (family + role + motif + subject) to render more interesting clean-room art for actor parts, surfaces, overlays, and VFX sprites.
