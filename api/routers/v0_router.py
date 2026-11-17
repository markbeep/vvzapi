from fastapi import APIRouter

from api.search.router import router as search_router

router = APIRouter(prefix="/api/v0", tags=["Experimental"])

router.include_router(search_router)
