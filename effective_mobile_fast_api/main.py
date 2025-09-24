import asyncio
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel

from effective_mobile_fast_api.api_v1 import router as router_v1
from effective_mobile_fast_api.api_v1.web.views import router as web_router
from effective_mobile_fast_api.core.config import settings
from effective_mobile_fast_api.core.models import db_helper
from effective_mobile_fast_api.middleware.middleware import auth_middleware

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Создание таблиц БД при запуске приложения"""
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield


app = FastAPI(
    title="Custom Authentication & Authorization System",
    description="Система аутентификации и авторизации (Access Control System)",
    version="1.0.0",
    lifespan=lifespan
)

# Подключаем middleware для аутентификации
app.middleware("http")(auth_middleware)

# Подключаем API роутеры
app.include_router(router_v1, prefix=settings.api_v1_prefix)

# Подключаем веб-роутеры
app.include_router(web_router)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="effective_mobile_fast_api/static"), name="static")


@app.get("/")
async def root():
    """Корневой endpoint с информацией о системе"""
    return {
        "message": "Custom Authentication & Authorization System",
        "version": "1.0.0",
        "docs": "/docs",
        "description": "Система аутентификации и авторизации (Access Control System)"
    }


if __name__ == '__main__':
    uvicorn.run("main:app", reload=True, host="0.0.0.0", port=8000)
