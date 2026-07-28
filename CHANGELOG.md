## Unreleased

### Added

* Add versioned asset realization registries with author metadata and estimated
  quality selection.
* Add ``--target_quality``, ``--include_authors``, and ``--exclude_authors``
  controls for image realization selection.
* Preserve the original human-authored semantic and random generators as
  ``human.semantic-v1`` and ``human.random-v1``.
* Add regression tests for nearest-quality selection, author filtering, version
  tie-breaking, deterministic random output, and clean-room registration.

### Changed

* Default ``build.sh`` to the playable ``sm64-port`` target while retaining
  ``pc`` as an alias.

### Fixed

* Use the filename-derived random state in the low-entropy special-texture path
  instead of global NumPy randomness.

# Changelog
We [keep a changelog](https://keepachangelog.com/en/1.0.0/).
We aim to adhere to [semantic versioning](https://semver.org/spec/v2.0.0.html).

## [Version 0.0.1] -

### Added
* Initial version

