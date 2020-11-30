from cronista.base import ModelExporter
from cronista.xlsx.exporter import Ready, XlsxModelExporter
from tests.shop.models import Shop, Product, ProductProperty


class ProductPropertyExporter(ModelExporter):
    model = ProductProperty
    fields = ('name', 'value', 'quantity')


class ProductExporter(ModelExporter):
    model = Product
    state = ModelExporter.HORIZONTAL
    fields = ('description', 'price',)
    related = {
        'properties': ProductPropertyExporter,
    }


class ShopExporter(XlsxModelExporter):
    model = Shop
    fields = ('name', 'date',)
    related = {
        'products': ProductExporter
    }
