import os
import traceback
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException


# 默认按教学/开发模式运行，便于排查问题；部署生产环境时设置 DEBUG_MODE=false。
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").strip().lower() in {"1", "true", "yes"}


def _debug_error_data(request: Request, exc: Exception) -> dict[str, Any] | None:
    """开发模式下整理异常诊断信息；生产模式不向客户端暴露内部细节。"""
    if not DEBUG_MODE:
        return None

    return {
        "error_type": type(exc).__name__,
        "error_detail": str(exc),
        "traceback": "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        ),
        "path": str(request.url),
    }


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """把主动抛出的 HTTP 异常统一包装成项目的 JSON 响应格式。"""
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            {
                "code": exc.status_code,
                "message": exc.detail,
                "data": None,
            }
        ),
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """统一处理请求体、路径参数和查询参数的校验错误。"""
    error_data: dict[str, Any] | None = None
    if DEBUG_MODE:
        # errors() 能指出具体字段和校验原因；通过 jsonable_encoder 确保可序列化。
        error_data = {
            "errors": jsonable_encoder(exc.errors()),
            "path": str(request.url),
        }

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "code": status.HTTP_400_BAD_REQUEST,
            "message": "请求参数校验失败",
            "data": error_data,
        },
    )


async def sqlalchemy_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """统一处理数据库异常；开发模式额外提供诊断信息。"""
    error_data = _debug_error_data(request, exc)
    if error_data is not None and isinstance(exc, IntegrityError):
        # 标出唯一键、外键等完整性约束异常，便于开发时定位数据冲突。
        error_data["error_type"] = "IntegrityError"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "数据库操作失败，请稍后重试",
            "data": error_data,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底处理未被其他处理器捕获的异常。"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "服务器内部错误",
            "data": _debug_error_data(request, exc),
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """将本模块的异常处理器注册到 FastAPI 应用。"""
    # StarletteHTTPException 也覆盖 FastAPI HTTPException 及框架生成的 404/405。
    app.add_exception_handler(StarletteHTTPException, http_exception_handler) # 业务
    app.add_exception_handler(RequestValidationError, validation_exception_handler) # 数据完整性约束
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler) # 数据库
    app.add_exception_handler(Exception, general_exception_handler) # 其他未被捕捉的错误
