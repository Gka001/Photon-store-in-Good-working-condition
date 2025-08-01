from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from products.models import Product

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

    def __str__(self):
        return f"Order {self.id} - {self.status}"

    def mark_as_failed(self):
        self.status = 'Failed'
        self.save()

    def mark_as_cancelled(self):
        self.status = 'Cancelled'
        self.save()

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
