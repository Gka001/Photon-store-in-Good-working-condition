from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Order

@receiver(pre_save, sender=Order)
def notify_user_on_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return  # New order, no status change yet

    try:
        previous = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    if previous.status != instance.status:
        if instance.status == 'Shipped' and not instance.expected_delivery:
            try:
                # ✅ FIXED: Access as property, not function
                instance.expected_delivery = instance.expected_delivery_range[1]
            except Exception:
                instance.expected_delivery = timezone.now().date() + timezone.timedelta(days=10)

        if instance.email:
            subject = f"Photon Cure - Order #{instance.id} Status Update"
            message = render_to_string('email/order_status_update.txt', {
                'order': instance,
                'old_status': previous.status,
                'new_status': instance.status,
                # ✅ FIXED: Access as property
                'expected_start': instance.expected_delivery_range[0],
                'expected_end': instance.expected_delivery_range[1],
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.email])
