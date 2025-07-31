from django.db import models
from django.contrib.postgres.fields import ArrayField
from users.models import CustomUser

# models.py
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    

class Size(models.Model):
    name = models.CharField(max_length=8, unique=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, default=4)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    posted_by = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    #postgres array for cloudinart
    image_urls = ArrayField(models.URLField(), blank=True, default=list)
    image_public_ids = ArrayField(models.CharField(max_length=200), blank=True, default=list)
    tags = models.ManyToManyField(Tag, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProductInventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory')
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'size') 

    def __str__(self):
        return f"{self.product.name} - {self.size.name}: {self.stock} unidades"

