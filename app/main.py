from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from .config import settings
from .db import engine, SessionLocal, Base
from .routes.users import router as users_router
from .middleware.auth_middleware import AuthMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title="MCP DB Query Validator", version="1.0.0")

    @app.on_event("startup")
    async def startup():
        logging.info("Starting up: creating database tables")
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables created")

    @app.on_event("shutdown")
    async def shutdown():
        logging.info("Shutting down application")

    app.add_middleware(BaseHTTPMiddleware, dispatch=AuthMiddleware(app))
    app.include_router(users_router)

    return app


app = create_app()