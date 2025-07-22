from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

@shared_task
def send_welcome_email_task(subject, plain_message, from_email, recipient_list, html_message=None):
    try:
        msg = EmailMultiAlternatives(subject, plain_message, from_email, recipient_list)
        if html_message:
            msg.attach_alternative(html_message, "text/html")
        msg.send()
        print(f"✅ Welcome email sent to {recipient_list}")
    except Exception as e:
        print(f"❌ Failed to send welcome email to {recipient_list}: {e}")
