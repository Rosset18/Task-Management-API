from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        value = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=value).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return value
