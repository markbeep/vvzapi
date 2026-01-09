from fastapi import APIRouter

from api.routers.v2.dump import router as dump_router
from api.routers.v2.search import router as search_router

router = APIRouter(prefix="/api/v2")

router.include_router(dump_router)
router.include_router(search_router)
