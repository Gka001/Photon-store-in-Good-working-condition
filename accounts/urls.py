from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from accounts import views as accounts_views

urlpatterns = [
    path('profile/', views.profile_view, name='user-profile'),
    path('profile/edit/', views.edit_profile, name='edit-profile'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html'),name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),
     path('register/success/', accounts_views.registration_success, name='registration-success'),
]