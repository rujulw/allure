from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_engine, init_engine
from app.routers.auth import router as auth_router
from app.routers.realtime import router as realtime_router
from app.realtime.manager import RealtimeManager
from app.table.manager import TableManager


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_engine()
    try:
        yield
    finally:
        await close_engine()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.table_manager = TableManager()
    app.state.realtime_manager = RealtimeManager(app.state.table_manager)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth_router)
    app.include_router(realtime_router)
    return app


app = create_app()
