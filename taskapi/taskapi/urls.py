from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from rest_framework.routers import DefaultRouter

from core.views import (
    TaskViewSet,
    NotificationViewSet,
    RegisterView,
    HomeView,
    DashboardView,
    SignupView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("admin/", admin.site.urls),
]

# Two-factor urls if enabled and available; otherwise, provide a safe fallback
if getattr(settings, "USE_2FA", False):
    try:
        urlpatterns += [
            path("", include(("two_factor.urls", "two_factor"), namespace="two_factor")),
        ]
    except Exception:
        # Fallback: make /account/login/ point to default login so links won't 404
        urlpatterns += [
            path("account/login/", RedirectView.as_view(pattern_name="login", permanent=False)),
        ]
else:
    # Even if 2FA off, also provide /account/login/ as a friendly alias to normal login
    urlpatterns += [
        path("account/login/", RedirectView.as_view(pattern_name="login", permanent=False)),
    ]

# Pages (HTML)
urlpatterns += [
    path("", HomeView.as_view(), name="home"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),

    # Accounts (signup + Django's auth views)
    path("accounts/signup/", SignupView.as_view(), name="signup"),
    path("accounts/", include("django.contrib.auth.urls")),
]

# API Auth (JWT + API register)
urlpatterns += [
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

# API routes
urlpatterns += [
    path("api/", include(router.urls)),
]
