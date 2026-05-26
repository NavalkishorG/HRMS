from datetime import datetime

from fastapi import HTTPException, status


class DomainError(HTTPException):
    def __init__(self, code: str, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail={'code': code, 'message': detail})


class ForbiddenError(DomainError):
    def __init__(self, detail: str = 'Forbidden'):
        super().__init__('forbidden', detail, status.HTTP_403_FORBIDDEN)


class NotFoundError(DomainError):
    def __init__(self, detail: str = 'Resource not found'):
        super().__init__('not_found', detail, status.HTTP_404_NOT_FOUND)


def error_payload(code: str, message: str, trace_id: str | None = None) -> dict:
    return {
        'error': {
            'code': code,
            'message': message,
            'trace_id': trace_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
    }
