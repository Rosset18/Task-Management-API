from django.urls import path
from .views import (
    HomeView, DashboardView, CalendarView,
    SignupView, ProfileEditView,
    TaskCreateView, TaskUpdateView,
    task_delete_view, task_complete_view,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("calendar/", CalendarView.as_view(), name="calendar"),

    path("accounts/signup/", SignupView.as_view(), name="signup"),
    path("profile/", ProfileEditView.as_view(), name="profile"),

    path("tasks/new/", TaskCreateView.as_view(), name="task_new"),
    path("tasks/<int:pk>/edit/", TaskUpdateView.as_view(), name="task_edit"),
    path("tasks/<int:pk>/delete/", task_delete_view, name="task_delete"),     # POST
    path("tasks/<int:pk>/complete/", task_complete_view, name="task_complete"),# POST
]

