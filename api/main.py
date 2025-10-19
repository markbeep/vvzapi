from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from api.routers.v1_router import router as v1_router
from api.util.version import get_api_version


@asynccontextmanager
async def lifespan(_: FastAPI):
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(v1_router)


_STATIC_INDEX = Path(__file__).parent / "static" / "index.html"
templates = Jinja2Templates(directory=str(_STATIC_INDEX.parent))


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
