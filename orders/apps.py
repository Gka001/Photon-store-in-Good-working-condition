from django.apps import AppConfig
from django.conf import settings


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'

    def ready(self):
        # Only load signals if explicitly enabled in settings
        if getattr(settings, 'SHIPROCKET_ENABLE_SIGNALS', True):
            import orders.signals
