from django import forms
from django.contrib.auth import get_user_model
from .models import Task, Profile

User = get_user_model()

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm password")

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password"]

    def clean(self):
        data = super().clean()
        if data.get("password") != data.get("password_confirm"):
            raise forms.ValidationError("Passwords do not match")
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "priority", "status", "due_date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

class QuickTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "due_date"]

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["name", "occupation", "age", "language"]

