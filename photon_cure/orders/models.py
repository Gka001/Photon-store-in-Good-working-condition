from django.db import models
from cart.models import Cart
from django.contrib.auth.models import User
from products.models import Product

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True) # If using users
    cart_items = models.ManyToManyField(Cart)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=255)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    order_date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100, default='Guest')

    def __str__(self):
        return f"Order {self.id} - {self.status}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return  f"{self.product.name} x {self.quantity}"   
