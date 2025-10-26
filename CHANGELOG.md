# Changelog

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
