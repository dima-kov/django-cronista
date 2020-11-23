from typing import Dict

from django.db import models
from django.db.models import QuerySet

from cronista.base import ExporterWriter
from cronista.base.shift import Shift


class ModelMixin:
    """
    Mixin for setting model and dynamically getting field details
    """
    model: models.Model = None

    def get_model_field_verbose_name(self, name):
        field = self.get_model_field(name)
        if isinstance(field, models.ManyToOneRel):
            return field.related_model._meta.verbose_name_plural

        return field.verbose_name

    def get_model_field(self, name):
        return self.model._meta.get_field(name)


class ModelExporter(ModelMixin):
    HORIZONTAL = 1
    VERTICAL = 2

    fields = ()
    nested_exporters: Dict[str, 'ModelExporter'] = {}
    state = VERTICAL

    def __init__(self, *args, **kwargs):
        if self.model is None:
            raise NotImplementedError('Model must be specified')

        self._col_start = None
        self._col_end = None
        self._number = 1
        self.set_start_end()
        super().__init__(*args, **kwargs)

    def get_number(self):
        """
        Returns how many times model exporter is placed on sheet
        """
        return self._number

    def increase_number(self):
        """
        Returns how many times model exporter is placed on sheet
        """
        self._number += 1

    def get_size(self):
        """
        Number of columns used by exporter
        If there are 5 fields set and 2 objects - size is equal 10
        """
        size = len(self.fields) * self.get_number()
        for exporter in self.nested_exporters.values():
            size += exporter.get_size()

        return size

    def get_one_size(self):
        """
        Returns number of columns that will be done for one object
        """
        size = len(self.fields)
        for exporter in self.nested_exporters.values():
            size += exporter.get_one_size()

        return size

    def set_start_end(self, col_start=1):
        """
        Sets start & end column
        """
        self._col_start = col_start
        self._col_end = self._col_start + self.get_size()

    def get_start_row(self):
        """
        TODO: return dynamically depending on headers rows count
        """
        raise NotImplementedError()

    def export(self, qs: [QuerySet, list], export_writer: ExporterWriter, row=None):
        """
        :param qs: queryset or list ob objects
        :param export_writer: object that implements ExporterWriter interface and allows to write
        :param row:
        """
        return_shift = Shift()
        row = row or self.get_start_row()
        col = self._col_start

        objects_number = len(qs)
        objects_counter = 0
        for obj in qs:
            objects_counter += 1

            col, shift = self.export_obj(obj, export_writer, col=col, row=row)
            row += shift.row
            return_shift += shift

            if objects_number == objects_counter:
                # this was the last object
                continue

            col, shift = self.after_object_shift(col, export_writer)
            row += shift.row
            return_shift += shift

        return return_shift

    def after_object_shift(self, col, export_writer):
        """
        Determines how to export next object
        should be called only if a next object exists

        Horizontal:
        if current column is same as end column, then
            1. sheet needs to be moved left for number of columns needed for exporting one object
            2. number of horizontal objects increased (self.increase_number())
            3. end_col is increased for same number as in 1

        Vertical:
            1. move col to start
            2. row is increased
        """
        return_shift = Shift()

        if self.state == self.HORIZONTAL:
            the_end = col == self._col_end
            if the_end:
                # there are no space more
                cols = self.get_one_size()
                export_writer.move_left(self._col_end, cols)
                self.increase_end_col(cols)
                self.increase_number()
                return_shift.increase_col(cols)

        elif self.state == self.VERTICAL:
            col = self._col_start
            return_shift.increase_row(1)

        return col, return_shift

    def export_obj(self, obj, export_writer: ExporterWriter, col: int, row: int):
        """
        Writes one object on the sheet
        """
        for field in self.fields:
            value = self.get_field_value(obj, field)
            export_writer.write(x=col, y=row, value=value)
            col += 1

        return_shift, nested_shift = Shift(), Shift()
        vertical, vertical_objects = None, None

        for name, nested_exporter in self.nested_exporters.items():
            if nested_shift.col != 0:
                nested_exporter.increase_end_col(nested_shift.col)

            col, nested_shift, objects_exported = self._export_nested(
                field_name=name,
                obj=obj,
                exporter=nested_exporter,
                export_writer=export_writer,
                col=col,
                row=row
            )
            return_shift += nested_shift

            # Save vertical exporter into variable
            # pretty temporary and not abstract solution
            if nested_exporter.state == ModelExporter.VERTICAL:
                vertical = nested_exporter
                vertical_objects = objects_exported

        duplicate_near_exporter(row, vertical, vertical_objects, export_writer)

        return col, return_shift

    def get_field_value(self, obj, field_name: str):
        display_attr = f'get_{field_name}_display'
        is_choice = hasattr(obj, display_attr)
        if is_choice:
            return getattr(obj, display_attr)()

        return getattr(obj, field_name)

    def _export_nested(self, field_name: str, obj, exporter: 'ModelExporter', export_writer: ExporterWriter, col: int,
                       row: int):
        model_field = self.get_model_field(field_name)
        is_m2o = isinstance(model_field, models.ManyToOneRel)  # related fks
        is_m2m = isinstance(model_field, models.ManyToManyField)
        is_o2o = isinstance(model_field, models.OneToOneField)
        is_fk = isinstance(model_field, models.ForeignKey)

        if is_m2o or is_m2m:
            field = getattr(obj, field_name)
            data = getattr(field, 'all')()
        elif is_o2o or is_fk:
            obj = getattr(obj, field_name)
            data = [obj]
        else:
            raise ValueError(f'Field {field_name} of type {type(model_field)} is '
                             f'not supported by exporter {exporter.__class__.__name__}')

        exporter.set_start_end(col_start=col)
        shift = exporter.export(qs=data, export_writer=export_writer, row=row)
        return col + exporter.get_size(), shift, len(data)

    def increase_end_col(self, shift_col):
        self._col_end += shift_col

    def export_header(self, exporter_writer: ExporterWriter, row=1, col=None):
        col = col or self._col_start
        for _ in range(self.get_number()):
            for field in self.fields:
                value = self.get_model_field_verbose_name(field)
                exporter_writer.write(x=col, y=row, value=value)
                col += 1

            for name, nested_exporter in self.nested_exporters.items():
                value = self.get_model_field_verbose_name(name)
                exporter_writer.write(x=nested_exporter._col_start, y=row, value=value)
                exporter_writer.merge_range(
                    min_col=nested_exporter._col_start,
                    min_row=row,
                    max_col=nested_exporter._col_end-1,
                    max_row=row
                )

                col = nested_exporter.export_header(exporter_writer, row=row + 1)

        return col


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
            max_col=exporter._col_start - 1,
            max_row=row,
            row_shift=row_shift,
        )

        # duplicate after
        exporter_writer.duplicate_range(
            min_col=exporter._col_start + 1,
            min_row=row,
            max_col=None,
            max_row=row,
            row_shift=row_shift,
        )
