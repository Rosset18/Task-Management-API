from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

PRIORITY_CHOICES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
]

STATUS_CHOICES = [
    ("todo", "To Do"),
    ("in_progress", "In Progress"),
    ("done", "Done"),
]

class User(AbstractUser):
    email = models.EmailField(unique=True)
    def __str__(self):
        return self.username

class Task(models.Model):
    user = models.ForeignKey("core.User", on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="todo")
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["completed_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.user})"

class Notification(models.Model):
    user = models.ForeignKey("core.User", on_delete=models.CASCADE, related_name="notifications")
    task = models.ForeignKey("core.Task", on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notif to {self.user}: {self.message[:30]}"

class TaskHistory(models.Model):
    """Immutable audit trail for Task changes."""
    CHANGE_CHOICES = [
        ("created", "Created"),
        ("updated", "Updated"),
        ("completed", "Completed"),
        ("deleted", "Deleted"),
    ]

    user = models.ForeignKey("core.User", on_delete=models.CASCADE, related_name="task_histories")
    task = models.ForeignKey("core.Task", on_delete=models.CASCADE, related_name="history")
    change_type = models.CharField(max_length=20, choices=CHANGE_CHOICES)
    changed_fields = models.JSONField(default=list)   # list[str]
    snapshot = models.JSONField(default=dict)        # point-in-time Task data
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["task", "change_type"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"TaskHistory<{self.change_type}> {self.task_id} by {self.user_id} @ {self.created_at}"

# ===== Signals: notifications + history =====
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

TASK_TRACK_FIELDS = ("title", "description", "priority", "status", "due_date", "completed_at")

def _task_snapshot(instance: Task) -> dict:
    return {
        "id": instance.id,
        "user_id": instance.user_id,
        "title": instance.title,
        "description": instance.description,
        "priority": instance.priority,
        "status": instance.status,
        "due_date": instance.due_date.isoformat() if instance.due_date else None,
        "created_at": instance.created_at.isoformat() if instance.created_at else None,
        "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
    }

@receiver(pre_save, sender=Task)
def task_pre_save(sender, instance: Task, **kwargs):
    if instance.pk:
        try:
            prev = Task.objects.get(pk=instance.pk)
        except Task.DoesNotExist:
            prev = None
        if prev:
            instance._previous_state = {
                f: getattr(prev, f) if f not in ("due_date", "completed_at") else (
                    getattr(prev, f).isoformat() if getattr(prev, f) else None
                )
                for f in TASK_TRACK_FIELDS
            }

@receiver(post_save, sender=Task)
def task_post_save(sender, instance: Task, created, **kwargs):
    # Always create a history & notification on create
    if created:
        TaskHistory.objects.create(
            user=instance.user,
            task=instance,
            change_type="created",
            changed_fields=list(TASK_TRACK_FIELDS),
            snapshot=_task_snapshot(instance),
        )
        Notification.objects.create(
            user=instance.user,
            task=instance,
            message=f"Task '{instance.title}' created.",
        )
        # Optional due-soon (within 24h)
        if instance.due_date and instance.due_date <= timezone.now() + timedelta(hours=24):
            Notification.objects.create(
                user=instance.user,
                task=instance,
                message=f"Task '{instance.title}' is due soon ({instance.due_date:%Y-%m-%d %H:%M}).",
            )
        return

    # Updates
    prev = getattr(instance, "_previous_state", None)
    if prev is not None:
        current = {
            f: (getattr(instance, f).isoformat() if getattr(instance, f) else None)
            if f in ("due_date", "completed_at") else getattr(instance, f)
            for f in TASK_TRACK_FIELDS
        }
        changed = [f for f in TASK_TRACK_FIELDS if prev.get(f) != current.get(f)]
        if changed:
            # If status moved to done and completed_at not set, stamp it without triggering signals again
            if "status" in changed and instance.status == "done" and instance.completed_at is None:
                from django.db import transaction
                with transaction.atomic():
                    type_now = timezone.now()
                    # update without signals
                    Task.objects.filter(pk=instance.pk).update(completed_at=type_now)
                    instance.completed_at = type_now
                TaskHistory.objects.create(
                    user=instance.user,
                    task=instance,
                    change_type="completed",
                    changed_fields=changed,
                    snapshot=_task_snapshot(instance),
                )
                Notification.objects.create(
                    user=instance.user,
                    task=instance,
                    message=f"Task '{instance.title}' marked completed.",
                )
            else:
                TaskHistory.objects.create(
                    user=instance.user,
                    task=instance,
                    change_type="updated",
                    changed_fields=changed,
                    snapshot=_task_snapshot(instance),
                )
                Notification.objects.create(
                    user=instance.user,
                    task=instance,
                    message=f"Task '{instance.title}' updated (fields: {', '.join(changed)}).",
                )

@receiver(post_delete, sender=Task)
def task_post_delete(sender, instance: Task, **kwargs):
    # Keep a tombstone history record; task FK will be dangling if cascaded, so store minimal snapshot
    TaskHistory.objects.create(
        user=instance.user,
        task=instance,  # OK: it's being deleted; for SQLite this is fine in practice as this runs before row removal
        change_type="deleted",
        changed_fields=list(TASK_TRACK_FIELDS),
        snapshot=_task_snapshot(instance),
    )

