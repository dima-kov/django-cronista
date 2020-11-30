from cronista.base import ModelExporter, BaseExporter, ExporterWriter
from cronista.xlsx.writer import OpenPyXlWriter


class Ready(ModelExporter, BaseExporter):
    writer_class = None

    def __init__(self):
        writer = self.writer_class()
        super().__init__(exporter_writer=writer, column_start=1)

    def export(self, qs):
        super().export(self.annotate_qs(qs), self.exporter_writer)
        self.export_header(self.exporter_writer)

    def export_header_after(self, exporter_writer: ExporterWriter):
        exporter_writer.freeze_panes(col=1, row=self.get_start_row())

    def annotate_qs(self, qs):
        return qs


class XlsxModelExporter(Ready):
    writer_class = OpenPyXlWriter
