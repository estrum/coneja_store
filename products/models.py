from django.db import models
from users.models import Usuario

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
    name = models.CharField(max_length=5, unique=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, default=4)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    posted_by = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    image_url = models.URLField(max_length=255, blank=True, null=True)
    image_public_id = models.CharField(blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True)
    sizes = models.ManyToManyField(Size, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
