from django.db import models
from django.contrib.postgres.fields import ArrayField
from users.models import CustomUser

# models.py
class Category(models.Model):
    """Categoria para el filtrado de productos"""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


#TODO: permitir que el usuario se cree un tag si no existe
class Tag(models.Model):
    """Tags para la clasificación y filtrado de productos"""
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    

class Size(models.Model):
    """
    Talla o tamaño para el articulo del producto.
        
        parameters:
            size_name (str): XS, S, M, XL, 48, 59, etc...
            description (str): si la talla es americana, Uk u otro.
    """
    size_name = models.CharField(max_length=8, unique=True)
    description = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return self.size_name


#TODO: añadír slug para las busquedas
class Product(models.Model):
    """
    productos para mostrar en la vitrina de la web u app.
    estos se pueden filtrar por categoria, tags, precio,
    nombre, descripción y tallas disponibles.
    deben mostrarse aquellos con is_active = True.
    si todos sus articulos quedan en 0, se cambia is active = False 
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    posted_by = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    #postgres array for cloudinart
    image_urls = ArrayField(models.URLField(), blank=True, default=list)
    image_public_ids = ArrayField(
        models.CharField(max_length=200), blank=True, default=list)
    tags = models.ManyToManyField(Tag, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProductInventory(models.Model):
    """
    Inventario de producto asociado a un producto.
    Un producto puede contener multiples tallas y cada talla
    tiene un stock propio
    """
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='inventory')
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'size') 

    def __str__(self):
        return (f"{self.product.name} - {self.size}")

