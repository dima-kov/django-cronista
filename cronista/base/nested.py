from django.db.models import QuerySet

from cronista.base import ModelExporter, ExporterWriter
from cronista.base.shift import Shift


class NestedExporter(object):
    exporter_class: type(ModelExporter) = None

    def __init__(self, exporter_class=None):
        self.exporter_class = exporter_class or self.exporter_class
        self.exporters: [ModelExporter] = []
        self.new()

    def get_number(self):
        """
        Returns how many times model exporter is placed on sheet
        """
        return len(self.exporters)

    def new(self):
        exporter: ModelExporter = self.exporter_class()
        # exporter.set_start_end()
        self.exporters.append(exporter)

    def export(self, qs: [QuerySet, list], export_writer: ExporterWriter, row=None):
        """
        :param qs: queryset or list ob objects
        :param export_writer: object that implements ExporterWriter interface and allows to write
        :param row:
        """
        raise NotImplementedError()


class NestedVertical(NestedExporter):
    def export(self, qs: [QuerySet, list], export_writer: ExporterWriter, row=None):
        """
        :param qs: queryset or list ob objects
        :param export_writer: object that implements ExporterWriter interface and allows to write
        :param row:
        """
        object_exporters = [
            [obj, self.exporters[0]] for obj in qs
        ]
        return self.export_objects(object_exporters, export_writer, row=row)

    def export_objects(self, object_exporters: [[object, ModelExporter]], export_writer: ExporterWriter, row=None):
        return_shift = Shift()
        for exporter, obj in object_exporters:
            shift = exporter.export_obj(obj, export_writer, row=row)
            row += 1
            row += shift.row
            return_shift += shift


class NestedHorizontal(NestedExporter):

    def export(self, qs: [QuerySet, list], export_writer: ExporterWriter, row=None):
        """
        :param qs: queryset or list ob objects
        :param export_writer: object that implements ExporterWriter interface and allows to write
        :param row:
        """
        count_objects = len(qs)
        count_exporters = self.get_number()

        append_n = count_objects - count_exporters
        if append_n > 0:
            export_writer.move_left(
                x_from=self.col_end() + 1,
                steps=self.exporter_class.get_size() * append_n,
            )
            [self.new() for _ in range(append_n)]

        object_exporters = zip(self.exporters, qs)
        return self.export_objects(object_exporters, export_writer, row=row)

    def export_objects(self, object_exporters: [[object, ModelExporter]], export_writer: ExporterWriter, row=None):
        return_shift = Shift()
        for exporter, obj in object_exporters:
            shift = exporter.export_obj(obj, export_writer, row=row)
            return_shift += shift

        return return_shift

    def col_start(self):
        if len(self.exporters) == 0:
            return None

        return self.exporters[0]._col_start

    def col_end(self):
        if len(self.exporters) == 0:
            return None
        return self.exporters[0]._col_end


def nested_vertical(model_exporter_class: type(ModelExporter)):
    return NestedExporter(exporter_class=model_exporter_class)


def nested_horizontal(model_exporter_class: type(ModelExporter)):
    return NestedExporter(exporter_class=model_exporter_class)
