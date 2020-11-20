from collections import Iterable
from typing import Dict

from django.db import models
from django.db.models import QuerySet, Model

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

    def get_size(self):
        """
        Returns number of columns that will be done for one object
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
        """TODO: return dynamically depending on headers rows count"""
        return 4

    def export(self, qo: [QuerySet, Model], export_writer: ExporterWriter, row=None):
        """
        :param qo: queryset, list or object
        :param export_writer: object that implements ExporterWriter interface and allows to write
        :param row:
        """
        return_shift = Shift()
        row = row or self.get_start_row()
        col = self._col_start
        if not isinstance(qo, Iterable):
            qo = [qo]

        objects_count = len(qo)
        i = 0
        for obj in qo:
            i += 1
            print('self.export_obj', f'start_col={col}, row={row}', type(obj))
            col, obj_shift = self.export_obj(obj, export_writer, start_col=col, row=row)
            return_shift += obj_shift

            is_not_last_object = objects_count != i
            if self.state == self.HORIZONTAL:
                if col + 1 > self._col_end and is_not_last_object:
                    shift_col = self.get_one_size()
                    export_writer.move_left(self._col_end, shift_col)
                    self.increase_end_col(shift_col)
                    self._number += 1
                    return_shift.increase_col(shift_col)
            elif self.state == self.VERTICAL:
                col = self._col_start
                if is_not_last_object:
                    return_shift.increase_row(1)

            row += return_shift.row

        return return_shift

    def export_obj(self, obj, export_writer: ExporterWriter, start_col, row):
        col = start_col
        for field in self.fields:
            value = self.get_field_value(obj, field)
            export_writer.write(x=col, y=row, value=value)
            col += 1

        return_shift = Shift()
        shift = Shift()
        vertical_duplicate = None
        for name, nested_exporter in self.nested_exporters.items():
            if shift.col != 0:
                nested_exporter.increase_end_col(shift.col)

            col, shift = self._export_nested(
                field_name=name,
                obj=obj,
                exporter=nested_exporter,
                export_writer=export_writer,
                col=col,
                row=row
            )
            print(f'Increase shift: {shift}, col={col}')
            return_shift += shift

            if nested_exporter.state == ModelExporter.VERTICAL:
                vertical_duplicate = nested_exporter

        duplicate_near_vertical(row, vertical_duplicate, export_writer)

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
            data = getattr(obj, field_name)
        else:
            raise ValueError(f'Field {field_name} of type {type(model_field)} is '
                             f'not supported by exporter {exporter.__class__.__name__}')
        exporter.set_start_end(col_start=col)
        shift = exporter.export(qo=data, export_writer=export_writer, row=row)
        print(f'Done nested: {col}, size= {exporter.get_size()}')
        return col + exporter.get_size(), shift

    def increase_end_col(self, shift_col):
        """TODO: name"""
        self._col_end += shift_col

    def export_header(self, exporter_writer: ExporterWriter, row=1, col=None):
        col = col or self._col_start
        for _ in range(self.get_number()):
            for field in self.fields:
                value = self.get_model_field_verbose_name(field)
                exporter_writer.write(x=col, y=row, value=value)
                col += 1

        for name, nested_exporter in self.nested_exporters.items():
            nested_row = row + 1
            value = self.get_model_field_verbose_name(name)
            exporter_writer.write(x=nested_exporter._col_start, y=row, value=value)
            col = nested_exporter.export_header(exporter_writer, row=nested_row)

        return col


def duplicate_near_vertical(row, exporter: ModelExporter, exporter_writer: ExporterWriter):
    if not exporter:
        return

    for i in range(exporter.get_number()):
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
