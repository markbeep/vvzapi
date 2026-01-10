# pyright: reportUntypedFunctionDecorator=false

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.env import Settings

router = APIRouter(prefix="/dump", tags=["Data Dump"])

limiter = Limiter(key_func=get_remote_address)


@router.get("")
@limiter.limit("2/minute")
def get_data_dump(request: Request):  # limiter requires request parameter
    """
    ## Data Dump Endpoint
    This downloads a ZIP file containing the entire sqlite3 database.

    Table structure, definition, and reasonings can be found in [models.py](https://github.com/markbeep/vvzapi/blob/main/api/models.py).

    **Note:** Access the `/api/vX/dump/metadata` endpoint to get the size and last modified value of the database dump
    to avoid downloading it unnecessarily.

    **Rate Limiting:** This endpoint is rate-limited to 2 requests per minute.
    """
    _ = request
    if not Path(Settings().zip_path).exists():
        raise HTTPException(status_code=404, detail="Data dump not found")
    return FileResponse(
        Settings().zip_path,
        media_type="application/zip",
        filename="database.zip",
        headers={
            "Cache-Control": f"public, max-age={Settings().sitemap_expiry}",
            "Etag": str(Path(Settings().zip_path).stat().st_mtime_ns),
        },
    )


class DatabaseMetadata(BaseModel):
    size_in_bytes: int
    last_modified_ms: int


@router.get("/metadata", response_model=DatabaseMetadata)
def get_data_dump_size() -> DatabaseMetadata:
    path = Path(Settings().zip_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Data dump not found")
    size_in_bytes = path.stat().st_size
    last_modified = path.stat().st_mtime_ns / 1e6  # ms
    return DatabaseMetadata(
        size_in_bytes=size_in_bytes,
        last_modified_ms=int(last_modified),
    )
