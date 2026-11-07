"""
Views for in-app notifications. Every view is scoped to the requesting user.
"""
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import ListView

from apps.notifications.models import Notification


def _safe_redirect_target(request: HttpRequest, target: str, fallback: str) -> str:
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return target
    return fallback


class NotificationListView(LoginRequiredMixin, ListView):
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 25

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        if self.request.GET.get('unread') == '1':
            queryset = queryset.filter(is_read=False)
        return queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['unread_only'] = self.request.GET.get('unread') == '1'
        return context


class NotificationOpenView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=['is_read'])
        fallback = reverse('notifications:notification_list')
        return redirect(_safe_redirect_target(request, notification.link, fallback))


class NotificationMarkReadView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        fallback = reverse('notifications:notification_list')
        return redirect(_safe_redirect_target(request, request.POST.get('next', ''), fallback))


class UnreadCountAPIView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> JsonResponse:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({'unread_count': count})


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest) -> HttpResponse:
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return redirect('notifications:notification_list')
