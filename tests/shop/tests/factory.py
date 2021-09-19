import factory
from factory import fuzzy

from tests.shop.models import Shop, Product, ProductProperty


class ShopFactory(factory.django.DjangoModelFactory):
    name = factory.sequence(lambda n: f'Shop name {n}')
    date = factory.sequence(lambda n: f'Some date {n}')

    class Meta:
        model = Shop


class ProductFactory(factory.django.DjangoModelFactory):
    shop = factory.SubFactory(ShopFactory)
    price = fuzzy.FuzzyInteger(low=10)
    description = factory.sequence(lambda n: f'Product {n}')

    class Meta:
        model = Product


class ProductPropertyFactory(factory.django.DjangoModelFactory):
    product = factory.SubFactory(ProductFactory)
    name = fuzzy.FuzzyText()
    value = fuzzy.FuzzyInteger(low=0)
    quantity = fuzzy.FuzzyInteger(low=0)

    class Meta:
        model = ProductProperty
