from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Task, Notification, TaskHistory


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("id", "username", "email", "date_joined", "is_staff")
    search_fields = ("username", "email")
    ordering = ("-date_joined",)
    date_hierarchy = "date_joined"


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "title", "priority", "status",
        "due_date", "created_at", "completed_at"
    )
    list_filter = ("priority", "status")
    search_fields = ("title", "description", "user__username", "user__email")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = ("user",)
    readonly_fields = ("created_at", "completed_at")


@admin.action(description="Mark selected notifications as READ")
def mark_selected_read(modeladmin, request, queryset):
    queryset.update(is_read=True)

@admin.action(description="Mark selected notifications as UNREAD")
def mark_selected_unread(modeladmin, request, queryset):
    queryset.update(is_read=False)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "task", "message", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("message", "user__username", "user__email", "task__title")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = ("user", "task")
    actions = [mark_selected_read, mark_selected_unread]


@admin.register(TaskHistory)
class TaskHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "task", "change_type", "created_at")
    list_filter = ("change_type",)
    search_fields = ("task__title", "task__id", "user__username", "user__email")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = ("user", "task")
    readonly_fields = ("user", "task", "change_type", "changed_fields", "snapshot", "created_at")
