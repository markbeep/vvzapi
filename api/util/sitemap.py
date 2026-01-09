import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from sqlmodel import col, select

from api.models import LearningUnit
from api.util.db import get_session


def _parse_index(root: ET.Element) -> dict[str, datetime]:
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_data: dict[str, datetime] = {}

    for sitemap in root.findall("ns:sitemap", namespace):
        loc = sitemap.find("ns:loc", namespace)
        lastmod = sitemap.find("ns:lastmod", namespace)
        if loc is None or lastmod is None:
            continue
        loc_text = loc.text or ""
        lastmod_text = lastmod.text or ""

        match = re.search(r"sitemap-(\w+?)\.xml", loc_text)
        if match:
            semkez = match.group(1)
            try:
                dt = datetime.fromisoformat(lastmod_text)
            except ValueError:
                dt = datetime.strptime(lastmod_text, "%Y-%m-%d")

            sitemap_data[semkez] = dt

    return sitemap_data


def generate_sitemap(expiry_seconds: int | None = None) -> None:
    base_url = "https://vvzapi.ch"
    path = Path("api/static/sitemap")
    path.mkdir(parents=True, exist_ok=True)

    if (path / "sitemap.xml").exists():
        if expiry_seconds is not None:
            if (
                path / "sitemap.xml"
            ).lstat().st_mtime + expiry_seconds > datetime.now().timestamp():
                print("Sitemap is still fresh, skipping generation.")
                return
        with open(path / "sitemap.xml", "r", encoding="utf-8") as f:
            changes = _parse_index(ET.parse(f).getroot())
    else:
        changes: dict[str, datetime] = {}

    with next(get_session()) as session:
        semesters = session.exec(
            select(LearningUnit.semkez)
            .distinct()
            .order_by(col(LearningUnit.semkez).desc())
        ).all()

        print(f"Found {len(semesters)} semesters for sitemap generation.")
        sitemap_header = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'

        for semkez in semesters:
            print(f"Generating sitemap for semester {semkez}...")

            latest_change = session.exec(
                select(LearningUnit.scraped_at)
                .where(LearningUnit.semkez == semkez)
                .order_by(col(LearningUnit.scraped_at).desc())
            ).first()
            if latest_change is None:
                print(f"  No units found for semester {semkez}, skipping...")
                continue
            changes_dt = datetime.fromtimestamp(latest_change)
            changes_dt = changes_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            previous = changes.get(semkez)
            if previous and changes_dt <= previous:
                print(f"  No changes since last generation, skipping {semkez}...")
                continue

            units = session.exec(
                select(LearningUnit.id, LearningUnit.scraped_at)
                .where(LearningUnit.semkez == semkez)
                .order_by(col(LearningUnit.id).asc())
            ).all()

            print(f"  Found {len(units)} units for semester {semkez}.")

            sem_sitemap_path = path / f"sitemap-{semkez}.xml"
            if sem_sitemap_path.exists():
                sem_sitemap_path.unlink()
            with open(sem_sitemap_path, "a", encoding="utf-8") as sem_f:
                sem_f.write(sitemap_header + "\n")
                for id, scraped_at in units:
                    dt = datetime.fromtimestamp(scraped_at).strftime("%Y-%m-%d")
                    sem_f.write(
                        f"<url><loc>{base_url}/unit/{id}</loc><lastmod>{dt}</lastmod></url>\n"
                    )
                sem_f.write("</urlset>")

            changes[semkez] = changes_dt
            print(f"  Sitemap for semester {semkez} generated.")

    # Generate sitemap index
    print("Generating sitemap index...")
    with open(path / "sitemap.xml", "w", encoding="utf-8") as index_f:
        index_f.write(
            '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        )
        for semkez, lastmod_dt in changes.items():
            index_f.write(
                f"<sitemap><loc>{base_url}/sitemap/sitemap-{semkez}.xml</loc><lastmod>{lastmod_dt.strftime('%Y-%m-%d')}</lastmod></sitemap>\n"
            )
        index_f.write("</sitemapindex>")

    print("Sitemap index generated.")


if __name__ == "__main__":
    generate_sitemap(3600)
