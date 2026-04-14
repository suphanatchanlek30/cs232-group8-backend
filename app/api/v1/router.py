from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.liff_auth import router as liff_auth_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.public import router as public_router
from app.api.v1.reports import router as reports_router
from app.api.v1.staff_auth import router as staff_auth_router
from app.api.v1.tracking import router as tracking_router

api_router = APIRouter()
api_router.include_router(liff_auth_router, prefix="/liff/auth", tags=["LIFF Auth"])
api_router.include_router(staff_auth_router, prefix="/staff/auth", tags=["Staff Auth"])
api_router.include_router(public_router, prefix="/public", tags=["Public"])
api_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
api_router.include_router(tracking_router, prefix="/tracking", tags=["Tracking"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])