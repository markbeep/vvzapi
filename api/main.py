from typing import Any

from fastapi import FastAPI, Request
from starlette.background import BackgroundTask
from fastapi.responses import HTMLResponse, StreamingResponse
from pathlib import Path
from fastapi.templating import Jinja2Templates
import httpx

from api.env import Settings
from api.routers.v1_router import router as v0_router
from api.util.version import get_api_version


app = FastAPI(title="VVZ API", version=get_api_version())
app.include_router(v0_router)


_STATIC_INDEX = Path(__file__).parent / "static" / "index.html"
templates = Jinja2Templates(directory=str(_STATIC_INDEX.parent))


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


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    if not _STATIC_INDEX.exists():
        return HTMLResponse("<h1>VVZ API</h1>", status_code=200)

    return templates.TemplateResponse(
        "index.html", {"request": {}, "version": get_api_version()}
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
