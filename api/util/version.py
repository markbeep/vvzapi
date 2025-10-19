import toml

# get current version
with open("pyproject.toml", "r") as f:
    pyproject = toml.load(f)
    version = pyproject["project"]["version"]


def get_api_version() -> str:
    return version
