from unittest import TestCase

from cronista.base import ModelExporter


class ModelExporterTestCase(TestCase):
    class TestExporter(ModelExporter):
        model = 2
        fields = ('field_one', 'field_two', 'field_three',)

    @classmethod
    def setUpClass(cls) -> None:
        cls.exporter = cls.TestExporter()

    def test(self):
        self.assertEqual(self.exporter.get_number(), 1)
        self.assertEqual(self.exporter.get_size(), 3)
        self.assertEqual(self.exporter.get_one_size(), 3)

        self.exporter._number = 2
        self.assertEqual(self.exporter.get_size(), 6)
        self.assertEqual(self.exporter.get_one_size(), 3)
