"""
Core views and custom HTTP error handlers for EviTrack.
"""
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def error_403(request: HttpRequest, exception: Exception = None) -> HttpResponse:
    """Custom 403 Forbidden error handler."""
    return render(request, 'core/403.html', status=403)


def error_404(request: HttpRequest, exception: Exception = None) -> HttpResponse:
    """Custom 404 Not Found error handler."""
    return render(request, 'core/404.html', status=404)


def error_500(request: HttpRequest) -> HttpResponse:
    """Custom 500 Internal Server Error handler."""
    return render(request, 'core/500.html', status=500)
