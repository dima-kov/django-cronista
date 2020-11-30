from django.db.models import QuerySet

from cronista.base import ModelExporter, ExporterWriter
from cronista.base.model import ColumnWidthExporter
from cronista.base.shift import Shift


class NestedExporter(ColumnWidthExporter):
    """
    Class defines logic for exporting queryset
    """

    def __init__(self, exporter_class: type(ModelExporter), *args, **kwargs):
        self.exporter_class: type(ModelExporter) = exporter_class
        self.exporters: [ModelExporter] = []
        super().__init__(*args, **kwargs)
        self.new()

    def get_number(self):
        """
        Returns how many times model exporter is placed on sheet
        """
        return len(self.exporters)

    def get_size(self):
        return self.exporter_class.get_size() * self.get_number()

    def new(self):
        """
        Method creates new object of export_class

        If there are any exporter already:
        - new exporter start_col will from the last object's end column;
        - size of shift will be exporter size;
        """
        already_has = len(self.exporters) > 0
        column = self.exporters[-1].column_end + 1 if already_has else self.column_start
        exporter: ModelExporter = self.exporter_class(column_start=column)
        self.exporters.append(exporter)

        shift_col = exporter.get_size()
        if already_has is False:
            shift_col -= 1
        self.shift_end_column(shift_col)
        return shift_col

    def shift(self, columns_shift: int):
        super().shift(columns_shift)
        for exporter in self.exporters:
            exporter.shift(columns_shift)

    def export(self, qs: [QuerySet, list], export_writer: ExporterWriter, row=None):
        """
        :param qs: queryset or list ob objects
        :param export_writer: object that implements ExporterWriter interface and allows to write
        :param row:
        """
        raise NotImplementedError()

    def export_header(self, export_writer: ExporterWriter, row: int):
        for exporter in self.exporters:
            exporter.export_header(exporter_writer=export_writer, row=row)

    def debug_structure(self):
        print(f'({self.__class__.__name__} of {self.exporter_class.__name__}): {self.column_start} - {self.column_end}')
        for exporter in self.exporters:
            exporter.debug_structure()
        print('\n')


class NestedVertical(NestedExporter):

    def export(self, qs: [QuerySet, list], export_writer: ExporterWriter, row=None):
        """
        :param qs: queryset or list ob objects
        :param export_writer: object that implements ExporterWriter interface and allows to write
        :param row:
        """
        exporter = self.exporters[0]
        object_exporters = [
            [obj, exporter] for obj in qs
        ]
        shift = self.export_objects(object_exporters, export_writer, row=row)
        duplicate_near_exporter(row, exporter, len(qs) - 1, export_writer)
        shift.increase_row(len(qs) - 1 if qs else 0)
        return shift

    def export_objects(self, object_exporters: [[object, ModelExporter]], export_writer: ExporterWriter, row=None):
        return_shift = Shift()
        for obj, exporter in object_exporters:
            shift = exporter.export_obj(obj, export_writer, row=row)
            row += 1
            row += shift.row
            return_shift += shift
            self.shift_end_column(shift.col)

        return return_shift

    def export_header(self, export_writer: ExporterWriter, row: int):
        for exporter in self.exporters:
            exporter.export_header(exporter_writer=export_writer, row=row)

    def _is_vertical(self):
        return False


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
        return_shift = Shift()
        if append_n > 0:
            for _ in range(append_n):
                export_writer.move_left(
                    x_from=self.column_end + 1,
                    steps=self.exporter_class.get_size(),
                )
                shift_col = self.new()
                return_shift.increase_col(shift_col)

        object_exporters = zip(self.exporters, qs)
        shift = self.export_objects(object_exporters, export_writer, row=row)
        return return_shift + shift

    def export_objects(self, object_exporters: [[object, ModelExporter]], export_writer: ExporterWriter, row=None):
        return_shift = Shift()
        shift = Shift()
        for exporter, obj in object_exporters:
            exporter.shift(shift.col)
            shift = exporter.export_obj(obj, export_writer, row=row)
            row += shift.row
            return_shift += shift

            self.shift_end_column(shift.col)

        return return_shift

    def col_start(self):
        if len(self.exporters) == 0:
            return None

        return self.exporters[0]._col_start

    def col_end(self):
        if len(self.exporters) == 0:
            return None
        return self.exporters[0]._col_end

    def export_header(self, export_writer: ExporterWriter, row: int):
        for exporter in self.exporters:
            exporter.export_header(exporter_writer=export_writer, row=row)

    def _is_vertical(self):
        return False


def nested_vertical(model_exporter_class: type(ModelExporter), column_start):
    return NestedVertical(exporter_class=model_exporter_class, column_start=column_start)


def nested_horizontal(model_exporter_class: type(ModelExporter), column_start):
    return NestedHorizontal(exporter_class=model_exporter_class, column_start=column_start)


def duplicate_near_exporter(row, exporter: ModelExporter, times: int, exporter_writer: ExporterWriter):
    """
    Copies all content near exporter to next rows
    """
    if not exporter:
        return

    if times < 2:
        return

    for i in range(times):
        # duplicate before
        row_shift = i + 1
        exporter_writer.duplicate_range(
            min_col=1,
            min_row=row,
            max_col=exporter.column_start - 1,
            max_row=row,
            row_shift=row_shift,
        )

        # duplicate after
        exporter_writer.duplicate_range(
            min_col=exporter.column_end + 1,
            min_row=row,
            max_col=None,
            max_row=row,
            row_shift=row_shift,
        )
