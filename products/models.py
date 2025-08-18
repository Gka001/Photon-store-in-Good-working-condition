from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db.models import Avg, Q, F  # added Q, F for constraints
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    stock = models.PositiveBigIntegerField(default=0)      # on-hand
    allocated = models.PositiveBigIntegerField(default=0)  # reserved for unpaid orders (NEW)

    search_vector = SearchVectorField(null=True, editable=False)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            GinIndex(fields=["search_vector"]),
        ]
        constraints = [
            # Ensure we never allocate more than we have on hand
            models.CheckConstraint(
                check=Q(allocated__lte=F('stock')),
                name="product_allocated_lte_stock",
            ),
        ]

    @property
    def available(self):
        # Inventory that can still be sold now
        return int(self.stock) - int(self.allocated)

    def average_rating(self):
        return self.reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    def is_in_stock(self):
        # use available instead of raw stock
        return self.available > 0


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')  # One review per user per product
        ordering = ['-created_at']

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.username}"
