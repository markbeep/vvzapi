# Changelog

## [1.10.0](https://github.com/markbeep/vvzapi/compare/v1.9.0...v1.10.0) (2026-02-11)


### Features

* **scraper:** scrape course review ratings ([16a66bf](https://github.com/markbeep/vvzapi/commit/16a66bf487cd31ac7ae0010e13c90b6cf854ae78))
* **search:** add coursereview operator to query by average rating ([5151c8e](https://github.com/markbeep/vvzapi/commit/5151c8e62d16d2215c1c786e1627258a2f9043df))
* **search:** allow querying by lecturer by clicking on name on unit page ([1ea359b](https://github.com/markbeep/vvzapi/commit/1ea359ba1d5540e1f27f94370f84cfb54bff4257))


### Bug Fixes

* **search:** escape title/description in header ([926800a](https://github.com/markbeep/vvzapi/commit/926800a2618c1e14173ca3e877abcc696eef86c2))


### Documentation

* add terms of use for clarity ([2f870f5](https://github.com/markbeep/vvzapi/commit/2f870f515805068e1252970f7e75d2c99eaceb0c))
* added readme banner ([e3b9aab](https://github.com/markbeep/vvzapi/commit/e3b9aab7292bb3ef07ad57d1f825fb499c1754a5))


### Miscellaneous Chores

* add k6 for benchmarking the website ([aa4bafd](https://github.com/markbeep/vvzapi/commit/aa4bafd5ad27462d451fad54df720ca3d89ba924))
* **search:** update index page description ([75e093b](https://github.com/markbeep/vvzapi/commit/75e093babc6d02d2038d52a45e21f124d7e457f5))

## [1.9.0](https://github.com/markbeep/vvzapi/compare/v1.8.0...v1.9.0) (2026-02-07)


### Features

* **search:** add compact mode for viewing search results ([b87c342](https://github.com/markbeep/vvzapi/commit/b87c342d5dd734aee252c962c7904433290257e2))
* **search:** prefetch script on mousedown for anchor tags ([a2112d5](https://github.com/markbeep/vvzapi/commit/a2112d502fedda8e93f5e6f358075412bd8b7321))


### Bug Fixes

* **scraper:** allow for lecturers to not have a title ([119fbba](https://github.com/markbeep/vvzapi/commit/119fbbadad55b519c668b71518d6b31100dca14d))
* **search:** allow searches to be scraped according to robots.txt ([619df0d](https://github.com/markbeep/vvzapi/commit/619df0da0ee943e226548ae4d2828e9ce00a2013))
* **search:** fix tabbing index to skip stacked results in search page ([29d1bc2](https://github.com/markbeep/vvzapi/commit/29d1bc20a752dd8b14752a7cb23529165331df67))


### Miscellaneous Chores

* **search:** adjust the title/description metadata tags to more updated keywords ([915c510](https://github.com/markbeep/vvzapi/commit/915c510a6ad96b4c2b3212dd889d900e7847d1d7))
* **search:** make AND/OR operators lower-case in query information ([29d1bc2](https://github.com/markbeep/vvzapi/commit/29d1bc20a752dd8b14752a7cb23529165331df67))
* **search:** update favicon to blue lines ([a4d4533](https://github.com/markbeep/vvzapi/commit/a4d4533d57cc300d3287ada22ed19857d0b01150))


### Code Refactoring

* **search:** switch to jinjax for templating and fix a few typing ([38395ff](https://github.com/markbeep/vvzapi/commit/38395ff98c85c8386445d8cc1e6fbb1cf3e5cbf5))


### Continuous Integration

* fix missing ruff formatter ([20194d3](https://github.com/markbeep/vvzapi/commit/20194d3ef9ffd830ca83fb30537fc5881738e6d4))

## [1.8.0](https://github.com/markbeep/vvzapi/compare/v1.7.0...v1.8.0) (2026-02-05)


### Features

* **scraper:** add lecturer title and department ([30b591b](https://github.com/markbeep/vvzapi/commit/30b591b55ac8799a3183c474de1ff253cdf357c0))
* **search:** add animated search placeholders on root page ([a765f14](https://github.com/markbeep/vvzapi/commit/a765f14fc4788ce35b8f25cc465c127ead992874))


### Bug Fixes

* fix ints being read out as strings from json array ([ddfcacb](https://github.com/markbeep/vvzapi/commit/ddfcacb7d04bf88677fef456a96e12c095b968e1))
* **search:** add cannonical link to unit pages leading to newest page ([9491f1a](https://github.com/markbeep/vvzapi/commit/9491f1a1102c6468948b60d99240ccaadbeba83b))


### Performance Improvements

* **search:** improve page load metrics ([e5f1db7](https://github.com/markbeep/vvzapi/commit/e5f1db74df52d16b1cd50b0caad16146a68b8cf6))


### Miscellaneous Chores

* add example commands for how to solely scrape lecturers ([1b6242a](https://github.com/markbeep/vvzapi/commit/1b6242a3faa9844f593cccc49c6b081c4db9f9f7))
* install arm tools in devcontainer ([30b591b](https://github.com/markbeep/vvzapi/commit/30b591b55ac8799a3183c474de1ff253cdf357c0))


### Continuous Integration

* enable type/tests to run on pull requests ([99fde66](https://github.com/markbeep/vvzapi/commit/99fde666ebc52c6441a2a8d2ed1fa90bfc96c858))

## [1.7.0](https://github.com/markbeep/vvzapi/compare/v1.6.0...v1.7.0) (2026-02-01)


### Features

* **search:** add notice when viewing out-of-date units ([c7cfddc](https://github.com/markbeep/vvzapi/commit/c7cfddc943a90f41f7fa4321f648a8f2682add68))
* **search:** match department on short acronym/name ([e2718d2](https://github.com/markbeep/vvzapi/commit/e2718d2c51cfcf6fb9b8b9ace65574e6ebcebf94))


### Bug Fixes

* **search:** add cache busting to site CSS to circumvent cloudflare ([eb6df48](https://github.com/markbeep/vvzapi/commit/eb6df486fec3d09aeab2f164c080e3eb107de6d3))
* **search:** add reference to favicon in header ([d2ff3bb](https://github.com/markbeep/vvzapi/commit/d2ff3bbbcd86fb19e00427149710dff7986e9a48))
* **search:** fix robots.txt not being returned ([6c5fcf8](https://github.com/markbeep/vvzapi/commit/6c5fcf83fdc36de5319cdcd68dd76fc46866ba1e))
* vacuum db into separate file to prevent file corruption ([9d1fc6e](https://github.com/markbeep/vvzapi/commit/9d1fc6e1c349485d412120f6ede5622ef2f99711))


### Dependencies

* update dependencies for python 3.14 compatibility ([f5bf30e](https://github.com/markbeep/vvzapi/commit/f5bf30ea2628288674f7ddbe5e5d9a44328b8843))
* update python to 3.14 ([ab908d9](https://github.com/markbeep/vvzapi/commit/ab908d90cbb283bf306244d7d952fa828f3e1536))


### Miscellaneous Chores

* add GPLv3 license ([ff6c5b1](https://github.com/markbeep/vvzapi/commit/ff6c5b136d1f0985624ac1bbb3fdca83fc7c7133))
* add jj to devcontainer ([cc9483e](https://github.com/markbeep/vvzapi/commit/cc9483e1f97c91da4dd5e127a09e45cae5c96bf6))
* add justfile for local development ([625f501](https://github.com/markbeep/vvzapi/commit/625f50153d88d57ce8dfc000a755e007cab0bc00))
* **api:** send more info to plausible ([d810e07](https://github.com/markbeep/vvzapi/commit/d810e0788c617931dc08d0ac6c1d9627c9e4d03a))
* set type checking mode to more strict "all" ([757bf6e](https://github.com/markbeep/vvzapi/commit/757bf6e0c1661e67fde9a951078cf1bee354e84e))
* test mise for local development ([652525f](https://github.com/markbeep/vvzapi/commit/652525fd73f95d760529dc3703ac9e9521abd294))


### Build System

* reduce scraper docker image size by removing uv from final step ([b688a53](https://github.com/markbeep/vvzapi/commit/b688a53c5824362b8682e5927f47907b9b47e8b5))

## [1.6.0](https://github.com/markbeep/vvzapi/compare/v1.5.0...v1.6.0) (2026-01-09)


### Features

* **api:** data dump endpoint to download database. Closes [#27](https://github.com/markbeep/vvzapi/issues/27) ([cb62114](https://github.com/markbeep/vvzapi/commit/cb62114741038240efb80eb7e78f3480249dbf69))
* **search:** add link anchors to guide page ([efa91cc](https://github.com/markbeep/vvzapi/commit/efa91cc1750d579496a65e1acf44c903cb685639))
* **search:** make external links more clear with an icon ([42bc492](https://github.com/markbeep/vvzapi/commit/42bc4922845e28ae0ab30248bd34fab0d4adc170))
* **search:** show last scraped_at time on unit details page ([799c6f4](https://github.com/markbeep/vvzapi/commit/799c6f429975f5ae149f029fa7471d9ec333cafc))


### Bug Fixes

* **search:** fix offered in typo ([a38350d](https://github.com/markbeep/vvzapi/commit/a38350d3f2400c7269c3f66db58c52744a3fdd40))
* **search:** fix order of operator parsing to correctly match &gt;= and &lt;= ([4637d95](https://github.com/markbeep/vvzapi/commit/4637d95372a31eb14238b4ba3719dc30953b9aa2))
* **search:** fix wrongly overflowing text about filter negation on guide page ([41db41e](https://github.com/markbeep/vvzapi/commit/41db41efa0656b556370d9d0eea49078c099a59b))


### Reverts

* "feat(search): show last scraped_at time on unit details page" ([d59c37c](https://github.com/markbeep/vvzapi/commit/d59c37cef664f29fdc7c19757c7fd4cb277ac999))


### Documentation

* update readme with model name explanation and details on how to contribute ([cb62114](https://github.com/markbeep/vvzapi/commit/cb62114741038240efb80eb7e78f3480249dbf69))


### Continuous Integration

* increase basedpyright typing from 'recommended' to 'strict' ([af123b0](https://github.com/markbeep/vvzapi/commit/af123b009826ef6f14c859f086dd3e9042031dde))

## [1.5.0](https://github.com/markbeep/vvzapi/compare/v1.4.0...v1.5.0) (2026-01-08)


### Features

* **search:** add query time to results ([c9378cf](https://github.com/markbeep/vvzapi/commit/c9378cfd836f0676e1a08d862a325391e85cda1a))
* **search:** OR operator and parentheses for more complex queries ([45227ea](https://github.com/markbeep/vvzapi/commit/45227ea909ea3d8527b3c9052b567337cb0fcf2a))
* **search:** remove awkward '!:' operator and instead use prefixed minus operator for negation ([3c76208](https://github.com/markbeep/vvzapi/commit/3c76208dcc9b9d5d38b0281948f119e629f83cfd))


### Bug Fixes

* **api:** fix wrong path in guide for first example ([80d6452](https://github.com/markbeep/vvzapi/commit/80d64528ba1679c389f85dc1c38845bd96ac7fc0))
* **search:** fix course numbers not being matched by regex ([3c76208](https://github.com/markbeep/vvzapi/commit/3c76208dcc9b9d5d38b0281948f119e629f83cfd))
* **search:** fix query from becoming infinitely big and fix invalid offered in results page filters ([231d929](https://github.com/markbeep/vvzapi/commit/231d92972e4d2dffd15c9df873896cc3a762a568))


### Miscellaneous Chores

* add back warnings for basedpyright ([05906df](https://github.com/markbeep/vvzapi/commit/05906df9900bf2e9a1d0d399680a53ad9f5830be))

## [1.4.0](https://github.com/markbeep/vvzapi/compare/v1.3.0...v1.4.0) (2026-01-07)


### Features

* add exam type filter ([03baace](https://github.com/markbeep/vvzapi/commit/03baacecd35a80ba3b3d250176e6cf6b5f86ca95))
* add sitemap ([ae0afb0](https://github.com/markbeep/vvzapi/commit/ae0afb030c469a1e2ba1bf161e43811cc1768122))
* **api:** offered in filters are now all matched against a single path of sections instead of against arbitrary matching sections ([e6e47b1](https://github.com/markbeep/vvzapi/commit/e6e47b1c76f50c002a98fc01b31b3e8d221b7ac8))


### Bug Fixes

* **api:** display search and unit information in embed description ([6152a74](https://github.com/markbeep/vvzapi/commit/6152a74909695e01d1fd8a2c961aa209f3fb539a))
* **api:** fix crashing of unit pages if course hours are missing ([488491b](https://github.com/markbeep/vvzapi/commit/488491b4473bf95281e28aadbd25d9b511cbdce9))
* **api:** fix non-stacked elements not expanding correctly ([0c7704b](https://github.com/markbeep/vvzapi/commit/0c7704b18efca36b8bf8a63cd0159643996a2269))
* **api:** fix plausible event condition ([77655df](https://github.com/markbeep/vvzapi/commit/77655df00f87ddc1927d225e2b37c23943d4b9e6))
* **api:** remove empty examination/registration block if no information exists ([6152a74](https://github.com/markbeep/vvzapi/commit/6152a74909695e01d1fd8a2c961aa209f3fb539a))
* **api:** remove german title if it's the same as the english ([0c7704b](https://github.com/markbeep/vvzapi/commit/0c7704b18efca36b8bf8a63cd0159643996a2269))
* fix departments filter showing other departments ([03baace](https://github.com/markbeep/vvzapi/commit/03baacecd35a80ba3b3d250176e6cf6b5f86ca95))
* fix incorrect media type for static files ([65db758](https://github.com/markbeep/vvzapi/commit/65db758647d8f28d324e953f29ed016d1f30a88f))


### Miscellaneous Chores

* move uv sync ahead of copy in dockerfiles ([2941916](https://github.com/markbeep/vvzapi/commit/29419166ba94fbd96c6ed644d74dc775a427c7f4))


### Tests

* replace ty with pyrefly type checking ([ae0afb0](https://github.com/markbeep/vvzapi/commit/ae0afb030c469a1e2ba1bf161e43811cc1768122))


### Build System

* **api:** reduce docker image size by splitting the build steps ([11c64e0](https://github.com/markbeep/vvzapi/commit/11c64e02367e12fb422d87410cecf8eed00ad861))

## [1.3.0](https://github.com/markbeep/vvzapi/compare/v1.2.0...v1.3.0) (2025-12-27)


### Features

* **api:** enable CORS ([ff61a23](https://github.com/markbeep/vvzapi/commit/ff61a231fc5a0e7c707a699302f67b335aba7106))
* **api:** fetch coursereview score when visiting a unit page ([87d0302](https://github.com/markbeep/vvzapi/commit/87d0302313cfed00e3c4fbca40e8888928a0f755))
* **api:** group together the same course by number ([2df51f7](https://github.com/markbeep/vvzapi/commit/2df51f755afec6e2a28f687d3f720b6840182f2d))


### Bug Fixes

* **api:** fix formatting on vvz/cr and results page links ([1d427ec](https://github.com/markbeep/vvzapi/commit/1d427ec980eb74f565f80fbee592528fbe2e1606))
* **api:** intersect offered in filters instead of unioning ([c2ba0e8](https://github.com/markbeep/vvzapi/commit/c2ba0e85bd6bb82c1f13417f0ac85aaa150ab850))
* **api:** wrap long links correctly ([f469251](https://github.com/markbeep/vvzapi/commit/f469251f1e2e45dfd44e4623f26a5751eee607c3))
* **scraper:** make exercise sessions where weekdays are missing get parsed correctly ([1f28faa](https://github.com/markbeep/vvzapi/commit/1f28faa0467196245d7d2b252ea2d87c3e236092))


### Styles

* **api:** change to a blue theme for search ([a8ff8ca](https://github.com/markbeep/vvzapi/commit/a8ff8cabea29f6fd1fd80b42b456d2ace5c49e5d))


### Miscellaneous Chores

* replace pyright type checking with ty ([06eb0ab](https://github.com/markbeep/vvzapi/commit/06eb0abc514cfe89bf3a29181fdc54ba7bb6f094))

## [1.2.0](https://github.com/markbeep/vvzapi/compare/v1.1.3...v1.2.0) (2025-12-22)


### Features

* **api:** add courses and lecturers to unit details page ([4faf15b](https://github.com/markbeep/vvzapi/commit/4faf15b1b9816cdf9d0f114dacfd5d1a51e6e320))
* **api:** add offered in details and search filter ([8fc98fc](https://github.com/markbeep/vvzapi/commit/8fc98fc352fdc5b014801cef33514c0c33c2cc99))
* **api:** change semester/year of a unit while on details page ([5040463](https://github.com/markbeep/vvzapi/commit/5040463736b132659e1e6852e4bc73e99f81dcca))
* **api:** show filters that got applied when searching ([09a1cf7](https://github.com/markbeep/vvzapi/commit/09a1cf7e32f395f82e1c23b824a675e39122609b))


### Bug Fixes

* **api:** correctly link to coursereview ([9d06379](https://github.com/markbeep/vvzapi/commit/9d063795c4197190a00160053f87880bcf26cc40))
* **api:** correctly sort using department/level ([e1141f4](https://github.com/markbeep/vvzapi/commit/e1141f404edf2bf552c452bb79786e0033bf088f))
* **api:** keep track of search options across pages ([a34a9be](https://github.com/markbeep/vvzapi/commit/a34a9bebde47174ab0be3f0cfaf98394e2fed6b0))
* **api:** make periodicity value more clear on unit page ([d68ede3](https://github.com/markbeep/vvzapi/commit/d68ede3503e596031e72bcab3dc5c8547c135f85))
* **api:** show short levels/departments with long title on hover ([d68ede3](https://github.com/markbeep/vvzapi/commit/d68ede3503e596031e72bcab3dc5c8547c135f85))
* **scraper:** not rescraping correctly ([9043c0b](https://github.com/markbeep/vvzapi/commit/9043c0b77d7ac3414e2650d2aa9f3c8aab920dfa))
* **scraper:** parse multiple courses without explicit weekdays correctly ([c63ccb7](https://github.com/markbeep/vvzapi/commit/c63ccb7f439446fa02012c96bd962310f33977df))


### Miscellaneous Chores

* make parsing of enums from db more consistent with separate wrapper class ([d68ede3](https://github.com/markbeep/vvzapi/commit/d68ede3503e596031e72bcab3dc5c8547c135f85))

## [1.1.3](https://github.com/markbeep/vvzapi/compare/v1.1.2...v1.1.3) (2025-12-21)


### Bug Fixes

* allow for a unit to be in multiple departments ([b9bf043](https://github.com/markbeep/vvzapi/commit/b9bf043b96e4d11be6f4d218e97ff342f56c5df5))
* **api:** title in search is not combined but instead each word is matched ([b9bf043](https://github.com/markbeep/vvzapi/commit/b9bf043b96e4d11be6f4d218e97ff342f56c5df5))

## [1.1.2](https://github.com/markbeep/vvzapi/compare/v1.1.1...v1.1.2) (2025-12-21)

### Features

* **api:** add daisyui styling ([548e1cd](https://github.com/markbeep/vvzapi/commit/548e1cde73f918e2cd0355a6b2fa135f88754628))
* **api:** add level, department, and language operators ([5f6275a](https://github.com/markbeep/vvzapi/commit/5f6275a7f5e7c6cc928b73f7f2247c59fd57daf5))
* **api:** add negation for all non-integer filter values as well ([5f6275a](https://github.com/markbeep/vvzapi/commit/5f6275a7f5e7c6cc928b73f7f2247c59fd57daf5))
* **api:** add opensearch spec ([6acabf4](https://github.com/markbeep/vvzapi/commit/6acabf4b5b373c16ff69ce845628c5e9e3cb6501))
* **api:** add ordering options to search ([548e1cd](https://github.com/markbeep/vvzapi/commit/548e1cde73f918e2cd0355a6b2fa135f88754628))

### Miscellaneous Chores

* **api:** minimize/zip html and format files ([e958db9](https://github.com/markbeep/vvzapi/commit/e958db9b20aabc9ad1909526d1190297ff633e64))

## [1.1.1](https://github.com/markbeep/vvzapi/compare/v1.1.0...v1.1.1) (2025-12-20)


### Bug Fixes

* **api:** translate fs/hs to correct semester ([3afa824](https://github.com/markbeep/vvzapi/commit/3afa8249f8aa6266775cbc8228b080d7c7c6eec5))

## [1.1.0](https://github.com/markbeep/vvzapi/compare/v1.0.0...v1.1.0) (2025-12-20)


### Features

* Search frontend with "poweruser" operators ([#35](https://github.com/markbeep/vvzapi/issues/35)) ([b2c3daf](https://github.com/markbeep/vvzapi/commit/b2c3daff3f78d01d71aca29e1928b5eb8a8fe2a4))


### Miscellaneous Chores

* remove mention of alpha in readme ([6d609d0](https://github.com/markbeep/vvzapi/commit/6d609d090d9724d71c4a4bc7a4089cf4b22f8db9))

## [1.0.0](https://github.com/markbeep/vvzapi/compare/v0.7.0-alpha...v1.0.0) (2025-11-05)


### ⚠ BREAKING CHANGES

* The /v0 endpoint has been removed

### Miscellaneous Chores

* update paths and readme to release v1.0.0. Closes [#32](https://github.com/markbeep/vvzapi/issues/32) ([910c778](https://github.com/markbeep/vvzapi/commit/910c778ee96e2d12e3eb1eea14ce8b981191db04))


### Code Refactoring

* **api:** replace third-party cache library with simple cache headers. Closes [#31](https://github.com/markbeep/vvzapi/issues/31) ([ff3f079](https://github.com/markbeep/vvzapi/commit/ff3f0793aa3b0ce00ebd711379dd8c9598889b8e))

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
