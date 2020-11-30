from cronista.base import ModelExporter, BaseExporter
from cronista.xlsx.writer import OpenPyXlWriter


class ModelExporterWriter(ModelExporter, BaseExporter):
    writer_class = None

    def __init__(self):
        writer = self.writer_class()
        super().__init__(exporter_writer=writer, column_start=1)

    def export(self, qs):
        super().export(self.annotate_qs(qs), self.exporter_writer)


class XlsxModelExporter(ModelExporterWriter):
    writer_class = OpenPyXlWriter
