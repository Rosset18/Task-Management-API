import django_filters
from django.utils import timezone
from .models import Task, Notification

class TaskFilter(django_filters.FilterSet):
    # String filters
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    description = django_filters.CharFilter(field_name="description", lookup_expr="icontains")
    status = django_filters.CharFilter(field_name="status", lookup_expr="iexact")
    priority = django_filters.CharFilter(field_name="priority", lookup_expr="iexact")

    # Date/time ranges
    created_between = django_filters.DateFromToRangeFilter(field_name="created_at")
    due_between = django_filters.DateFromToRangeFilter(field_name="due_date")
    completed_between = django_filters.DateFromToRangeFilter(field_name="completed_at")

    # Convenience booleans
    is_completed = django_filters.BooleanFilter(method="filter_is_completed")
    overdue = django_filters.BooleanFilter(method="filter_overdue")
    due_today = django_filters.BooleanFilter(method="filter_due_today")
    due_soon = django_filters.BooleanFilter(method="filter_due_soon")  # next 24h

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "status",
            "priority",
            "created_between",
            "due_between",
            "completed_between",
            "is_completed",
            "overdue",
            "due_today",
            "due_soon",
        ]

    def filter_is_completed(self, queryset, name, value):
        return queryset.exclude(completed_at__isnull=True) if value else queryset.filter(completed_at__isnull=True)

    def filter_overdue(self, queryset, name, value):
        if not value:
            return queryset
        now = timezone.now()
        return queryset.filter(due_date__lt=now, completed_at__isnull=True)

    def filter_due_today(self, queryset, name, value):
        if not value:
            return queryset
        now = timezone.localtime()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timezone.timedelta(days=1)
        return queryset.filter(due_date__gte=start, due_date__lt=end, completed_at__isnull=True)

    def filter_due_soon(self, queryset, name, value):
        if not value:
            return queryset
        now = timezone.now()
        return queryset.filter(due_date__gte=now, due_date__lte=now + timezone.timedelta(hours=24), completed_at__isnull=True)

class NotificationFilter(django_filters.FilterSet):
    is_read = django_filters.BooleanFilter(field_name="is_read")
    created_between = django_filters.DateFromToRangeFilter(field_name="created_at")
    task_id = django_filters.NumberFilter(field_name="task__id")

    class Meta:
        model = Notification
        fields = ["is_read", "created_between", "task_id"]
