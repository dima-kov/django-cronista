# django-cronista

Powerful and fully customizable django app to export model objects into xlsx/json/...

## Example 

```python
# models.py
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

```
and exporter:
```python
#exporter.py
from cronista.base import ModelExporter
from cronista.readers.django import DjangoModelReader
from cronista.xlsx.exporter import XlsxModelExporter
from tests.shop.models import Shop, Product, ProductProperty


class ProductPropertyExporter(ModelExporter):
    model = ProductProperty
    model_reader = DjangoModelReader(ProductProperty)
    fields = ('name', 'value', 'quantity')


class ProductExporter(ModelExporter):
    model = Product
    state = ModelExporter.HORIZONTAL
    model_reader = DjangoModelReader(Product)
    fields = ('description', 'price',)
    related = {
        'properties': ProductPropertyExporter,
    }


class ShopExporter(XlsxModelExporter):
    model = Shop
    model_reader = DjangoModelReader(Shop)
    fields = ('name', 'date',)
    related = {
        'products': ProductExporter
    }


```

then use it:

```python
exporter = ShopExporter()
exporter.export(Shop.objects.all())
exporter.as_http_response() # django http response
file = exporter.as_file()
```

Example result file is [here](tests/assets/example.xlsx)
