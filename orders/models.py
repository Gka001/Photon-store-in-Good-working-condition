from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.db.models import F
from datetime import timedelta
from products.models import Product


class InventoryError(Exception):
    pass


class InsufficientStock(InventoryError):
    pass


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='Pending')
    address = models.TextField()
    phone = models.CharField(max_length=15)
    order_date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100, default='Guest')
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField()
    expected_delivery = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=100, default='Vijayawada')
    state = models.CharField(max_length=100, default='Andhra Pradesh')
    pincode = models.CharField(max_length=10, default='520001')

    # ✅ Shiprocket shipment fields
    awb_code = models.CharField(max_length=100, blank=True, null=True)
    shiprocket_shipment_id = models.CharField(max_length=100, blank=True, null=True)
    courier_company_id = models.CharField(max_length=100, blank=True, null=True)
    tracking_url = models.URLField(blank=True, null=True)

    # ✅ New: inventory reservation state (idempotency & safety)
    inventory_reserved = models.BooleanField(default=False)
    inventory_finalized = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.id} - {self.status}"

    # ---------- Convenience & UX ----------

    def mark_as_failed(self):
        self.status = 'Failed'
        self.save(update_fields=['status'])
        # Auto-release any reservation if payment failed/aborted
        self.release_inventory()

    def mark_as_cancelled(self):
        self.status = 'Cancelled'
        self.save(update_fields=['status'])
        # Auto-release any reservation if user/admin cancels
        self.release_inventory()

    # ---------- Delivery window logic (unchanged) ----------

    def is_metro_city(self):
        metro_keywords = ['delhi', 'mumbai', 'chennai', 'kolkata', 'bengaluru', 'bangalore', 'hyderabad', 'pune', 'ahmedabad']
        return any(city in self.address.lower() for city in metro_keywords)

    def calculate_expected_delivery_range(self):
        def add_business_days(start_date, days):
            current = start_date
            added = 0
            while added < days:
                current += timedelta(days=1)
                if current.weekday() < 5:  # Monday–Friday
                    added += 1
            return current

        order_date = self.order_date or timezone.now()

        if self.is_metro_city():
            start_days, end_days = 7, 10
        else:
            start_days, end_days = 10, 14

        start_date = add_business_days(order_date, start_days)
        end_date = add_business_days(order_date, end_days)
        return start_date, end_date

    @property
    def expected_delivery_range(self):
        return self.calculate_expected_delivery_range()

    # ---------- Inventory reservation workflow ----------

    def _items_for_lock(self):
        # Lock products in a deterministic order to avoid deadlocks
        return list(self.items.select_related("product").order_by("product_id"))

    def reserve_inventory(self):
        """
        Reserve (allocate) quantities before opening payment.
        Idempotent: safe to call more than once.
        Raises InsufficientStock if any line cannot be reserved.
        """
        if self.inventory_reserved:
            return

        with transaction.atomic():
            order_items = self._items_for_lock()
            if not order_items:
                return  # empty order, nothing to do

            # Lock the product rows we're about to update
            Product.objects.select_for_update().filter(
                id__in=[it.product_id for it in order_items]
            ).order_by('id')

            for it in order_items:
                updated = Product.objects.filter(
                    id=it.product_id,
                    allocated__lte=F('stock') - it.quantity
                ).update(allocated=F('allocated') + it.quantity)
                if updated == 0:
                    raise InsufficientStock(f"{it.product.name} just ran out")

            self.inventory_reserved = True
            self.save(update_fields=['inventory_reserved'])

    def confirm_inventory(self):
        """
        Finalize after successful payment: move from allocated -> sold.
        Idempotent: safe to call more than once.
        Raises InsufficientStock only if a rare mismatch occurs.
        """
        if self.inventory_finalized:
            return

        with transaction.atomic():
            order_items = self._items_for_lock()
            if not order_items:
                return

            Product.objects.select_for_update().filter(
                id__in=[it.product_id for it in order_items]
            ).order_by('id')

            for it in order_items:
                updated = Product.objects.filter(
                    id=it.product_id,
                    allocated__gte=it.quantity,
                    stock__gte=it.quantity
                ).update(
                    allocated=F('allocated') - it.quantity,
                    stock=F('stock') - it.quantity
                )
                if updated == 0:
                    # Very rare: allocation missing or stock shrank unexpectedly
                    raise InsufficientStock("Inventory mismatch during finalize")

            self.inventory_finalized = True
            self.save(update_fields=['inventory_finalized'])

    def release_inventory(self):
        """
        Release a prior reservation (payment failed/abandoned/cancelled).
        Idempotent: if not reserved or already finalized, it’s a no-op.
        """
        if not self.inventory_reserved or self.inventory_finalized:
            return

        with transaction.atomic():
            order_items = self._items_for_lock()
            if not order_items:
                return

            Product.objects.select_for_update().filter(
                id__in=[it.product_id for it in order_items]
            ).order_by('id')

            for it in order_items:
                # Guard with allocated__gte to avoid going negative if retried
                Product.objects.filter(
                    id=it.product_id,
                    allocated__gte=it.quantity
                ).update(allocated=F('allocated') - it.quantity)

            self.inventory_reserved = False
            self.save(update_fields=['inventory_reserved'])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity
