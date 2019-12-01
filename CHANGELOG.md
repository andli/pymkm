# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
## [1.4.4]
### Added
- Time shifted rarity supported.
- Default action (no) for yes/no prompts.
- Better support for non-card products like booster displays and bundles.

## [1.4.1]
### Changed
- Update stock price supports YuGiOh (#12)

## [1.4.0]
### Added
- New function: Clean wantslists (show already purchased cards).
### Fixed
- Better error handling in the menu.

## [1.3.5]
### Fixed
- Now considers playsets. (#11)

## [1.3.3]
### Fixed
- Fixed a bug with looking for deals from a user. (#9)

## [1.3.1]
### Fixed
- Fixed a bug with the new version message

## [1.3.0]
### Changed
- Better error handling for connection errors to Cardmarket.
- Improved fault tolerance for CSV imports.
- Added a notice to make users aware of new releases.

## [1.2.3]
### Changed
- Improved table view for finding deals.

### Fixed
- Minor bugs related to filtering deals.

## [1.2.2]
### Fixed
- Merged Fix for unknown rarity type conversion (#8)

## [1.2.0]
### Added
- Finding good deals from a specific user!
- Using new price guide from updated API data to set foil prices.
- Possibilty to not undercut local market.

## Removed
- Old algorithm for pricing foils, since the API now provides trend prices for foils.

## [1.1.0]
### Added
- Lightweight usage reporting

## [1.0.4]
### Added
- Configurable rounding limits for prices.
### Changed
- Broke out the console menu to a separate class.
### Removed
- Cached price changes. It was not very useful. This also fixed one bug.

## [1.0.2] - 2019-07-08
### Fixed
- Fixed a bug with comparing prices for cards not found in stock.

## [1.0.1] - 2019-06-24
### Fixed
- Fixed a bug where the cached price changes file was not present.

## [1.0.0] - 2019-06-18
### Added
- More tests, making it easier to spot bugs and errors.
- This changelog.

### Changed
- Refactored the menu printing function and added version number.