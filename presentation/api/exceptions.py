from fastapi import Request
from fastapi.responses import JSONResponse
from shared.exceptions.exceptions import BaseAPIException, ValidationError, NotFoundError, InternalServerError

async def base_exception_handler(request: Request, exc: BaseAPIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "type": exc.__class__.__name__
        }
    )


async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "type": "ValidationError"
        }
    )


async def not_found_exception_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "type": "NotFoundError"
        }
    )


async def internal_server_error_exception_handler(request: Request, exc: InternalServerError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "type": "InternalServerError"
        }
    )