import json
from pathlib import Path
import argparse
import re
from shutil import rmtree

import yaml


CACHE_PATH = Path(".scrapy/httpcache")

re_lectures = r"https://www\.vvz\.ethz\.ch/Vorlesungsverzeichnis/lerneinheit\.view\?lerneinheitId=\d+?&semkez=\d{4}\w&ansicht=ALLE&lang=\w\w"
re_lectures_root = r"https://www\.vvz\.ethz\.ch/Vorlesungsverzeichnis/sucheLehrangebot\.view\?semkez=\d{4}\w&ansicht=1&seite=0"
re_lecturers_root = r"https://www\.vvz\.ethz\.ch/Vorlesungsverzeichnis/sucheDozierende\.view\?lang=de&semkez=\d{4}\w&seite=0"


def get_files(path: Path, dry_run: bool):
    if not path.is_dir():
        return
    for top in path.iterdir():
        if top.is_dir():
            for bot in top.iterdir():
                if bot.is_dir():
                    meta = bot / "meta"
                    if not meta.exists():
                        yield "", bot
                    with open(meta, "r") as f:
                        data = yaml.load(f, Loader=yaml.SafeLoader)
                    yield data.get("url", ""), bot


def cleanup_scrapy(dry_run: bool = False):
    unts, lecrs = 0, 0
    units = CACHE_PATH / "lectures"
    lecturers = CACHE_PATH / "lecturers"

    for url, dir in get_files(units, dry_run):
        if not re.match(re_lectures, url) and not re.match(re_lectures_root, url):
            print(f"Delete unit: {dir}: URL mismatch {url}")
            unts += 1
            if not dry_run:
                rmtree(dir)

    for url, dir in get_files(lecturers, dry_run):
        if not re.match(re_lecturers_root, url):
            print(f"Delete lecturer: {dir}: URL mismatch {url}")
            lecrs += 1
            if not dry_run:
                rmtree(dir)

    print(
        f"===============\nDeleted {unts} files in lecturers dir\nDeleted {lecrs} files in lecturers dir"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup scrapy cache")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
        default=False,
    )
    args = parser.parse_args()
    cleanup_scrapy(dry_run=args.dry_run)
