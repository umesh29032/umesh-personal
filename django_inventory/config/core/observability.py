"""Request-ID correlation for logs (P0.4 observability) — no external service.

A short id is generated per HTTP request, stored in a contextvar, injected into
EVERY log record by RequestIDFilter, and echoed in the `X-Request-ID` response
header. So all log lines for one request share an id — `grep <id> logs/django.log`
reconstructs the request. Outside a request (management commands, startup) the id
is '-'. ContextVar is async/thread-safe, so this survives a future async move.
"""
import logging
import uuid
from contextvars import ContextVar

_request_id: ContextVar[str] = ContextVar('request_id', default='-')


def get_request_id() -> str:
    return _request_id.get()


class RequestIDFilter(logging.Filter):
    """Inject `request_id` onto every LogRecord so the formatter can render it."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id.get()
        return True


class RequestIDMiddleware:
    """Assign a request id (honour an inbound X-Request-ID, else generate one),
    bind it for the request's lifetime, and return it in the response header."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        rid = request.headers.get('X-Request-ID') or uuid.uuid4().hex[:12]
        token = _request_id.set(rid)
        try:
            response = self.get_response(request)
        finally:
            _request_id.reset(token)
        response['X-Request-ID'] = rid
        return response
