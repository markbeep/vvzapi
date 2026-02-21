# Changelog

## [1.10.2](https://github.com/markbeep/vvzapi/compare/v1.10.1...v1.10.2) (2026-02-21)


### ⚠ BREAKING CHANGES

* The /v0 endpoint has been removed
* Requires old database to be deleted.
* remove foreign keys for more efficient way of adding items to DB
Merged migrations, requires database to be deleted

### Features

* add exam type filter ([03baace](https://github.com/markbeep/vvzapi/commit/03baacecd35a80ba3b3d250176e6cf6b5f86ca95))
* add info for amount of scraped lecturers ([12ef9e3](https://github.com/markbeep/vvzapi/commit/12ef9e3dab9c28dcb1c0005279512bdb46964e5a))
* add request url logs to get redirect information ([21f7839](https://github.com/markbeep/vvzapi/commit/21f7839f23a0a8f48d691872b520aad9be73b351))
* Add scraped_at timestamps to main models. Closes [#3](https://github.com/markbeep/vvzapi/issues/3) ([20f511f](https://github.com/markbeep/vvzapi/commit/20f511f983d7030c30b360f3c83ac9f4b5741d85))
* add sitemap ([ae0afb0](https://github.com/markbeep/vvzapi/commit/ae0afb030c469a1e2ba1bf161e43811cc1768122))
* add system to track if all units of a semester have been added ([e2262a0](https://github.com/markbeep/vvzapi/commit/e2262a09eb2224d8483d5c1657abcd99c7724753))
* added new signup closing time for group signups ([e2262a0](https://github.com/markbeep/vvzapi/commit/e2262a09eb2224d8483d5c1657abcd99c7724753))
* **api:** add courses and lecturers to unit details page ([4faf15b](https://github.com/markbeep/vvzapi/commit/4faf15b1b9816cdf9d0f114dacfd5d1a51e6e320))
* **api:** add daisyui styling ([548e1cd](https://github.com/markbeep/vvzapi/commit/548e1cde73f918e2cd0355a6b2fa135f88754628))
* **api:** add endpoints to retrieve sections and lecturers from units ([dcdd3a6](https://github.com/markbeep/vvzapi/commit/dcdd3a6ca9e84e21796cfed948125c9429310c6f))
* **api:** add level, deparment, and language operators ([5f6275a](https://github.com/markbeep/vvzapi/commit/5f6275a7f5e7c6cc928b73f7f2247c59fd57daf5))
* **api:** add negation for all non-integer filter values as well ([5f6275a](https://github.com/markbeep/vvzapi/commit/5f6275a7f5e7c6cc928b73f7f2247c59fd57daf5))
* **api:** add offered in details and search filter ([8fc98fc](https://github.com/markbeep/vvzapi/commit/8fc98fc352fdc5b014801cef33514c0c33c2cc99))
* **api:** add opensearch spec ([6acabf4](https://github.com/markbeep/vvzapi/commit/6acabf4b5b373c16ff69ce845628c5e9e3cb6501))
* **api:** add OpenTelemetry for more detailed traces ([ab5d27e](https://github.com/markbeep/vvzapi/commit/ab5d27e0c31951abd92d75edb4b59c8e32b9f367))
* **api:** add ordering options to search ([548e1cd](https://github.com/markbeep/vvzapi/commit/548e1cde73f918e2cd0355a6b2fa135f88754628))
* **api:** add unit-changes endpoint using unit ID ([e8cbf31](https://github.com/markbeep/vvzapi/commit/e8cbf311b72fe0428bfaf733a7bfd2db404498ab))
* **api:** add vvz filters to unit endpoint. Closes [#29](https://github.com/markbeep/vvzapi/issues/29) ([1ed9d84](https://github.com/markbeep/vvzapi/commit/1ed9d8452c73f5b175603acebef2aef8cbf5ee8b))
* **api:** Add VVZ-like alphabetical sort to sections. Closes [#26](https://github.com/markbeep/vvzapi/issues/26). Closes [#30](https://github.com/markbeep/vvzapi/issues/30). ([44c0dce](https://github.com/markbeep/vvzapi/commit/44c0dce2a68f6e6710fd8cefa9487484768d71b6))
* **api:** change semester/year of a unit while on details page ([5040463](https://github.com/markbeep/vvzapi/commit/5040463736b132659e1e6852e4bc73e99f81dcca))
* **api:** data dump endpoint to download database. Closes [#27](https://github.com/markbeep/vvzapi/issues/27) ([cb62114](https://github.com/markbeep/vvzapi/commit/cb62114741038240efb80eb7e78f3480249dbf69))
* **api:** enable CORS ([ff61a23](https://github.com/markbeep/vvzapi/commit/ff61a231fc5a0e7c707a699302f67b335aba7106))
* **api:** fetch coursereview score when visiting a unit page ([87d0302](https://github.com/markbeep/vvzapi/commit/87d0302313cfed00e3c4fbca40e8888928a0f755))
* **api:** group together the same course by number ([2df51f7](https://github.com/markbeep/vvzapi/commit/2df51f755afec6e2a28f687d3f720b6840182f2d))
* **api:** offered in filters are now all matched against a single path of sections instead of against arbitrary matching sections ([e6e47b1](https://github.com/markbeep/vvzapi/commit/e6e47b1c76f50c002a98fc01b31b3e8d221b7ac8))
* **api:** show filters that got applied when searching ([09a1cf7](https://github.com/markbeep/vvzapi/commit/09a1cf7e32f395f82e1c23b824a675e39122609b))
* halve the total amount of requests. Closes [#6](https://github.com/markbeep/vvzapi/issues/6) ([df82dc4](https://github.com/markbeep/vvzapi/commit/df82dc4c30c8d722b668918928d1df74de9ab58e))
* keep track of keys that change ([#11](https://github.com/markbeep/vvzapi/issues/11)) ([82a929f](https://github.com/markbeep/vvzapi/commit/82a929f4ea30839c3c43bf93602bfec4b0a2d022))
* **scraper:** add lecturer title and department ([30b591b](https://github.com/markbeep/vvzapi/commit/30b591b55ac8799a3183c474de1ff253cdf357c0))
* **scraper:** rescrape latest semesters. Closes [#5](https://github.com/markbeep/vvzapi/issues/5) ([95345ed](https://github.com/markbeep/vvzapi/commit/95345ed7bf94926386622704a5f01f2e0c02d2de))
* **scraper:** scrape course review ratings ([16a66bf](https://github.com/markbeep/vvzapi/commit/16a66bf487cd31ac7ae0010e13c90b6cf854ae78))
* Search frontend with "poweruser" operators ([#35](https://github.com/markbeep/vvzapi/issues/35)) ([b2c3daf](https://github.com/markbeep/vvzapi/commit/b2c3daff3f78d01d71aca29e1928b5eb8a8fe2a4))
* **search:** add animated search placeholders on root page ([a765f14](https://github.com/markbeep/vvzapi/commit/a765f14fc4788ce35b8f25cc465c127ead992874))
* **search:** add compact mode for viewing search results ([b87c342](https://github.com/markbeep/vvzapi/commit/b87c342d5dd734aee252c962c7904433290257e2))
* **search:** add coursereview operator to query by average rating ([5151c8e](https://github.com/markbeep/vvzapi/commit/5151c8e62d16d2215c1c786e1627258a2f9043df))
* **search:** add link anchors to guide page ([efa91cc](https://github.com/markbeep/vvzapi/commit/efa91cc1750d579496a65e1acf44c903cb685639))
* **search:** add notice when viewing out-of-date units ([c7cfddc](https://github.com/markbeep/vvzapi/commit/c7cfddc943a90f41f7fa4321f648a8f2682add68))
* **search:** add query time to results ([c9378cf](https://github.com/markbeep/vvzapi/commit/c9378cfd836f0676e1a08d862a325391e85cda1a))
* **search:** allow querying by lecturer by clicking on name on unit page ([1ea359b](https://github.com/markbeep/vvzapi/commit/1ea359ba1d5540e1f27f94370f84cfb54bff4257))
* **search:** make external links more clear with an icon ([42bc492](https://github.com/markbeep/vvzapi/commit/42bc4922845e28ae0ab30248bd34fab0d4adc170))
* **search:** match department on short acronym/name ([e2718d2](https://github.com/markbeep/vvzapi/commit/e2718d2c51cfcf6fb9b8b9ace65574e6ebcebf94))
* **search:** OR operator and parentheses for more complex queries ([45227ea](https://github.com/markbeep/vvzapi/commit/45227ea909ea3d8527b3c9052b567337cb0fcf2a))
* **search:** prefetch script on mousedown for anchor tags ([a2112d5](https://github.com/markbeep/vvzapi/commit/a2112d502fedda8e93f5e6f358075412bd8b7321))
* **search:** remove awkward '!:' operator and instead use prefixed minus operator for negation ([3c76208](https://github.com/markbeep/vvzapi/commit/3c76208dcc9b9d5d38b0281948f119e629f83cfd))
* **search:** show last scraped_at time on unit details page ([799c6f4](https://github.com/markbeep/vvzapi/commit/799c6f429975f5ae149f029fa7471d9ec333cafc))
* separated group timeslots into a new 'Group' model that also includes restrictions and group-specific course number ([e2262a0](https://github.com/markbeep/vvzapi/commit/e2262a09eb2224d8483d5c1657abcd99c7724753))
* split lecturers/examiners of units/courses into separate linked tables ([#7](https://github.com/markbeep/vvzapi/issues/7)) ([2ebf8dc](https://github.com/markbeep/vvzapi/commit/2ebf8dc03c99a3719164bf9ed859cbcd74e3c789))


### Bug Fixes

* add default value on scraped_at column ([1d926fd](https://github.com/markbeep/vvzapi/commit/1d926fd0203583047fd9f83cdfa1ac55decce4a6))
* Add unit_id to course composite PK (number+semkez isn't unique) ([20f511f](https://github.com/markbeep/vvzapi/commit/20f511f983d7030c30b360f3c83ac9f4b5741d85))
* allow for a unit to be in multiple departments ([b9bf043](https://github.com/markbeep/vvzapi/commit/b9bf043b96e4d11be6f4d218e97ff342f56c5df5))
* **api:** correctly link to coursereview ([9d06379](https://github.com/markbeep/vvzapi/commit/9d063795c4197190a00160053f87880bcf26cc40))
* **api:** correctly sort using department/level ([e1141f4](https://github.com/markbeep/vvzapi/commit/e1141f404edf2bf552c452bb79786e0033bf088f))
* **api:** display search and unit information in embed description ([6152a74](https://github.com/markbeep/vvzapi/commit/6152a74909695e01d1fd8a2c961aa209f3fb539a))
* **api:** fix crashing of unit pages if course hours are missing ([488491b](https://github.com/markbeep/vvzapi/commit/488491b4473bf95281e28aadbd25d9b511cbdce9))
* **api:** fix formatting on vvz/cr and results page links ([1d427ec](https://github.com/markbeep/vvzapi/commit/1d427ec980eb74f565f80fbee592528fbe2e1606))
* **api:** fix non-stacked elements not expanding correctly ([0c7704b](https://github.com/markbeep/vvzapi/commit/0c7704b18efca36b8bf8a63cd0159643996a2269))
* **api:** fix plausible event condition ([77655df](https://github.com/markbeep/vvzapi/commit/77655df00f87ddc1927d225e2b37c23943d4b9e6))
* **api:** fix wrong path in guide for first example ([80d6452](https://github.com/markbeep/vvzapi/commit/80d64528ba1679c389f85dc1c38845bd96ac7fc0))
* **api:** intersect offered in filters instead of unioning ([c2ba0e8](https://github.com/markbeep/vvzapi/commit/c2ba0e85bd6bb82c1f13417f0ac85aaa150ab850))
* **api:** keep track of search options across pages ([a34a9be](https://github.com/markbeep/vvzapi/commit/a34a9bebde47174ab0be3f0cfaf98394e2fed6b0))
* **api:** make periodicity value more clear on unit page ([d68ede3](https://github.com/markbeep/vvzapi/commit/d68ede3503e596031e72bcab3dc5c8547c135f85))
* **api:** remove empty examination/registration block if no information exists ([6152a74](https://github.com/markbeep/vvzapi/commit/6152a74909695e01d1fd8a2c961aa209f3fb539a))
* **api:** remove german title if it's the same as the english ([0c7704b](https://github.com/markbeep/vvzapi/commit/0c7704b18efca36b8bf8a63cd0159643996a2269))
* **api:** remove static path from api docs ([9bd84f2](https://github.com/markbeep/vvzapi/commit/9bd84f25c8a756e6b66c3617210092168da885d2))
* **api:** show short levels/departments with long title on hover ([d68ede3](https://github.com/markbeep/vvzapi/commit/d68ede3503e596031e72bcab3dc5c8547c135f85))
* **api:** title in search is not combined but instead each word is matched ([b9bf043](https://github.com/markbeep/vvzapi/commit/b9bf043b96e4d11be6f4d218e97ff342f56c5df5))
* **api:** translate fs/hs to correct semester ([3afa824](https://github.com/markbeep/vvzapi/commit/3afa8249f8aa6266775cbc8228b080d7c7c6eec5))
* **api:** wrap long links correctly ([f469251](https://github.com/markbeep/vvzapi/commit/f469251f1e2e45dfd44e4623f26a5751eee607c3))
* fix departments filter showing other departments ([03baace](https://github.com/markbeep/vvzapi/commit/03baacecd35a80ba3b3d250176e6cf6b5f86ca95))
* fix incorrect media type for static files ([65db758](https://github.com/markbeep/vvzapi/commit/65db758647d8f28d324e953f29ed016d1f30a88f))
* fix ints being read out as strings from json array ([ddfcacb](https://github.com/markbeep/vvzapi/commit/ddfcacb7d04bf88677fef456a96e12c095b968e1))
* handle course number with missing course type and support "by appt.". Closes [#13](https://github.com/markbeep/vvzapi/issues/13) ([6e60075](https://github.com/markbeep/vvzapi/commit/6e60075479a058597bf20738d4ce19ac2ea4fd14))
* ignore misleading key for occurence. Closes [#14](https://github.com/markbeep/vvzapi/issues/14) ([9261a4a](https://github.com/markbeep/vvzapi/commit/9261a4aac56900ba17565388a52e0926161a9cf8))
* log to stdout with scraper ([6bdb6f6](https://github.com/markbeep/vvzapi/commit/6bdb6f64675ca8b7a80a27adee6dcd1d2e2f5bba))
* main parse functions were not running. corrected the naming so that those are correctly executed ([e2262a0](https://github.com/markbeep/vvzapi/commit/e2262a09eb2224d8483d5c1657abcd99c7724753))
* move logs into file by default and show key-value pairs from log statement ([2bd524c](https://github.com/markbeep/vvzapi/commit/2bd524c04a57fbdd23eeda84512bed2544f8cc23))
* remove unique constraint on unit semkez/number. ([4e410c7](https://github.com/markbeep/vvzapi/commit/4e410c71e6ed6090df2a2d3c8b12ab5d25a91de7))
* **scraper:** allow for lecturers to not have a title ([119fbba](https://github.com/markbeep/vvzapi/commit/119fbbadad55b519c668b71518d6b31100dca14d))
* **scraper:** detect duplicate changes and update values instead of creating a new entry. Closes [#24](https://github.com/markbeep/vvzapi/issues/24) ([5ba6bcb](https://github.com/markbeep/vvzapi/commit/5ba6bcbba8d8e56f7b5c037a4bbe8366ed949c0f))
* **scraper:** keyerror when removing course id ([c24bf9a](https://github.com/markbeep/vvzapi/commit/c24bf9ab5edec1301d3b4c5acffe1a72a2fe7033))
* **scraper:** make exercise sessions where weekdays are missing get parsed correctly ([1f28faa](https://github.com/markbeep/vvzapi/commit/1f28faa0467196245d7d2b252ea2d87c3e236092))
* **scraper:** not rescraping correctly ([9043c0b](https://github.com/markbeep/vvzapi/commit/9043c0b77d7ac3414e2650d2aa9f3c8aab920dfa))
* **scraper:** Only rescrape the last relevant semesters. Closes [#22](https://github.com/markbeep/vvzapi/issues/22) ([fec3262](https://github.com/markbeep/vvzapi/commit/fec3262a1445fb0572bfd16b8609e4b059afc350))
* **scraper:** only scrape units from root page without filters to avoid duplicates ([742020c](https://github.com/markbeep/vvzapi/commit/742020ccfedbd50a4dd7c0ddb436716f749e594b))
* **scraper:** parse multiple courses without explicit weekdays correctly ([c63ccb7](https://github.com/markbeep/vvzapi/commit/c63ccb7f439446fa02012c96bd962310f33977df))
* **scraper:** parse shorter unit numbers like "17-412 1L" correctly ([8ec283e](https://github.com/markbeep/vvzapi/commit/8ec283e78cd6229bb5181d4c8c8ad95154fef66f))
* **search:** add cache busting to site CSS to circumvent cloudflare ([eb6df48](https://github.com/markbeep/vvzapi/commit/eb6df486fec3d09aeab2f164c080e3eb107de6d3))
* **search:** add cannonical link to unit pages leading to newest page ([9491f1a](https://github.com/markbeep/vvzapi/commit/9491f1a1102c6468948b60d99240ccaadbeba83b))
* **search:** add reference to favicon in header ([d2ff3bb](https://github.com/markbeep/vvzapi/commit/d2ff3bbbcd86fb19e00427149710dff7986e9a48))
* **search:** allow for utf8 letters in queries ([de17fb3](https://github.com/markbeep/vvzapi/commit/de17fb3d6cef4a5f480d11df8ce588f72c945b29))
* **search:** allow searches to be scraped according to robots.txt ([619df0d](https://github.com/markbeep/vvzapi/commit/619df0da0ee943e226548ae4d2828e9ce00a2013))
* **search:** escape title/description in header ([926800a](https://github.com/markbeep/vvzapi/commit/926800a2618c1e14173ca3e877abcc696eef86c2))
* **search:** fix course numbers not being matched by regex ([3c76208](https://github.com/markbeep/vvzapi/commit/3c76208dcc9b9d5d38b0281948f119e629f83cfd))
* **search:** fix offered in typo ([a38350d](https://github.com/markbeep/vvzapi/commit/a38350d3f2400c7269c3f66db58c52744a3fdd40))
* **search:** fix order of operator parsing to correctly match &gt;= and &lt;= ([4637d95](https://github.com/markbeep/vvzapi/commit/4637d95372a31eb14238b4ba3719dc30953b9aa2))
* **search:** fix query from becoming infinitely big and fix invalid offered in results page filters ([231d929](https://github.com/markbeep/vvzapi/commit/231d92972e4d2dffd15c9df873896cc3a762a568))
* **search:** fix robots.txt not being returned ([6c5fcf8](https://github.com/markbeep/vvzapi/commit/6c5fcf83fdc36de5319cdcd68dd76fc46866ba1e))
* **search:** fix search query not transferring over when visiting a unit ([d19f8a2](https://github.com/markbeep/vvzapi/commit/d19f8a2c8f427c36c42c19902c31031095fb57a4))
* **search:** fix tabbing index to skip stacked results in search page ([29d1bc2](https://github.com/markbeep/vvzapi/commit/29d1bc20a752dd8b14752a7cb23529165331df67))
* **search:** fix wrongly overflowing text about filter negation on guide page ([41db41e](https://github.com/markbeep/vvzapi/commit/41db41efa0656b556370d9d0eea49078c099a59b))
* Split floor and room into at most 2 values. Closes [#15](https://github.com/markbeep/vvzapi/issues/15) ([4d2e244](https://github.com/markbeep/vvzapi/commit/4d2e24427b581a673eaae68ce18a36290b6df4a2))
* vacuum db into separate file to prevent file corruption ([9d1fc6e](https://github.com/markbeep/vvzapi/commit/9d1fc6e1c349485d412120f6ede5622ef2f99711))


### Performance Improvements

* **api:** replace database acceses with async connections ([0abcfee](https://github.com/markbeep/vvzapi/commit/0abcfee64a507ce5604138721aeb7f5719616038))
* **search:** add async db access, resulting in over 4x req/s under heavy load ([05eeee4](https://github.com/markbeep/vvzapi/commit/05eeee41cf51a89d312816540be4f8e920ceb8a4))
* **search:** add db indices to improve performance on title/credits queries ([9d404d6](https://github.com/markbeep/vvzapi/commit/9d404d6205a8f9783f016df2b9f3dde077f67187))
* **search:** add fixi.js for lightweight DOM replacement when changing pages ([b960a1d](https://github.com/markbeep/vvzapi/commit/b960a1dde98745a48cce0ac6666c7d51aec68087))
* **search:** add materialized tables for section paths and departments ([05eeee4](https://github.com/markbeep/vvzapi/commit/05eeee41cf51a89d312816540be4f8e920ceb8a4))
* **search:** aggressively preload next page and search queries ([b960a1d](https://github.com/markbeep/vvzapi/commit/b960a1dde98745a48cce0ac6666c7d51aec68087))
* **search:** improve page load metrics ([e5f1db7](https://github.com/markbeep/vvzapi/commit/e5f1db74df52d16b1cd50b0caad16146a68b8cf6))
* **search:** improve search query performance by splitting it into two concurrent queries ([aaa40e0](https://github.com/markbeep/vvzapi/commit/aaa40e07e48678beb084e1af45aa8ee2474cfc4c))


### Dependencies

* update dependencies for python 3.14 compatibility ([f5bf30e](https://github.com/markbeep/vvzapi/commit/f5bf30ea2628288674f7ddbe5e5d9a44328b8843))
* update python to 3.14 ([ab908d9](https://github.com/markbeep/vvzapi/commit/ab908d90cbb283bf306244d7d952fa828f3e1536))


### Reverts

* "feat(search): show last scraped_at time on unit details page" ([d59c37c](https://github.com/markbeep/vvzapi/commit/d59c37cef664f29fdc7c19757c7fd4cb277ac999))


### Documentation

* add terms of use for clarity ([2f870f5](https://github.com/markbeep/vvzapi/commit/2f870f515805068e1252970f7e75d2c99eaceb0c))
* added readme banner ([e3b9aab](https://github.com/markbeep/vvzapi/commit/e3b9aab7292bb3ef07ad57d1f825fb499c1754a5))
* update readme with model name explanation and details on how to contribute ([cb62114](https://github.com/markbeep/vvzapi/commit/cb62114741038240efb80eb7e78f3480249dbf69))


### Styles

* **api:** change to a blue theme for search ([a8ff8ca](https://github.com/markbeep/vvzapi/commit/a8ff8cabea29f6fd1fd80b42b456d2ace5c49e5d))


### Miscellaneous Chores

* add back warnings for basedpyright ([05906df](https://github.com/markbeep/vvzapi/commit/05906df9900bf2e9a1d0d399680a53ad9f5830be))
* add example commands for how to solely scrape lecturers ([1b6242a](https://github.com/markbeep/vvzapi/commit/1b6242a3faa9844f593cccc49c6b081c4db9f9f7))
* add GPLv3 license ([ff6c5b1](https://github.com/markbeep/vvzapi/commit/ff6c5b136d1f0985624ac1bbb3fdca83fc7c7133))
* add jj to devcontainer ([cc9483e](https://github.com/markbeep/vvzapi/commit/cc9483e1f97c91da4dd5e127a09e45cae5c96bf6))
* add justfile for local development ([625f501](https://github.com/markbeep/vvzapi/commit/625f50153d88d57ce8dfc000a755e007cab0bc00))
* add k6 for benchmarking the website ([aa4bafd](https://github.com/markbeep/vvzapi/commit/aa4bafd5ad27462d451fad54df720ca3d89ba924))
* add pyright type checking ([0daa45f](https://github.com/markbeep/vvzapi/commit/0daa45f66ea8b5459070a49701018ee4ccf448f3))
* add release-please ([e1bcd90](https://github.com/markbeep/vvzapi/commit/e1bcd90ada9f37003a5d7d6ad9a789a59a10a45f))
* **api:** add influxdb support for more detailed analytics ([99417b9](https://github.com/markbeep/vvzapi/commit/99417b95189c0fa1486cbb7a8fb72fe336e2a024))
* **api:** minimize/zip html and format files ([e958db9](https://github.com/markbeep/vvzapi/commit/e958db9b20aabc9ad1909526d1190297ff633e64))
* **api:** prometheus endpoint for gathering metrics ([2b0543d](https://github.com/markbeep/vvzapi/commit/2b0543d3967bcd29cbb9b66084c913eed52c4569))
* **api:** send more info to plausible ([d810e07](https://github.com/markbeep/vvzapi/commit/d810e0788c617931dc08d0ac6c1d9627c9e4d03a))
* change to strict pyright typing. Closes [#17](https://github.com/markbeep/vvzapi/issues/17) ([127de96](https://github.com/markbeep/vvzapi/commit/127de967bf9ffd1a2dd21a7cb2c6f802a6b8884d))
* finished scraping 2023S/2022W ([1205ee7](https://github.com/markbeep/vvzapi/commit/1205ee7e7740c905ebfdca47348ad99b5e0a1e8b))
* install arm tools in devcontainer ([30b591b](https://github.com/markbeep/vvzapi/commit/30b591b55ac8799a3183c474de1ff253cdf357c0))
* **main:** release 0.2.0-alpha ([#2](https://github.com/markbeep/vvzapi/issues/2)) ([d418f68](https://github.com/markbeep/vvzapi/commit/d418f684786f7cf2f7474f09059e32b4e30c9562))
* **main:** release 0.2.1-alpha ([#9](https://github.com/markbeep/vvzapi/issues/9)) ([8720c46](https://github.com/markbeep/vvzapi/commit/8720c46797a80d871d8fffebf479f32d96491bca))
* **main:** release 0.3.0-alpha ([#10](https://github.com/markbeep/vvzapi/issues/10)) ([2e73e28](https://github.com/markbeep/vvzapi/commit/2e73e281d0c122158f32489c0e6de5374454a4fe))
* **main:** release 0.4.0-alpha ([#18](https://github.com/markbeep/vvzapi/issues/18)) ([fe3689e](https://github.com/markbeep/vvzapi/commit/fe3689edfb39403d9a46e1858622e139b7f0d383))
* **main:** release 0.5.0-alpha ([#19](https://github.com/markbeep/vvzapi/issues/19)) ([2f37ff9](https://github.com/markbeep/vvzapi/commit/2f37ff92d7399892d0eeb1adda6d295d664c9137))
* **main:** release 0.6.0-alpha ([#21](https://github.com/markbeep/vvzapi/issues/21)) ([d7c201f](https://github.com/markbeep/vvzapi/commit/d7c201fed6a128ea7dbb62d6e98a5c7460a170df))
* **main:** release 0.6.1-alpha ([#23](https://github.com/markbeep/vvzapi/issues/23)) ([a36cb99](https://github.com/markbeep/vvzapi/commit/a36cb995b81a59b4db9c4e110b38cb47a1037434))
* **main:** release 0.7.0-alpha ([#25](https://github.com/markbeep/vvzapi/issues/25)) ([75ede83](https://github.com/markbeep/vvzapi/commit/75ede838eab8f43736d19f18957329a045739589))
* **main:** release 1.0.0 ([#33](https://github.com/markbeep/vvzapi/issues/33)) ([e563cde](https://github.com/markbeep/vvzapi/commit/e563cde004097d24e1ddd8d195de52f792e038d7))
* **main:** release 1.1.0 ([#34](https://github.com/markbeep/vvzapi/issues/34)) ([d591c45](https://github.com/markbeep/vvzapi/commit/d591c45ff9a58f2cbea2a11f269d5a0129ca3a68))
* **main:** release 1.1.1 ([#37](https://github.com/markbeep/vvzapi/issues/37)) ([ccf88ea](https://github.com/markbeep/vvzapi/commit/ccf88ea7a9df16545d40c2afdd623e44aab0170f))
* **main:** release 1.1.2 ([#38](https://github.com/markbeep/vvzapi/issues/38)) ([367719a](https://github.com/markbeep/vvzapi/commit/367719ae372ea6a611a429ebc0cbfe9f404a31ae))
* **main:** release 1.1.3 ([#40](https://github.com/markbeep/vvzapi/issues/40)) ([17d4884](https://github.com/markbeep/vvzapi/commit/17d48846bafa5e2745593e84e7693c74c7c66605))
* **main:** release 1.10.0 ([#51](https://github.com/markbeep/vvzapi/issues/51)) ([510d557](https://github.com/markbeep/vvzapi/commit/510d5576ffffee02bd769156d02f6af338368c84))
* **main:** release 1.10.1 ([#52](https://github.com/markbeep/vvzapi/issues/52)) ([d527cca](https://github.com/markbeep/vvzapi/commit/d527cca85036bdc2fc1f8027cbba5898586d6827))
* **main:** release 1.2.0 ([#41](https://github.com/markbeep/vvzapi/issues/41)) ([f7d2cfa](https://github.com/markbeep/vvzapi/commit/f7d2cfab17b48186fd416111c587dd2e6901df3c))
* **main:** release 1.3.0 ([#42](https://github.com/markbeep/vvzapi/issues/42)) ([fb95803](https://github.com/markbeep/vvzapi/commit/fb958035625bf658b9f1be0bbb4bcba03a77b612))
* **main:** release 1.4.0 ([#43](https://github.com/markbeep/vvzapi/issues/43)) ([4feb9a0](https://github.com/markbeep/vvzapi/commit/4feb9a05a4371fca8ba3c46c15e3c7a05c1e4177))
* **main:** release 1.5.0 ([#44](https://github.com/markbeep/vvzapi/issues/44)) ([76df434](https://github.com/markbeep/vvzapi/commit/76df4341b76f178ec883c6d9daa1b9ab8e05b239))
* **main:** release 1.6.0 ([#45](https://github.com/markbeep/vvzapi/issues/45)) ([9bd0f36](https://github.com/markbeep/vvzapi/commit/9bd0f364a5a9a660f7a6d369b743c28baf25e118))
* **main:** release 1.7.0 ([#46](https://github.com/markbeep/vvzapi/issues/46)) ([e01b01e](https://github.com/markbeep/vvzapi/commit/e01b01e1c6d58722c45148d20de3edf871bfae4a))
* **main:** release 1.8.0 ([#47](https://github.com/markbeep/vvzapi/issues/47)) ([3ad6aed](https://github.com/markbeep/vvzapi/commit/3ad6aed720c5dbd6d79e3fc9dcb6a3e9a5f5354a))
* **main:** release 1.9.0 ([#50](https://github.com/markbeep/vvzapi/issues/50)) ([d99fbe0](https://github.com/markbeep/vvzapi/commit/d99fbe08b600e5b1cb792c96cd802a96c9925804))
* make parsing of enums from db more consistent with separate wrapper class ([d68ede3](https://github.com/markbeep/vvzapi/commit/d68ede3503e596031e72bcab3dc5c8547c135f85))
* move uv sync ahead of copy in dockerfiles ([2941916](https://github.com/markbeep/vvzapi/commit/29419166ba94fbd96c6ed644d74dc775a427c7f4))
* offload ideas from readme into gh issues ([ace17fd](https://github.com/markbeep/vvzapi/commit/ace17fd661763785125a5bad559722475ffc9c51))
* remove mention of alpha in readme ([6d609d0](https://github.com/markbeep/vvzapi/commit/6d609d090d9724d71c4a4bc7a4089cf4b22f8db9))
* remove network-mode:host from local devcontainer ([1d6d545](https://github.com/markbeep/vvzapi/commit/1d6d5459ec232d2d6a7c72a22e008b35c0248869))
* replace pyright type checking with ty ([06eb0ab](https://github.com/markbeep/vvzapi/commit/06eb0abc514cfe89bf3a29181fdc54ba7bb6f094))
* **search:** adjust the title/description metadata tags to more updated keywords ([915c510](https://github.com/markbeep/vvzapi/commit/915c510a6ad96b4c2b3212dd889d900e7847d1d7))
* **search:** make AND/OR operators lower-case in query information ([29d1bc2](https://github.com/markbeep/vvzapi/commit/29d1bc20a752dd8b14752a7cb23529165331df67))
* **search:** simplify plausible condition for analytics ([c39b422](https://github.com/markbeep/vvzapi/commit/c39b42255b7871785548738888df312a3af505df))
* **search:** update favicon to blue lines ([a4d4533](https://github.com/markbeep/vvzapi/commit/a4d4533d57cc300d3287ada22ed19857d0b01150))
* **search:** update index page description ([75e093b](https://github.com/markbeep/vvzapi/commit/75e093babc6d02d2038d52a45e21f124d7e457f5))
* set type checking mode to more strict "all" ([757bf6e](https://github.com/markbeep/vvzapi/commit/757bf6e0c1661e67fde9a951078cf1bee354e84e))
* test mise for local development ([652525f](https://github.com/markbeep/vvzapi/commit/652525fd73f95d760529dc3703ac9e9521abd294))
* update paths and readme to release v1.0.0. Closes [#32](https://github.com/markbeep/vvzapi/issues/32) ([910c778](https://github.com/markbeep/vvzapi/commit/910c778ee96e2d12e3eb1eea14ce8b981191db04))
* update semester status to be complete ([ae5bcff](https://github.com/markbeep/vvzapi/commit/ae5bcffc8e01b1c5b80ee3e2479c2b528077e9c5))


### Code Refactoring

* **api:** replace third-party cache library with simple cache headers. Closes [#31](https://github.com/markbeep/vvzapi/issues/31) ([ff3f079](https://github.com/markbeep/vvzapi/commit/ff3f0793aa3b0ce00ebd711379dd8c9598889b8e))
* more cleanly place all extracted links as LinkExtractor links ([0b6f2a4](https://github.com/markbeep/vvzapi/commit/0b6f2a48fadfb7b6b1eb57a92ef87984a71623a3))
* move all models into same file to better cross reference ([0daa45f](https://github.com/markbeep/vvzapi/commit/0daa45f66ea8b5459070a49701018ee4ccf448f3))
* remove foreign keys for more efficient way of adding items to DB ([2bd524c](https://github.com/markbeep/vvzapi/commit/2bd524c04a57fbdd23eeda84512bed2544f8cc23))
* rename "lectures" to "units" for consistency ([8daf0e9](https://github.com/markbeep/vvzapi/commit/8daf0e987e118aac7f6f79e1bc96eb189dbe75c9))
* **search:** switch to jinjax for templating and fix a few typing ([38395ff](https://github.com/markbeep/vvzapi/commit/38395ff98c85c8386445d8cc1e6fbb1cf3e5cbf5))
* shorten link extractor regex ([12ef9e3](https://github.com/markbeep/vvzapi/commit/12ef9e3dab9c28dcb1c0005279512bdb46964e5a))
* unified function for extracting timeslots for courses and groups ([e2262a0](https://github.com/markbeep/vvzapi/commit/e2262a09eb2224d8483d5c1657abcd99c7724753))


### Tests

* replace ty with pyrefly type checking ([ae0afb0](https://github.com/markbeep/vvzapi/commit/ae0afb030c469a1e2ba1bf161e43811cc1768122))
* **search:** benchmark search queries with k6s ([2535276](https://github.com/markbeep/vvzapi/commit/253527625b707bc8ae93c775b462ebf6fdaa5b92))


### Build System

* **api:** reduce docker image size by splitting the build steps ([11c64e0](https://github.com/markbeep/vvzapi/commit/11c64e02367e12fb422d87410cecf8eed00ad861))
* reduce scraper docker image size by removing uv from final step ([b688a53](https://github.com/markbeep/vvzapi/commit/b688a53c5824362b8682e5927f47907b9b47e8b5))


### Continuous Integration

* enable type/tests to run on pull requests ([99fde66](https://github.com/markbeep/vvzapi/commit/99fde666ebc52c6441a2a8d2ed1fa90bfc96c858))
* fix missing ruff formatter ([20194d3](https://github.com/markbeep/vvzapi/commit/20194d3ef9ffd830ca83fb30537fc5881738e6d4))
* increase basedpyright typing from 'recommended' to 'strict' ([af123b0](https://github.com/markbeep/vvzapi/commit/af123b009826ef6f14c859f086dd3e9042031dde))

## [1.10.1](https://github.com/markbeep/vvzapi/compare/v1.10.0...v1.10.1) (2026-02-20)


### Features

* **api:** add OpenTelemetry for more detailed traces ([ab5d27e](https://github.com/markbeep/vvzapi/commit/ab5d27e0c31951abd92d75edb4b59c8e32b9f367))


### Bug Fixes

* **api:** remove static path from api docs ([9bd84f2](https://github.com/markbeep/vvzapi/commit/9bd84f25c8a756e6b66c3617210092168da885d2))
* **search:** allow for utf8 letters in queries ([de17fb3](https://github.com/markbeep/vvzapi/commit/de17fb3d6cef4a5f480d11df8ce588f72c945b29))


### Performance Improvements

* **api:** replace database acceses with async connections ([99d59bc](https://github.com/markbeep/vvzapi/commit/99d59bc4ce03f7add53db14207767ad1f2405835))
* **search:** add async db access, resulting in over 4x req/s under heavy load ([05eeee4](https://github.com/markbeep/vvzapi/commit/05eeee41cf51a89d312816540be4f8e920ceb8a4))
* **search:** add db indices to improve performance on title/credits queries ([9d404d6](https://github.com/markbeep/vvzapi/commit/9d404d6205a8f9783f016df2b9f3dde077f67187))
* **search:** add materialized tables for section paths and departments ([05eeee4](https://github.com/markbeep/vvzapi/commit/05eeee41cf51a89d312816540be4f8e920ceb8a4))


### Miscellaneous Chores

* **search:** simplify plausible condition for analytics ([c39b422](https://github.com/markbeep/vvzapi/commit/c39b42255b7871785548738888df312a3af505df))


### Tests

* **search:** benchmark search queries with k6s ([2535276](https://github.com/markbeep/vvzapi/commit/253527625b707bc8ae93c775b462ebf6fdaa5b92))

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
