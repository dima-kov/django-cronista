from typing import Dict

from django.db import models
from django.db.models import DateField

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


class ColumnWidthExporter(object):

    def __init__(self, column_start: int, *args, **kwargs):
        self.column_start = column_start
        self.column_end = self._count_end_column()
        super().__init__(*args, **kwargs)

    def shift(self, columns_shift: int):
        self.column_start += columns_shift
        self.column_end += columns_shift

    def shift_end_column(self, columns_shift: int):
        self.column_end += columns_shift

    def _count_end_column(self):
        size = self.get_size()
        normalized_size = size - 1 if size > 0 else size
        return self.column_start + normalized_size

    def get_size(self):
        raise NotImplementedError()


def init_nested(exporter: 'ModelExporter', start_col):
    from cronista.base.nested import nested_vertical, nested_horizontal

    if exporter.state == ModelExporter.HORIZONTAL:
        return nested_horizontal(exporter, start_col)

    elif exporter.state == ModelExporter.VERTICAL:
        return nested_vertical(exporter, start_col)

    else:
        raise ValueError('Error')


class ModelExporter(ColumnWidthExporter, ModelMixin):
    """
    Class for exporting one object into sheet using exporter_writer

    state - defines export direction: horizontal or vertical
    fields - defines list of fields to export
        exporter reads data from these fields and places data into appropriate cells
    related - defines related exporters, e.g. for m2m objects, lists, nested dicts
    """
    HORIZONTAL = 1
    VERTICAL = 2

    fields = ()
    related: Dict[str, 'ModelExporter'] = {}
    state = VERTICAL

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.model is None:
            raise NotImplementedError('Model must be specified')

        self.nested_exporters: Dict[str, 'NestedExporter'] = self.init_nested()

    def debug_structure(self):
        print(f'{self.__class__.__name__}: {self.column_start} - {self.column_end}')
        for name, nested in self.nested_exporters.items():
            nested.debug_structure()

    def init_nested(self):
        """
        Method creates objects of NestedVertical or NestedHorizontal
        for related fields based on their exporters
        """
        nested = {}
        col = self.column_start + self.get_fields_size()
        for name, exp in self.related.items():
            nested[name] = init_nested(exp, col)
            col += nested[name].get_size()

        return nested

    @classmethod
    def get_fields_size(cls):
        """Returns size of fields"""
        return len(cls.fields)

    @classmethod
    def get_size(cls):
        """
        Returns number of columns needed for exporting one object
        """
        size = cls.get_fields_size()
        for exporter in cls.related.values():
            size += exporter.get_size()

        return size

    @classmethod
    def get_start_row(cls):
        """Start from next row"""
        return cls.get_depth() + 1

    @classmethod
    def get_depth(cls):
        if cls.related == {}:
            return 1
        else:
            return max([e.get_depth() for e in cls.related.values()]) + 1

    def shift(self, columns_shift: int):
        """
        Performs shift of all nested exporters
        """
        super().shift(columns_shift)
        for nested in self.nested_exporters.values():
            nested.shift(columns_shift)

    def export(self, qs, exporter_writer):
        """
        Export entry point. Used only once for the first exporter
        """
        qs = self.annotate_qs(qs)
        row = self.get_start_row()
        shift = Shift()
        for obj in qs:
            self.shift_end_column(shift.col)
            shift = self.export_obj(obj, exporter_writer, row=row)
            row += shift.row
            row += 1

        self.export_header(exporter_writer)
        self.export_header_after(exporter_writer)

    def annotate_qs(self, qs):
        return qs

    def export_obj(self, obj, export_writer: ExporterWriter, row: int):
        """
        Exports one object on the sheet start from column and on row

        Returns shift - how col and row for next export object should be changed
        """

        def shift_nested_after(_name, shift_col):
            """Shifts all nested exporters after those with name `_name`"""
            all_names = list(self.nested_exporters.keys())
            current_index = all_names.index(_name)
            to_shift_names = all_names[current_index + 1:]
            [self.nested_exporters[_nested].shift(shift_col) for _nested in to_shift_names]

        col = self.column_start
        for field in self.fields:
            value = self.get_field_value(obj, field)
            export_writer.write(x=col, y=row, value=value)
            col += 1

        return_shift = Shift()
        for name, nested in self.nested_exporters.items():
            shift = self._export_nested(name, obj, nested, export_writer, row)
            return_shift += shift
            shift_nested_after(name, shift.col)

        self.shift_end_column(return_shift.col)

        return return_shift

    def _export_nested(self, field_name: str, obj, nested_exporter: 'NestedExporter', export_writer: ExporterWriter,
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
            data = [obj]  # fake qs
        else:
            raise ValueError(f'Field {field_name} of type {type(model_field)} is '
                             f'not supported by exporter {nested_exporter.exporter_class.__class__.__name__}')

        return nested_exporter.export(qs=data, export_writer=export_writer, row=row)

    def get_field_value(self, obj, field_name: str):
        """
        This field returns raw data that will be places into file

        In future for better design, it should be split into separate class
        to specify format, use choice, or override, etc
        """
        display_attr = f'get_{field_name}_display'
        is_choice = hasattr(obj, display_attr)
        if is_choice:
            return getattr(obj, display_attr)()

        field = self.get_model_field(field_name)
        if isinstance(field, DateField):
            date = getattr(obj, field_name)
            if not date:
                return
            return date.strftime("%d.%m.%Y")

        return getattr(obj, field_name)

    def export_header(self, exporter_writer: ExporterWriter, row=1):
        col = self.column_start
        # print(f'{self.__class__.__name__}: {self.column_start} - {self.column_end}')
        for field in self.fields:
            depth = self.get_depth()
            exporter_writer.merge_range(
                min_col=col,
                min_row=row,
                max_col=col,
                max_row=row + depth - 1 if depth > 1 else row
            )

            value = self.get_model_field_verbose_name(field)
            exporter_writer.write(x=col, y=row, value=value)
            col += 1

        for name, nested_exporter in self.nested_exporters.items():
            # print(
            #     f'Nested: {nested_exporter.__class__.__name__} of {name}: '
            #     f'{nested_exporter.column_start}, {nested_exporter.column_end} in {row} + 1'
            # )
            value = self.get_model_field_verbose_name(name)
            exporter_writer.write(x=nested_exporter.column_start, y=row, value=value)
            exporter_writer.merge_range(
                min_col=nested_exporter.column_start,
                min_row=row,
                max_col=nested_exporter.column_end,
                max_row=row
            )

            nested_exporter.export_header(exporter_writer, row=row + 1)

    def export_header_after(self, exporter_writer: ExporterWriter):
        exporter_writer.freeze_panes(col=1, row=self.get_start_row())
