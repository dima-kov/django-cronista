import random

from django.test import TestCase

from tests.shop.exporter import ShopExporter, ProductExporter, ProductPropertyExporter
from tests.shop.models import Shop
from tests.shop.tests.factory import ShopFactory, ProductFactory, ProductPropertyFactory


class NestedTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.exporter = ShopExporter()

    def test_get_size(self):
        self.assertEqual(ShopExporter.get_size(), 7)
        self.assertEqual(ProductExporter.get_size(), 5)
        self.assertEqual(ProductPropertyExporter.get_size(), 3)

    def test(self):
        self.assertEqual(self.exporter.column_start, 1)
        self.assertEqual(self.exporter.column_end, 7)

    def test_nested(self):
        nested_products = self.exporter.nested_exporters['products']
        self.assertEqual(nested_products.column_start, 3)
        self.assertEqual(nested_products.column_end, 7)

        product_exporter = nested_products.exporters[0]
        self.assertEqual(product_exporter.column_start, 3)
        self.assertEqual(product_exporter.column_end, 7)

    def test_nested_property(self):
        nested_products = self.exporter.nested_exporters['products']
        product_exporter = nested_products.exporters[0]

        nested_properties = product_exporter.nested_exporters['properties']
        self.assertEqual(nested_properties.column_start, 5)
        self.assertEqual(nested_properties.column_end, 7)

        self.assertEqual(nested_properties.exporters[0].column_start, 5)
        self.assertEqual(nested_properties.exporters[0].column_end, 7)


class NestedWithNewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.exporter = ShopExporter()

    def _assert_exporter(self, exporter, start, end):
        self.assertEqual(exporter.column_start, start)
        self.assertEqual(exporter.column_end, end)

    def _assert_shop(self, start, end):
        self._assert_exporter(self.exporter, start, end)

    def _assert_products(self, start, end, number=None):
        nested_products = self.exporter.nested_exporters['products']
        self._assert_exporter(nested_products, start, end)

        if number:
            self.assertEqual(nested_products.get_number(), number)

    def test(self):
        self._assert_shop(1, 7)
        self._assert_products(3, 7, number=1)

        col_shift = self.exporter.nested_exporters['products'].new()
        self.assertEqual(col_shift, 5)
        self._assert_products(3, 12, number=2)
        self._assert_shop(1, 7)


class ShopExporterWithData(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.exporter = ShopExporter()
        cls._new_shop()
        cls._new_shop()

    @classmethod
    def _new_shop(cls, product_n=2, product_properties_n_max=3):
        shop = ShopFactory()
        products = ProductFactory.create_batch(size=product_n, shop=shop)
        for p in products:
            [ProductPropertyFactory(product=p) for _ in range(random.randint(0, product_properties_n_max))]

    def test(self):
        self.exporter.export(Shop.objects.all())
        self.exporter.as_file('fff.xlsx')
