import httpx
from fastapi import HTTPException, status

from app.core.config import settings


class LineService:
    @staticmethod
    def verify_id_token(id_token: str) -> dict:
        mode = settings.LINE_VERIFY_MODE.lower().strip()
        if mode == "mock":
            return LineService._verify_mock_token(id_token)

        if mode == "real":
            return LineService._verify_real_token(id_token)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LINE_VERIFY_MODE must be 'mock' or 'real'",
        )

    @staticmethod
    def _verify_mock_token(id_token: str) -> dict:
        prefix = "mock-line-token-"
        if not id_token.startswith(prefix):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Line token invalid",
            )

        line_user_id = id_token.replace(prefix, "", 1).strip()
        if not line_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token payload",
            )

        return {
            "sub": line_user_id,
            "name": f"Mock User {line_user_id[-4:]}",
            "picture": "https://example.com/mock-profile.jpg",
        }

    @staticmethod
    def _verify_real_token(id_token: str) -> dict:
        if not settings.LINE_CHANNEL_ID:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LINE_CHANNEL_ID is not configured",
            )

        url = "https://api.line.me/oauth2/v2.1/verify"
        payload = {
            "id_token": id_token,
            "client_id": settings.LINE_CHANNEL_ID,
        }

        try:
            response = httpx.post(url, data=payload, timeout=10.0)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Line verify failed",
            ) from exc

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Line token invalid",
            )

        return response.json()