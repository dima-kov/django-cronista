from typing import Dict

from django.db import models
from django.db.models import QuerySet, Model

from cronista.base import BaseExporter, ExporterWriter


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
            size += exporter.get_size() * exporter.get_size()

        return size

    # def get_real_size(self):
    #     """
    #     Returns number of columns to be exported by exporter including nested exporter fields
    #     """
    #     return self.get_static_size() * self.get_number()
    #     # size = len(self.fields) * self.get_number()
    # for exporter in self.nested_exporters.values():
    #     size += exporter.get_size() * exporter.get_number()()`
    #
    # return size

    def set_start_end(self, col_start=1):
        """
        Sets start & end column
        """
        self._col_start = col_start
        self._col_end = self._col_start + self.get_size()

    def get_start_row(self):
        """TODO: return dynamically depending on headers rows count"""
        return 3

    def export(self, qo: [QuerySet, Model], export_writer: ExporterWriter, row=None):
        """
        :param qo: queryset, list or object
        :param export_writer: object that implements ExporterWriter interface and allows to write
        :param row:
        """
        return_shift = 0
        row = row or self.get_start_row()
        col = self._col_start
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
                    shift_col = self.get_size()
                    export_writer.move_left(self._col_end + 1, shift_col)
                    self.increase_end_col(shift_col)
                    self._number += 1
                    return_shift += shift_col
            elif self.state == self.VERTICAL:
                row += 1
                col = self._col_start

        return return_shift

    def export_obj(self, obj, export_writer: ExporterWriter, start_col, row):
        col = start_col
        for field in self.fields:
            value = getattr(obj, field)
            export_writer.write(x=col, y=row, value=value)
            col += 1

        return_shift = 0
        shift_col = 0
        for name, nested_exporter in self.nested_exporters.items():
            if shift_col != 0:
                nested_exporter.increase_end_col(shift_col)

            col, shift_col = self._export_nested(
                field_name=name,
                obj=obj,
                exporter=nested_exporter,
                export_writer=export_writer,
                col=col,
                row=row
            )
            return_shift += shift_col

        return col, return_shift

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
        shift_col = exporter.export(qo=data, export_writer=export_writer, row=row)
        return col + exporter.get_size(), shift_col

    def increase_end_col(self, shift_col):
        """TODO: name"""
        self._col_end += shift_col
