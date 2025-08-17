# orders/signals.py
from django.conf import settings

# Only wire signals if explicitly enabled
if getattr(settings, "SHIPROCKET_ENABLE_SIGNALS", False):
    from django.db.models.signals import post_save
    from django.dispatch import receiver
    from .models import Order
    from core.api_clients.shiprocket import create_shiprocket_shipment

    @receiver(post_save, sender=Order)
    def push_to_shiprocket_on_ship(sender, instance: Order, **kwargs):
        # Fire only when order is set to 'Shipped'
        if instance.status == "Shipped":
            try:
                create_shiprocket_shipment(instance)
            except Exception as e:
                # You can add logging here if you prefer
                pass
else:
    # Signals disabled (admin action handles Shiprocket push)
    pass
