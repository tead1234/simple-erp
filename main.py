import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from app.infrastructure.database.session import init_db
from migrate import migrate
from app.infrastructure.logging.error_handlers import register_error_handlers
from app.infrastructure.backup.db_backup import create_backup, create_diagnostics_zip
from app.infrastructure.logging.logger import logger
from app.presentation.api.customers_router import router as customers_router
from app.presentation.api.sales_router import router as sales_router
from app.presentation.api.maintenance_router import router as maintenance_router
from app.presentation.api.settings_router import router as settings_router
from app.presentation.api.dashboard_router import router as dashboard_router
from app.presentation.api.fieldtrip_router import router as fieldtrip_router
from app.presentation.api.inventory_router import router as inventory_router
from app.presentation.api.estimate_router import router as estimate_router


async def _daily_backup():
    while True:
        await asyncio.sleep(86400)
        try:
            create_backup()
        except Exception as e:
            logger.error(json.dumps({"error_type": type(e).__name__, "message": str(e)}, ensure_ascii=False))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    migrate()
    asyncio.create_task(_daily_backup())
    yield


app = FastAPI(title="농기구 판매 ERP", lifespan=lifespan)
register_error_handlers(app)
app.include_router(customers_router)
app.include_router(sales_router)
app.include_router(maintenance_router)
app.include_router(settings_router)
app.include_router(dashboard_router)
app.include_router(fieldtrip_router)
app.include_router(inventory_router)
app.include_router(estimate_router)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


# 문제 발생 시 의뢰인이 로그+DB 덤프를 받아 전달할 수 있도록 하는 진단 다운로드
@app.get("/admin/diagnostics/download")
def download_diagnostics():
    from fastapi.responses import FileResponse as FR
    path = create_diagnostics_zip()
    return FR(str(path), filename=path.name, media_type="application/zip")
