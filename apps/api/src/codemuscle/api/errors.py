from fastapi import Request
from fastapi.responses import JSONResponse

from codemuscle.domain.exceptions import DomainError


async def domain_error_handler(_request: Request, error: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"error": {"code": error.code, "message": error.message, "details": error.details}},
    )
