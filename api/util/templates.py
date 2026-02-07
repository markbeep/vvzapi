from pathlib import Path
from typing import Any, Mapping

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader
from jinja2_htmlmin import minify_loader
from jinja2_pluralize import pluralize_dj
from jinjax import Catalog
from jinjax.jinjax import JinjaX
from starlette.background import BackgroundTask

from api.util.version import get_api_version

templates_dir = Path("api") / "templates"

env = Environment(
    loader=minify_loader(
        FileSystemLoader(templates_dir),
        remove_comments=True,
        remove_empty_space=True,
        remove_all_empty_space=True,
        reduce_boolean_attributes=True,
    )
)
templates = Jinja2Templates(env=env)


def trim_float(value: float) -> int | float:
    if value % 1 == 0:
        return int(value)
    return round(value, 3)


templates.env.filters["pluralize"] = pluralize_dj  # pyright: ignore[reportUnknownMemberType]
templates.env.filters["trim_float"] = trim_float  # pyright: ignore[reportUnknownMemberType]
templates.env.globals["version"] = get_api_version()  # pyright: ignore[reportUnknownMemberType]


env.add_extension(JinjaX)
catalog = Catalog(jinja_env=env)
catalog.add_folder(templates_dir / "components")
catalog.add_folder(templates_dir / "pages")
catalog.add_folder(templates_dir / "layouts")


def catalog_response(
    name: str,
    status_code: int = 200,
    headers: Mapping[str, str] | None = None,
    media_type: str | None = None,
    background: BackgroundTask | None = None,
    **kwargs: Any,  # pyright: ignore[reportExplicitAny, reportAny]
):
    return HTMLResponse(
        catalog.render(name, **kwargs),  # pyright: ignore[reportAny]
        status_code=status_code,
        headers=headers,
        media_type=media_type,
        background=background,
    )
