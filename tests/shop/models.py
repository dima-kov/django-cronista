from django.db import models


class Shop(models.Model):
    name = models.CharField(
        max_length=255,
    )
    date = models.CharField(
        max_length=255,
    )


class Product(models.Model):
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='products'
    )
    price = models.CharField(
        max_length=255,
    )
    description = models.TextField()


class ProductProperty(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='properties')
    name = models.CharField(
        max_length=255,
    )
    value = models.CharField(
        max_length=255,
    )
    quantity = models.IntegerField()
