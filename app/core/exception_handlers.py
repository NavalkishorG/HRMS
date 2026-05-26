from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import error_payload


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        trace_id = getattr(request.state, 'trace_id', None)
        detail = exc.detail if isinstance(exc.detail, dict) else {'code': 'http_error', 'message': str(exc.detail)}
        return JSONResponse(error_payload(detail.get('code', 'http_error'), detail.get('message', 'Error'), trace_id), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        trace_id = getattr(request.state, 'trace_id', None)
        payload = error_payload('validation_error', 'Input validation failed', trace_id)
        payload['error']['details'] = exc.errors()
        return JSONResponse(payload, status_code=422)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        trace_id = getattr(request.state, 'trace_id', None)
        return JSONResponse(error_payload('internal_error', 'Unexpected server error', trace_id), status_code=500)
