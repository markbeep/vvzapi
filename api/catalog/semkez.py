def semkez_to_comparable(semkez: str) -> int:
    """Convert semkez to an integer for correct chronological comparison.

    W (winter/autumn) comes after S (spring) in the same year.
    Returns e.g. 2025S→20250, 2025W→20251, 2026S→20260, 2026W→20261.
    """
    year = int(semkez[:4])
    sem = 1 if semkez[4] == "W" else 0
    return year * 10 + sem
