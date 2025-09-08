from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView
from django.shortcuts import redirect
from django.contrib.auth import login
from django.conf import settings

from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

# Safe import for 2FA; fall back to a no-op mixin if not installed
try:
    if getattr(settings, "USE_2FA", False):
        from two_factor.views import OTPRequiredMixin as _OTPRequiredMixin
    else:
        raise ImportError
except Exception:
    class _OTPRequiredMixin:
        """No-op mixin used when 2FA is disabled/unavailable."""
        pass

from .models import Task, Notification, TaskHistory
from .serializers import TaskSerializer, NotificationSerializer, RegisterSerializer, TaskHistorySerializer
from .permissions import IsOwner
from .filters import TaskFilter, NotificationFilter
from .forms import SignupForm

# ===== HTML views =====
class HomeView(TemplateView):
    template_name = "home.html"
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

class SignupView(FormView):
    template_name = "registration/signup.html"
    form_class = SignupForm
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect("dashboard")

class DashboardView(LoginRequiredMixin, _OTPRequiredMixin, TemplateView):
    template_name = "dashboard.html"
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["recent_tasks"] = Task.objects.filter(user=user).order_by("-created_at")[:20]
        ctx["recent_notifications"] = Notification.objects.filter(user=user).order_by("-created_at")[:20]
        return ctx

# ===== API views =====
class RegisterView(CreateAPIView):
    authentication_classes = []  # allow anonymous registration
    permission_classes = []
    serializer_class = RegisterSerializer

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "due_date", "completed_at", "priority", "status"]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        task = self.get_object()
        task.status = "done"
        if task.completed_at is None:
            task.completed_at = timezone.now()
        task.save(update_fields=["status", "completed_at"])
        serializer = self.get_serializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        qs = TaskHistory.objects.filter(task_id=pk, user=request.user).order_by("-created_at")
        page = self.paginate_queryset(qs)
        ser = TaskHistorySerializer(page or qs, many=True)
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)

class NotificationViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = NotificationFilter
    ordering_fields = ["created_at"]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        count = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"updated": count})

