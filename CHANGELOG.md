# Changelog

## [0.7.0-alpha](https://github.com/markbeep/vvzapi/compare/v0.6.1-alpha...v0.7.0-alpha) (2025-11-05)


### Features

* **api:** add endpoints to retrieve sections and lecturers from units ([dcdd3a6](https://github.com/markbeep/vvzapi/commit/dcdd3a6ca9e84e21796cfed948125c9429310c6f))
* **api:** add unit-changes endpoint using unit ID ([e8cbf31](https://github.com/markbeep/vvzapi/commit/e8cbf311b72fe0428bfaf733a7bfd2db404498ab))
* **api:** add vvz filters to unit endpoint. Closes [#29](https://github.com/markbeep/vvzapi/issues/29) ([1ed9d84](https://github.com/markbeep/vvzapi/commit/1ed9d8452c73f5b175603acebef2aef8cbf5ee8b))
* **api:** Add VVZ-like alphabetical sort to sections. Closes [#26](https://github.com/markbeep/vvzapi/issues/26). Closes [#30](https://github.com/markbeep/vvzapi/issues/30). ([44c0dce](https://github.com/markbeep/vvzapi/commit/44c0dce2a68f6e6710fd8cefa9487484768d71b6))


### Bug Fixes

* **scraper:** only scrape units from root page without filters to avoid duplicates ([742020c](https://github.com/markbeep/vvzapi/commit/742020ccfedbd50a4dd7c0ddb436716f749e594b))


### Miscellaneous Chores

* offload ideas from readme into gh issues ([ace17fd](https://github.com/markbeep/vvzapi/commit/ace17fd661763785125a5bad559722475ffc9c51))
* remove network-mode:host from local devcontainer ([1d6d545](https://github.com/markbeep/vvzapi/commit/1d6d5459ec232d2d6a7c72a22e008b35c0248869))

## [0.6.1-alpha](https://github.com/markbeep/vvzapi/compare/v0.6.0-alpha...v0.6.1-alpha) (2025-11-05)


### Bug Fixes

* **scraper:** detect duplicate changes and update values instead of creating a new entry. Closes [#24](https://github.com/markbeep/vvzapi/issues/24) ([5ba6bcb](https://github.com/markbeep/vvzapi/commit/5ba6bcbba8d8e56f7b5c037a4bbe8366ed949c0f))
* **scraper:** Only rescrape the last relevant semesters. Closes [#22](https://github.com/markbeep/vvzapi/issues/22) ([fec3262](https://github.com/markbeep/vvzapi/commit/fec3262a1445fb0572bfd16b8609e4b059afc350))

## [0.6.0-alpha](https://github.com/markbeep/vvzapi/compare/v0.5.0-alpha...v0.6.0-alpha) (2025-11-04)


### Features

* **scraper:** rescrape latest semesters. Closes [#5](https://github.com/markbeep/vvzapi/issues/5) ([95345ed](https://github.com/markbeep/vvzapi/commit/95345ed7bf94926386622704a5f01f2e0c02d2de))


### Bug Fixes

* **scraper:** keyerror when removing course id ([c24bf9a](https://github.com/markbeep/vvzapi/commit/c24bf9ab5edec1301d3b4c5acffe1a72a2fe7033))
* **scraper:** parse shorter unit numbers like "17-412 1L" correctly ([8ec283e](https://github.com/markbeep/vvzapi/commit/8ec283e78cd6229bb5181d4c8c8ad95154fef66f))

## [0.5.0-alpha](https://github.com/markbeep/vvzapi/compare/v0.4.0-alpha...v0.5.0-alpha) (2025-10-29)


### Features

* add system to track if all units of a semester have been added ([e2262a0](https://github.com/markbeep/vvzapi/commit/e2262a09eb2224d8483d5c1657abcd99c7724753))
* added new signup closing time for group signups ([e2262a0](https://github.com/markbeep/vvzapi/commit/e2262a09eb2224d8483d5c1657abcd99c7724753))
* separated group timeslots into a new 'Group' model that also includes restrictions and group-specific course number ([e2262a0](https://github.com/markbeep/vvzapi/commit/e2262a09eb2224d8483d5c1657abcd99c7724753))


### Bug Fixes

* main parse functions were not running. corrected the naming so that those are correctly executed ([e2262a0](https://github.com/markbeep/vvzapi/commit/e2262a09eb2224d8483d5c1657abcd99c7724753))


### Code Refactoring

* rename "lectures" to "units" for consistency ([8daf0e9](https://github.com/markbeep/vvzapi/commit/8daf0e987e118aac7f6f79e1bc96eb189dbe75c9))
* unified function for extracting timeslots for courses and groups ([e2262a0](https://github.com/markbeep/vvzapi/commit/e2262a09eb2224d8483d5c1657abcd99c7724753))

## [0.4.0-alpha](https://github.com/markbeep/vvzapi/compare/v0.3.0-alpha...v0.4.0-alpha) (2025-10-29)


### Features

* add info for amount of scraped lecturers ([12ef9e3](https://github.com/markbeep/vvzapi/commit/12ef9e3dab9c28dcb1c0005279512bdb46964e5a))


### Bug Fixes

* add default value on scraped_at column ([1d926fd](https://github.com/markbeep/vvzapi/commit/1d926fd0203583047fd9f83cdfa1ac55decce4a6))
* log to stdout with scraper ([6bdb6f6](https://github.com/markbeep/vvzapi/commit/6bdb6f64675ca8b7a80a27adee6dcd1d2e2f5bba))


### Code Refactoring

* shorten link extractor regex ([12ef9e3](https://github.com/markbeep/vvzapi/commit/12ef9e3dab9c28dcb1c0005279512bdb46964e5a))

## [0.3.0-alpha](https://github.com/markbeep/vvzapi/compare/v0.2.1-alpha...v0.3.0-alpha) (2025-10-28)


### Features

* add request url logs to get redirect information ([21f7839](https://github.com/markbeep/vvzapi/commit/21f7839f23a0a8f48d691872b520aad9be73b351))
* Add scraped_at timestamps to main models. Closes [#3](https://github.com/markbeep/vvzapi/issues/3) ([20f511f](https://github.com/markbeep/vvzapi/commit/20f511f983d7030c30b360f3c83ac9f4b5741d85))
* keep track of keys that change ([#11](https://github.com/markbeep/vvzapi/issues/11)) ([82a929f](https://github.com/markbeep/vvzapi/commit/82a929f4ea30839c3c43bf93602bfec4b0a2d022))


### Bug Fixes

* Add unit_id to course composite PK (number+semkez isn't unique) ([20f511f](https://github.com/markbeep/vvzapi/commit/20f511f983d7030c30b360f3c83ac9f4b5741d85))
* handle course number with missing course type and support "by appt.". Closes [#13](https://github.com/markbeep/vvzapi/issues/13) ([6e60075](https://github.com/markbeep/vvzapi/commit/6e60075479a058597bf20738d4ce19ac2ea4fd14))
* ignore misleading key for occurence. Closes [#14](https://github.com/markbeep/vvzapi/issues/14) ([9261a4a](https://github.com/markbeep/vvzapi/commit/9261a4aac56900ba17565388a52e0926161a9cf8))
* Split floor and room into at most 2 values. Closes [#15](https://github.com/markbeep/vvzapi/issues/15) ([4d2e244](https://github.com/markbeep/vvzapi/commit/4d2e24427b581a673eaae68ce18a36290b6df4a2))


### Miscellaneous Chores

* change to strict pyright typing. Closes [#17](https://github.com/markbeep/vvzapi/issues/17) ([127de96](https://github.com/markbeep/vvzapi/commit/127de967bf9ffd1a2dd21a7cb2c6f802a6b8884d))
* update semester status to be complete ([ae5bcff](https://github.com/markbeep/vvzapi/commit/ae5bcffc8e01b1c5b80ee3e2479c2b528077e9c5))


### Code Refactoring

* more cleanly place all extracted links as LinkExtractor links ([0b6f2a4](https://github.com/markbeep/vvzapi/commit/0b6f2a48fadfb7b6b1eb57a92ef87984a71623a3))

## [0.2.1-alpha](https://github.com/markbeep/vvzapi/compare/v0.2.0-alpha...v0.2.1-alpha) (2025-10-27)


### ⚠ BREAKING CHANGES

* Requires old database to be deleted.

### Bug Fixes

* remove unique constraint on unit semkez/number. ([4e410c7](https://github.com/markbeep/vvzapi/commit/4e410c71e6ed6090df2a2d3c8b12ab5d25a91de7))

## 0.2.0-alpha (2025-10-26)


### ⚠ BREAKING CHANGES

* remove foreign keys for more efficient way of adding items to DB
Merged migrations, requires database to be deleted

### Features

* halve the total amount of requests. Closes [#6](https://github.com/markbeep/vvzapi/issues/6) ([df82dc4](https://github.com/markbeep/vvzapi/commit/df82dc4c30c8d722b668918928d1df74de9ab58e))
* split lecturers/examiners of units/courses into separate linked tables ([#7](https://github.com/markbeep/vvzapi/issues/7)) ([2ebf8dc](https://github.com/markbeep/vvzapi/commit/2ebf8dc03c99a3719164bf9ed859cbcd74e3c789))


### Bug Fixes

* move logs into file by default and show key-value pairs from log statement ([2bd524c](https://github.com/markbeep/vvzapi/commit/2bd524c04a57fbdd23eeda84512bed2544f8cc23))


### Miscellaneous Chores

* add pyright type checking ([0daa45f](https://github.com/markbeep/vvzapi/commit/0daa45f66ea8b5459070a49701018ee4ccf448f3))
* add release-please ([e1bcd90](https://github.com/markbeep/vvzapi/commit/e1bcd90ada9f37003a5d7d6ad9a789a59a10a45f))
* finished scraping 2023S/2022W ([1205ee7](https://github.com/markbeep/vvzapi/commit/1205ee7e7740c905ebfdca47348ad99b5e0a1e8b))


### Code Refactoring

* move all models into same file to better cross reference ([0daa45f](https://github.com/markbeep/vvzapi/commit/0daa45f66ea8b5459070a49701018ee4ccf448f3))
* remove foreign keys for more efficient way of adding items to DB ([2bd524c](https://github.com/markbeep/vvzapi/commit/2bd524c04a57fbdd23eeda84512bed2544f8cc23))
