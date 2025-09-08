from datetime import datetime, timedelta, date
import calendar

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, FormView, CreateView, UpdateView

from django.contrib.auth import get_user_model
from .models import Task, Profile
from .forms import SignupForm, TaskForm, QuickTaskForm, ProfileForm

# --- News (free RSS) ---
def fetch_news(limit=6):
    try:
        import feedparser
        # Technology/World feeds (no API key)
        feeds = [
            "https://feeds.bbci.co.uk/news/technology/rss.xml",
            "https://feeds.bbci.co.uk/news/world/rss.xml",
        ]
        items = []
        for url in feeds:
            d = feedparser.parse(url)
            for e in d.entries[:limit]:
                items.append({
                    "title": e.get("title", "Headline"),
                    "link": e.get("link", "#"),
                    "published": e.get("published", ""),
                    "source": d.feed.get("title", "News"),
                })
        # de-dupe by title, keep order
        seen = set(); unique = []
        for it in items:
            if it["title"] not in seen:
                seen.add(it["title"])
                unique.append(it)
        return unique[:limit]
    except Exception:
        return []

# --- Helpers ---
def display_name_for(user):
    prof = Profile.objects.filter(user=user).first()
    return (prof.name or user.first_name or user.username)

# --- Views ---
class HomeView(TemplateView):
    template_name = "landing.html"
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

class SignupView(FormView):
    template_name = "registration/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("dashboard")
    def form_valid(self, form):
        user = form.save()
        # create paired profile
        Profile.objects.get_or_create(user=user, defaults={"name": user.first_name or user.username})
        login(self.request, user)
        messages.success(self.request, "Welcome to Focus Flow!")
        return super().form_valid(form)

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        ctx["greeting"] = display_name_for(u)
        ctx["quick_form"] = QuickTaskForm()
        ctx["tasks"] = Task.objects.filter(user=u).order_by("-created_at")[:30]
        ctx["news"] = fetch_news(limit=6)
        return ctx

class ProfileEditView(LoginRequiredMixin, FormView):
    template_name = "profile.html"
    form_class = ProfileForm
    success_url = reverse_lazy("profile")
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        kwargs["instance"] = profile
        return kwargs
    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Profile updated.")
        return super().form_valid(form)

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    template_name = "task_form.html"
    form_class = TaskForm
    success_url = reverse_lazy("dashboard")
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Task created.")
        return super().form_valid(form)

class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    template_name = "task_form.html"
    form_class = TaskForm
    success_url = reverse_lazy("dashboard")
    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)
    def form_valid(self, form):
        messages.success(self.request, "Task updated.")
        return super().form_valid(form)

@login_required
def task_delete_view(request, pk):
    if request.method == "POST":
        task = get_object_or_404(Task, pk=pk, user=request.user)
        task.delete()
        messages.success(request, "Task deleted.")
        return redirect("dashboard")
    return redirect("dashboard")

@login_required
def task_complete_view(request, pk):
    if request.method == "POST":
        task = get_object_or_404(Task, pk=pk, user=request.user)
        task.status = "done"
        task.completed_at = datetime.now()
        task.save(update_fields=["status", "completed_at"])
        messages.success(request, "Task marked complete.")
        return redirect("dashboard")
    return redirect("dashboard")

class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = "calendar.html"
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = date.today()
        year = int(self.request.GET.get("year", today.year))
        month = int(self.request.GET.get("month", today.month))
        cal = calendar.Calendar(firstweekday=0)
        month_days = list(cal.itermonthdates(year, month))  # includes spillover days
        # tasks by date
        user_tasks = Task.objects.filter(user=self.request.user, due_date__isnull=False)
        tasks_by_day = {}
        for t in user_tasks:
            d = t.due_date.date()
            tasks_by_day.setdefault(d, []).append(t)
        ctx.update({
            "year": year,
            "month": month,
            "month_name": calendar.month_name[month],
            "days": month_days,
            "tasks_by_day": tasks_by_day,
        })
        return ctx

