from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularAPIView
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api.serializers import StatusSerializer


class SchemaAccessPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            settings.DEBUG
            or (user and user.is_authenticated and (user.is_superuser or user.is_admin))
        )


class SchemaAPIView(SpectacularAPIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [SchemaAccessPermission]


class HealthAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=StatusSerializer)
    def get(self, request):
        return Response({'status': 'ok'})


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfCookieAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=StatusSerializer)
    def get(self, request):
        return Response({'status': 'ok'})
