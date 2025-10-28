from re import Pattern
from scrapy.http import Response
from parsel import Selector, SelectorList

from scraper.util.keymap import TranslationKey, translations


class Table:
    """
    Takes a page and throws all table rows into a list of (key, columns) tuples.
    """

    def __init__(
        self,
        response: Response | SelectorList[Selector] | Selector,
        /,
        pre_parsed: bool = False,
    ) -> None:
        self.response = response
        self.accessed_keys: set[str] = set()
        self.rows: list[tuple[str, SelectorList[Selector]]] = []
        if isinstance(response, Response):
            xpath_rows = response.xpath("//table/tbody/tr")
        else:
            if pre_parsed:
                if isinstance(response, SelectorList):
                    xpath_rows = response
                else:
                    xpath_rows = SelectorList([response])
            else:
                xpath_rows = response.xpath(".//tr")
        for r in xpath_rows:
            cols = r.xpath("./td")
            if len(cols) == 0:
                continue
            key = cols[0].xpath("string()").get()
            if key:
                key = key.replace("\xa0", "").strip()
            else:
                key = "unkeyed"
            self.rows.append((key, SelectorList(cols)))

    def find(
        self,
        table_key: TranslationKey,
        /,
        rows: list[tuple[str, SelectorList[Selector]]] | None = None,
    ) -> SelectorList[Selector] | None:
        translation = translations[table_key]
        if rows is None:
            rows = self.rows
        for key, cols in rows:
            if translation.de in key or translation.en in key:
                self.accessed_keys.add(key)  # keep track of what we accessed
                return cols
        return None

    def find_last(self, table_key: TranslationKey) -> SelectorList[Selector] | None:
        return self.find(table_key, list(reversed(self.rows)))

    def find_all(self, table_key: TranslationKey) -> list[SelectorList[Selector]]:
        translation = translations[table_key]
        found: list[SelectorList[Selector]] = []
        for key, cols in self.rows:
            if translation.de in key or translation.en in key:
                self.accessed_keys.add(key)  # keep track of what we accessed
                found.append(cols)
        return found

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


def table_under_header(response: Response, table_header_variants: list[str]) -> Table:
    ors = " or ".join(
        [f'contains(text(), "{header}")' for header in table_header_variants]
    )
    table = response.xpath(f"//h3[{ors}]/following-sibling::table[1]")

    return Table(table)
