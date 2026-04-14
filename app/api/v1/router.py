from fastapi import APIRouter

from app.api.v1.liff_auth import router as liff_auth_router
from app.api.v1.staff_auth import router as staff_auth_router

api_router = APIRouter()
api_router.include_router(liff_auth_router, prefix="/liff/auth", tags=["LIFF Auth"])
api_router.include_router(staff_auth_router, prefix="/staff/auth", tags=["Staff Auth"])