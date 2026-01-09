from datetime import datetime
from pathlib import Path
import argparse
import re
from shutil import rmtree
import time
from typing import TypedDict, cast

import yaml


HTTP_CACHE_PATH = Path(".scrapy/httpcache")

re_units_en = r"https://www\.vvz\.ethz\.ch/Vorlesungsverzeichnis/lerneinheit\.view\?ansicht=ALLE&lang=en&lerneinheitId=\d+&semkez=\d{4}\w"
re_root_units = r"https://www\.vvz\.ethz\.ch/Vorlesungsverzeichnis/sucheLehrangebot\.view\?semkez=\d{4}\w&ansicht=2&seite=0(&deptId=\d+)?(&studiengangTyp=\w+)?&lang=\w\w"
re_legends = r"https://www\.vvz\.ethz\.ch/Vorlesungsverzeichnis/legendeStudienplanangaben\.view\?abschnittId=\d+&lang=en&semkez=\d{4}\w"

re_lecturers_root = r"https://www\.vvz\.ethz\.ch/Vorlesungsverzeichnis/sucheDozierende\.view\?lang=de&semkez=\d{4}\w&seite=0"


class FileMetadata(TypedDict):
    url: str
    timestamp: int


def get_files(path: Path):
    if not path.is_dir():
        return
    for top in path.iterdir():
        if top.is_dir():
            for bot in top.iterdir():
                if bot.is_dir():
                    meta = bot / "meta"
                    if not meta.exists():
                        yield "", bot, 0
                    with open(meta, "r") as f:
                        # yaml allows us to open the invalid formatted json file
                        data = cast(
                            FileMetadata,
                            yaml.load(f, Loader=yaml.SafeLoader),
                        )
                    yield data.get("url", ""), bot, data.get("timestamp", 0)


def cleanup_scrapy(
    dry_run: bool = False,
    delete_cached_semesters: list[str] | None = None,
    amount: int = 100,
    age_seconds: int = 0,
):
    if delete_cached_semesters is None:
        delete_cached_semesters = []

    unts, lecrs = 0, 0
    cached_unts = 0
    units = HTTP_CACHE_PATH / "units"
    lecturers = HTTP_CACHE_PATH / "lecturers"
    now = time.time()

    for url, dir, timestamp in get_files(units):
        dt = datetime.fromtimestamp(timestamp)
        # delete files that we do not use anymore
        if (
            not re.match(re_units_en, url)
            and not re.match(re_root_units, url)
            and not re.match(re_legends, url)
        ):
            print(f"Delete unit: {dir}: URL mismatch {url}: {dt}")
            unts += 1
            if not dry_run:
                rmtree(dir)
        # delete files from cached semesters
        if cached_unts < amount:
            for sem in delete_cached_semesters:
                if f"semkez={sem}" in url and (now - timestamp) > age_seconds:
                    print(f"Delete unit: {dir}: Cached semester {sem} {url}: {dt}")
                    unts += 1
                    cached_unts += 1
                    if not dry_run:
                        rmtree(dir)
                    break

    for url, dir, timestamp in get_files(lecturers):
        dt = datetime.fromtimestamp(timestamp)
        if not re.match(re_lecturers_root, url):
            print(f"Delete lecturer: {dir}: URL mismatch {url}: {dt}")
            lecrs += 1
            if not dry_run:
                rmtree(dir)

    print(
        f"===============\nDeleted {unts} files in lecturers dir\nDeleted {lecrs} files in lecturers dir"
    )


if __name__ == "__main__":

    class Arguments(argparse.Namespace):
        dry_run: bool
        delete_cached_semesters: list[str]
        amount: int
        age_seconds: int

    parser = argparse.ArgumentParser(description="Cleanup scrapy cache")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
        default=False,
    )
    parser.add_argument(
        "-d",
        "--delete-cached-semesters",
        nargs="+",
        help="List of semesters to delete from cache, e.g., 2023W 2024S",
        default=[],
    )
    parser.add_argument(
        "-n",
        "--amount",
        type=int,
        help="Amount of cached semesters to delete",
        default=100,
    )
    parser.add_argument(
        "--age-seconds",
        type=int,
        help="Delete cached files older than this many seconds",
        default=0,
    )
    parser.add_argument(
        "--age-seconds",
        type=int,
        help="Delete cached files older than this many seconds",
        default=0,
    )
    args = parser.parse_args(namespace=Arguments())
    cleanup_scrapy(
        dry_run=args.dry_run,
        delete_cached_semesters=args.delete_cached_semesters,
        amount=args.amount,
        age_seconds=args.age_seconds,
    )
