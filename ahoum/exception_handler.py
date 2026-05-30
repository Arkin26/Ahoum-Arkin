import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, AuthenticationFailed, NotAuthenticated, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def _error(detail, code, status_code):
    return Response({"detail": detail, "code": code}, status=status_code)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        code = "error"
        detail = "An error occurred."

        if isinstance(exc, ValidationError):
            code = "validation_error"
            if isinstance(exc.detail, dict):
                first_key = next(iter(exc.detail))
                first_val = exc.detail[first_key]
                detail = first_val[0] if isinstance(first_val, list) else str(first_val)
            elif isinstance(exc.detail, list):
                detail = str(exc.detail[0])
            else:
                detail = str(exc.detail)
        elif isinstance(exc, AuthenticationFailed):
            code = "authentication_failed"
            detail = str(exc.detail)
        elif isinstance(exc, NotAuthenticated):
            code = "not_authenticated"
            detail = "Authentication credentials were not provided."
        elif isinstance(exc, APIException):
            code = exc.__class__.__name__.lower()
            detail = str(exc.detail) if not isinstance(exc.detail, list) else str(exc.detail[0])

        status_code = response.status_code
        if status_code == status.HTTP_403_FORBIDDEN:
            code = "permission_denied"
        elif status_code == status.HTTP_404_NOT_FOUND:
            code = "not_found"
        elif status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            code = "rate_limited"

        return _error(detail, code, status_code)

    if isinstance(exc, Http404):
        return _error("Resource not found.", "not_found", status.HTTP_404_NOT_FOUND)

    if isinstance(exc, PermissionDenied):
        return _error("Permission denied.", "permission_denied", status.HTTP_403_FORBIDDEN)

    logger.exception("Unhandled server error", exc_info=exc)
    return _error("An internal server error occurred.", "server_error", status.HTTP_500_INTERNAL_SERVER_ERROR)
