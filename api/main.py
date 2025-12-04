from typing import Annotated, Any

from fastapi import Depends, FastAPI, Query, Request
from starlette.background import BackgroundTask
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    RedirectResponse,
    StreamingResponse,
)
from pathlib import Path
from fastapi.templating import Jinja2Templates
import httpx

from api.env import Settings
from api.routers.v1_router import router as v1_router
from api.routers.v2_router import router as v2_router
from api.routers.v2.search import search_units
from api.routers.v1.units import get_unit
from api.util.db import get_session
from api.util.version import get_api_version


app = FastAPI(title="VVZ API", version=get_api_version())
app.include_router(v1_router)
app.include_router(v2_router)


templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def send_analytics_event(request: Request):
    plausible_url = Settings().plausible_url
    if not plausible_url:
        return
    headers = {
        "Content-Type": "application/json",
        "User-Agent": request.headers.get("user-agent", "vvzapi"),
    }
    if request.client:
        headers["X-Forwarded-For"] = request.client.host

    httpx.post(
        plausible_url,
        json={
            "name": "pageview",
            "url": str(request.url),
            "domain": request.url.hostname,
        },
        headers=headers,
        timeout=10,
    )


@app.middleware("http")
async def analytics_middleware(request: Request, call_next: Any):
    response: StreamingResponse = await call_next(request)
    if (
        not Settings().plausible_url
        and not request.url.path.startswith("/api")
        and not request.url.path == "/"
        and not request.url.path.startswith("/docs")
    ):
        return response
    task = BackgroundTask(send_analytics_event, request)
    response.background = task

    if 200 <= response.status_code < 300:
        response.headers["Cache-Control"] = (
            f"Cache-Control: public, max-age={Settings().cache_expiry}"
        )
    return response


@app.get("/", include_in_schema=False)
async def root(
    session: Annotated[Any, Depends(get_session)],
    query: Annotated[str | None, Query(alias="q"), str] = None,
    page: int = 1,
):
    if not query:
        return templates.TemplateResponse(
            "root_search.html", {"request": {}, "version": get_api_version()}
        )

    results = await search_units(query, session)

    if results.total == 1:
        return RedirectResponse(f"/unit/{results.results[0].id}", status_code=303)

    return templates.TemplateResponse(
        "results.html",
        {
            "request": {},
            "version": get_api_version(),
            "query": query,
            "page": page,
            "results": results,
        },
    )


@app.get("/unit/{unit_id}", include_in_schema=False)
async def unit_detail(
    unit_id: int,
    session: Annotated[Any, Depends(get_session)],
):
    unit = await get_unit(unit_id, session)
    if not unit:  # TODO: redirect to 404 page once implemented
        return HTMLResponse(status_code=404)

    # lecturer_ids = await get_unit_lecturers(unit_id, session)
    courses = []
    lecturers = []

    return templates.TemplateResponse(
        "unit_detail.html",
        {
            "request": {},
            "version": get_api_version(),
            "unit": unit,
            "courses": courses,
            "lecturers": lecturers,
        },
    )


@app.get("/{favicon}", include_in_schema=False)
async def favicon(favicon: str):
    if favicon not in [
        "android-chrome-192x192.png",
        "android-chrome-512x512.png",
        "apple-touch-icon.png",
        "favicon-16x16.png",
        "favicon-32x32.png",
        "favicon.ico",
        "site.webmanifest",
    ]:
        return HTMLResponse(status_code=404)

    favicon_path = Path(__file__).parent / "static" / favicon
    if favicon_path.exists():
        return HTMLResponse(favicon_path.read_bytes(), media_type="image/x-icon")
    return HTMLResponse(status_code=404)


@app.get("/static/{file_path:path}", include_in_schema=False)
async def static_files(file_path: str):
    if file_path not in [
        "globals.css",
    ]:
        return HTMLResponse(status_code=404)
    static_path = Path(__file__).parent / "static" / file_path
    if static_path.exists():
        return FileResponse(static_path)
    return HTMLResponse(status_code=404)
