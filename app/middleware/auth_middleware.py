from datetime import datetime
from typing import Callable

import jwt
from fastapi import Request, Response, status
from fastapi.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, skip_paths: list[str] | None = None) -> None:
        super().__init__(app)
        self.skip_paths = skip_paths or []

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        if any(request.url.path.startswith(p) for p in self.skip_paths):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header",
            )

        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {exc}",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject",
            )
        request.state.user_id = user_id
        request.state.token_payload = payload

        response = await call_next(request)
        return response

    @staticmethod
    def get_user_from_state(request: Request) -> str:
        if not hasattr(request.state, "user_id"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated",
            )
        return request.state.user_id

    @staticmethod
    def get_token_payload(request: Request) -> dict:
        if not hasattr(request.state, "token_payload"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing",
            )
        return request.state.token_payload

    @classmethod
    def middleware(cls, app: ASGIApp, skip_paths: list[str] | None = None) -> BaseHTTPMiddleware:
        return cls(app, skip_paths=skip_paths)