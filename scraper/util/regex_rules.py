RE_NUMBER = r"\d{2,3}-\d{3,4}-?\w{0,2}[\xa0 \d\w]{0,4}"
"""
Number variations:
- 529-2002-02L (https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lerneinheitId=168203&semkez=2023S&ansicht=LEHRVERANSTALTUNGEN&lang=de)
- 101-0515-AAR
- 051-0135-0jL (https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lerneinheitId=26652&semkez=2005W&ansicht=LEHRVERANSTALTUNGEN&lang=de)
- 262-0201G
- 17-412 1L (https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lerneinheitId=13629&semkez=2003S&ansicht=LEHRVERANSTALTUNGEN&lang=de)
- 10-824 (https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lerneinheitId=6467&semkez=2003S&ansicht=LEHRVERANSTALTUNGEN&lang=de)
"""
RE_DATE = r"\d{2}\.\d{2}\.\d{4}"  # 31.12.2023
RE_SEMKEZ = r"semkez=(\w+)"
RE_UNITID = r"lerneinheitId=(\d+)"
RE_DOZIDE = r"dozide=(\d+)"
RE_ABSCHNITTID = r"abschnittId=(\d+)"
