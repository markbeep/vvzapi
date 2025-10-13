def create_progress(lowest: int, most: int, max_chars: int):
    percent = float(lowest) / float(most)
    return f"PROGRESS: {int(percent * max_chars) * '█':<{max_chars}} [ {lowest}/{most} | {round(100 * percent, 1)}% ]"
