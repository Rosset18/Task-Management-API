from django.contrib import admin
from .models import Task, Profile

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "priority", "status", "due_date", "created_at")
    list_filter = ("priority", "status", "created_at")
    search_fields = ("title", "description", "user__username")

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "occupation", "age", "language")
    search_fields = ("user__username", "name", "occupation", "language")

