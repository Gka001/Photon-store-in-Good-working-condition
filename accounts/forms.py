from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.core.exceptions import ValidationError
from .models import CustomUser, UserProfile

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required. Enter a valid email address.")

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered. Please use a different one.")
        return email


class UserProfileForm(forms.ModelForm):
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    phone = forms.CharField(required=False, help_text="Optional. Include your country code if applicable.")

    class Meta:
        model = UserProfile
        fields = ['address', 'phone']


class CustomPasswordResetForm(PasswordResetForm):
    username = forms.CharField(max_length=150, required=True, label="Username")

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        username = cleaned_data.get('username')

        if email and username:
            try:
                User.objects.get(username=username, email=email)
            except User.DoesNotExist:
                raise ValidationError("No user found with the given username and email.")
        return cleaned_data

    def get_users(self, email):
        username = self.cleaned_data.get('username')
        try:
            user = User.objects.get(email=email, username=username)
            if user.has_usable_password():
                return [user]
        except User.DoesNotExist:
            return []
        return []
