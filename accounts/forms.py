from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError  # ✅ NEW: For custom error
from .models import CustomUser, UserProfile  # ✅ Use your custom user model


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser  # ✅ Use the custom user model here
        fields = ('username', 'email', 'password1', 'password2')

    # ✅ NEW: Override the email validation to show a friendlier message
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered. Please use a different one.")
        return email


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['address', 'phone']  # ✅ Adjust based on your actual fields
