from fastapi import Request, status
from fastapi.responses import JSONResponse
from shared.exceptions.exceptions import BaseAPIException, ValidationError

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