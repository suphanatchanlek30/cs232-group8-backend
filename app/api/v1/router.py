from fastapi import APIRouter

from app.api.v1.liff_auth import router as liff_auth_router
from app.api.v1.analytics import router as analytics_router

api_router = APIRouter()
api_router.include_router(liff_auth_router, prefix="/liff/auth", tags=["LIFF Auth"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])