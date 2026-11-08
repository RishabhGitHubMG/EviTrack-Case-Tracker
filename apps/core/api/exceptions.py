import logging

from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, NotFound, PermissionDenied, Throttled, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


ERROR_CODES = {
    400: 'validation_error',
    401: 'not_authenticated',
    403: 'permission_denied',
    404: 'not_found',
    429: 'throttled',
}


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        logger.exception('Unhandled API exception', exc_info=exc)
        return Response(
            {
                'code': 'server_error',
                'message': 'The request could not be completed.',
                'fields': None,
                'retry_after': None,
            },
            status=500,
        )

    status_code = response.status_code
    code = ERROR_CODES.get(status_code, 'server_error')
    fields = None
    retry_after = getattr(exc, 'wait', None) if isinstance(exc, Throttled) else None

    if isinstance(exc, ValidationError):
        fields = response.data
        message = 'Please fix the highlighted fields.'
    elif isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        message = 'Authentication is required.'
    elif isinstance(exc, PermissionDenied):
        message = 'You do not have permission to perform this action.'
    elif isinstance(exc, NotFound):
        message = 'The requested item was not found.'
    elif isinstance(exc, Throttled):
        message = 'Request was throttled. Try again later.'
    else:
        detail = response.data.get('detail') if isinstance(response.data, dict) else None
        message = str(detail) if detail else 'The request could not be completed.'

    response.data = {
        'code': code,
        'message': message,
        'fields': fields,
        'retry_after': retry_after,
    }
    if isinstance(exc, Throttled):
        response.data['retry_after'] = int(retry_after) if retry_after is not None else None
    return response
