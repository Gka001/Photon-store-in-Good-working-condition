from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Order
from core.api_clients.shiprocket import create_shiprocket_shipment  # 🚀 Shiprocket integration


@receiver(pre_save, sender=Order)
def notify_user_on_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return  # New order, no status change yet

    try:
        previous = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    # 🚨 If status changed
    if previous.status != instance.status:
        # 🚚 Auto set delivery date if shipped
        if instance.status == 'Shipped' and not instance.expected_delivery:
            try:
                instance.expected_delivery = instance.expected_delivery_range[1]
            except Exception:
                instance.expected_delivery = timezone.now().date() + timezone.timedelta(days=10)

            # 🚀 Create shipment via Shiprocket API
            try:
                shipment_response = create_shiprocket_shipment(instance)
                # You can optionally store shipment ID, tracking ID, etc. from response
                # Example:
                # instance.shiprocket_shipment_id = shipment_response.get('shipment_id')
            except Exception as e:
                print(f"Error creating Shiprocket shipment: {e}")

        # 📧 Send email notification
        if instance.email:
            subject = f"Photon Cure - Order #{instance.id} Status Update"
            message = render_to_string('orders/email/order_status_update.txt', {
                'order': instance,
                'old_status': previous.status,
                'new_status': instance.status,
                'expected_start': instance.expected_delivery_range[0],
                'expected_end': instance.expected_delivery_range[1],
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.email])
