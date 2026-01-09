import toml

# get current version
with open("pyproject.toml", "r") as f:
    pyproject = toml.load(f)
    version = str(pyproject["project"]["version"])  # pyright: ignore[reportAny]


def get_api_version() -> str:
    return version
