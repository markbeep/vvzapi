from collections import defaultdict
from re import Pattern
from typing import Annotated, DefaultDict
from pydantic import BaseModel, Field
from scrapy.http import Response
from scrapy.selector.unified import SelectorList
from parsel import Selector

from scraper.util.keymap import TranslationKey, get_key, translations


class Table:
    def __init__(self, response: Response) -> None:
        self.response = response
        self.accessed_keys = set()

        xpath_rows = response.xpath("//table/tbody/tr")
        self.rows: list[tuple[str, SelectorList]] = []
        for r in xpath_rows:
            cols = r.xpath("./td")
            if len(cols) == 0:
                continue
            key = cols[0].xpath("string()").get()
            if not key:
                continue
            key = key.replace("\xa0", "").strip()
            self.rows.append((key, SelectorList(cols)))

    def find(
        self,
        table_key: TranslationKey,
        /,
        rows: list[tuple[str, SelectorList]] | None = None,
    ) -> SelectorList | None:
        translation = translations[table_key]
        if rows is None:
            rows = self.rows
        for key, cols in rows:
            if translation.de in key or translation.en in key:
                self.accessed_keys.add(key)  # keep track of what we accessed
                return cols
        return None

    def find_last(self, table_key: TranslationKey) -> SelectorList | None:
        return self.find(table_key, list(reversed(self.rows)))

    def get_texts(self, table_key: TranslationKey) -> list[str]:
        cols = self.find(table_key)
        if cols is None:
            return []
        return [x.replace("\xa0", " ").strip() for x in cols[1:].css("::text").getall()]

    def re(self, table_key: TranslationKey, pattern: str | Pattern[str]) -> list[str]:
        cols = self.find(table_key)
        if cols is None:
            return []
        return cols[1:].re(pattern)

    def re_first(
        self, table_key: TranslationKey, pattern: str | Pattern[str]
    ) -> str | None:
        cols = self.find(table_key)
        if cols is None:
            return None
        return cols[1:].re_first(pattern)

    def keys(self) -> list[str]:
        return [key for key, _ in self.rows]


class TableExtractor:
    def __init__(self, response: Response, table_header_variants: list[str]) -> None:
        self.response = response
        ors = " or ".join(
            [f'contains(text(), "{header}")' for header in table_header_variants]
        )
        self.table = response.xpath(f"//h3[{ors}]/following-sibling::table[1]")

    def get_parts(self) -> list["TablePart"]:
        # Split table rows at elements containing td with img.
        # Allows us to split the Performance assessment category if it has multiple sections.
        performance_rows: list[list[Selector]] = []
        current_section: list[Selector] = []

        for row in self.table.xpath(".//tr"):
            # Check if this row contains a td with an img
            has_img = row.xpath(".//td//img").get() is not None

            if has_img and current_section:
                performance_rows.append(current_section)
                current_section = [row]
            else:
                current_section.append(row)

        if current_section:
            performance_rows.append(current_section)

        return [TablePart(SelectorList(rows)) for rows in performance_rows]


class Cell:
    def __init__(self, cells: list[Selector] = []) -> None:
        self.cells = SelectorList(cells)

    def text(self) -> str | None:
        if len(self.cells) == 0:
            return None
        text = self.cells.css("::text").get()
        if not text:
            return None
        return text.replace("\xa0", " ").strip()

    def texts(self) -> list[str]:
        return [
            x.replace("\xa0", " ").strip() for x in self.cells.css("::text").getall()
        ]

    def credit(self) -> float | None:
        text = self.cells.css("::text").get()
        if not text:
            return None
        text = text.split("\xa0")[0]
        return float(text)

    def re(self, pattern: str | Pattern[str]) -> list[str]:
        return self.cells.re(pattern)


class TableRows(BaseModel):
    one: DefaultDict[TranslationKey, Annotated[Cell, Field(default_factory=Cell)]] = (
        defaultdict(Cell)
    )
    two: DefaultDict[TranslationKey, Annotated[Cell, Field(default_factory=Cell)]] = (
        defaultdict(Cell)
    )
    three: DefaultDict[TranslationKey, Annotated[Cell, Field(default_factory=Cell)]] = (
        defaultdict(Cell)
    )
    four: DefaultDict[TranslationKey, Annotated[Cell, Field(default_factory=Cell)]] = (
        defaultdict(Cell)
    )
    others: list[Cell] = []

    class Config:
        arbitrary_types_allowed = True


class TablePart:
    def __init__(self, table: SelectorList) -> None:
        self.table = table

    def extend(self, *others: "TablePart") -> "TablePart":
        all_rows = []
        for part in (self, *others):
            all_rows.extend(part.table)
        return TablePart(SelectorList(all_rows))

    def get_rows(self) -> TableRows:
        """Returns a mapping of keys to cells for each column count."""
        one: defaultdict[TranslationKey, Cell] = defaultdict(Cell)
        two: defaultdict[TranslationKey, Cell] = defaultdict(Cell)
        three: defaultdict[TranslationKey, Cell] = defaultdict(Cell)
        four: defaultdict[TranslationKey, Cell] = defaultdict(Cell)
        # unknown keys
        others: list[Cell] = []

        for row in self.table.css("tr"):
            columns = row.css("td")
            if len(columns) < 1:  # headers
                continue
            key = columns[0].css("::text").get()
            if not key:
                continue
            key = key.replace("\xa0", " ").strip().rstrip(":")
            key = get_key(key)

            if key == "other":
                others.append(Cell(columns[0 : len(columns)]))
            elif len(columns) == 1:
                one[key] = Cell([columns[0]])
            else:
                two[key] = Cell(columns[1 : len(columns)])

        return TableRows(one=one, two=two, three=three, four=four, others=others)
