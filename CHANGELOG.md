# Changelog
We [keep a changelog](https://keepachangelog.com/en/1.0.0/).
We aim to adhere to [semantic versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
* Versioned image realizations with `author`, `version`, and `estimated_quality` metadata.
* A quality-based realization selector with author filtering.
* An incremental semantic asset catalog with family/member identities.
* Regression tests for realization selection and deterministic human realizations.

### Changed
* Preserved the original image generators as frozen `human.random` and `human.semantic` realizations.
* Reorganized image generation so the top-level generator is now a thin orchestrator.
* Default `build.sh` target is now the playable `sm64-port`.

## [Version 0.0.1] -

### Added
* Initial version