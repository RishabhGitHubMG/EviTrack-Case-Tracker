from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import SessionAuthentication


class SessionAuthentication401(SessionAuthentication):
    def authenticate_header(self, request):
        return 'Session'


class SessionAuthentication401Scheme(OpenApiAuthenticationExtension):
    target_class = 'apps.core.api.authentication.SessionAuthentication401'
    name = 'cookieAuth'

    def get_security_definition(self, auto_schema):
        return {'type': 'apiKey', 'in': 'cookie', 'name': settings.SESSION_COOKIE_NAME}
