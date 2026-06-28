import json
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.infrastructure.logging.logger import logger


def register_error_handlers(app: FastAPI):
    @app.exception_handler(Exception)
    async def _(request: Request, exc: Exception):
        logger.error(json.dumps({
            "error_type": type(exc).__name__,
            "message": str(exc),
            "context": {"method": request.method, "path": request.url.path},
            "traceback": traceback.format_exc(),
        }, ensure_ascii=False))
        return JSONResponse(status_code=500, content={"error": "서버 오류가 발생했습니다."})
