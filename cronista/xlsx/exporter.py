from cronista.base import ModelExporter, BaseExporter
from cronista.xlsx.writer import OpenPyXlWriter


class XlsxModelExporter(ModelExporter, BaseExporter):
    writer_class = OpenPyXlWriter

    def __init__(self):
        writer = self.writer_class()
        super().__init__(exporter_writer=writer)

    def export(self, qs):
        super().export(qs, self.exporter_writer)
        self.export_header(self.exporter_writer)
