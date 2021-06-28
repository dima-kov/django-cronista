from cronista.base.model import ModelExporterWriter
from cronista.xlsx.writer import OpenPyXlWriter


class XlsxModelExporter(ModelExporterWriter):
    writer_class = OpenPyXlWriter
