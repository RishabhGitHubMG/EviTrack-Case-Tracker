from django.conf import settings


def _content_security_policy() -> str:
    directives = getattr(settings, 'EVITRACK_CSP', {})
    return '; '.join(f"{name} {' '.join(sources)}" for name, sources in directives.items())


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.csp = _content_security_policy()

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('Content-Security-Policy', self.csp)
        response.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        response.setdefault('Referrer-Policy', 'same-origin')
        return response
