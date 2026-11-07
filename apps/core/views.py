from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView


class LandingView(TemplateView):
    template_name = 'landing.html'


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'


class SearchAPIView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> JsonResponse:
        return JsonResponse({'results': []})


class DashboardChartsAPIView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> JsonResponse:
        return JsonResponse({})


def error_403(request: HttpRequest, exception: Exception = None) -> HttpResponse:
    """Custom 403 Forbidden error handler."""
    return render(request, 'errors/403.html', status=403)


def error_404(request: HttpRequest, exception: Exception = None) -> HttpResponse:
    """Custom 404 Not Found error handler."""
    return render(request, 'errors/404.html', status=404)


def error_500(request: HttpRequest) -> HttpResponse:
    """Custom 500 Internal Server Error handler."""
    return render(request, 'errors/500.html', status=500)
