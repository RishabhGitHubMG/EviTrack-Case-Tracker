from django.http import JsonResponse
from django.views.csrf import csrf_failure as django_csrf_failure


def csrf_failure(request, reason='', template_name='403_csrf.html'):
    if request.path.startswith('/api/v1/'):
        return JsonResponse(
            {
                'code': 'permission_denied',
                'message': 'CSRF verification failed.',
                'fields': None,
                'retry_after': None,
            },
            status=403,
        )
    return django_csrf_failure(request, reason=reason, template_name=template_name)
