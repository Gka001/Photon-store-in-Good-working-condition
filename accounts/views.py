from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from orders.models import Order
from .forms import UserProfileForm, CustomUserCreationForm
from .models import UserProfile
from .tasks import send_welcome_email_task

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Automatically create a UserProfile if signals are not used
            UserProfile.objects.get_or_create(user=user)

            email = user.email
            if email:
                html_message = render_to_string('emails/welcome_email.html', {'username': user.username})
                plain_message = strip_tags(html_message)
                send_welcome_email_task.delay(
                    subject='Welcome to Photon Cure!',
                    plain_message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    html_message=html_message
                )
            messages.success(request, 'Account created successfully! A welcome email has been sent.')
            return redirect('registration-success')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'orders': orders
    })

@login_required
def edit_profile(request):
    # Make sure user has profile (in case signals not working)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('user-profile')
    else:
        form = UserProfileForm(instance=user_profile)
    return render(request, 'accounts/edit_profile.html', {'form': form})

def registration_success(request):
    return render(request, 'registration/success.html')
