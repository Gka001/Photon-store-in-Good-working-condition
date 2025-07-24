from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Registration
    path('register/', views.register, name='register'),
    path('register/success/', views.registration_success, name='registration-success'),

    # Profile
    path('profile/', views.profile_view, name='user-profile'),
    path('profile/edit/', views.edit_profile, name='edit-profile'),

    # Password change
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change_form.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'), name='password_change_done'),
]
