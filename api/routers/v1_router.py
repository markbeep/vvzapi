from fastapi import APIRouter
from api.routers.v1.units import router as unit_router
from api.routers.v1.misc import router as misc_router
from api.routers.v1.lecturers import router as lecturer_router
from api.routers.v1.courses import router as course_router
from api.routers.v1.sections import router as section_router

router = APIRouter(prefix="/v1")

router.include_router(unit_router)
router.include_router(misc_router)
router.include_router(lecturer_router)
router.include_router(course_router)
router.include_router(section_router)
