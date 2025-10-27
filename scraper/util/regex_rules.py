RE_CODE = r"\d{3}-\d{4}-?\w{0,2}\xa0?\w?"
"""
- Standard: 262-0201-00L
- Slightly cursed: 101-0515-AAR
- Why: 262-0201G
"""
RE_DATE = r"\d{2}\.\d{2}\.\d{4}"  # 31.12.2023
RE_SEMKEZ = r"semkez=(\w+)"
RE_UNITID = r"lerneinheitId=(\d+)"
RE_DOZIDE = r"dozide=(\d+)"
RE_ABSCHNITTID = r"abschnittId=(\d+)"
