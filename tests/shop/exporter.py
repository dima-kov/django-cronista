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
