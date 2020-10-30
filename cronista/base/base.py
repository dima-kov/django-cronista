import abc

from django.db import models

from cronista.base.fields import ObjectExporter
from cronista.base.mixins import ModelFieldMixin


class BaseExporter(abc.ABC):

    def export(self):
        raise NotImplementedError()

    def as_http_response(self):
        raise NotImplementedError()

    def as_file(self):
        raise NotImplementedError()


class BaseModelExporter(BaseExporter, ModelFieldMixin):
    """
    A class used to declare an exporter
    :param model - django Model for export
    :param fields - fields to export
    :param exporters - a dict containing exporter classes for FK, O2O, M2M,
        related FK fields. Every exporter should be an instance of one
        class from fiels.py module

    Execution:
    1. fields to export can be passed during __init__ or the fields declared on
        class level will be used;
    2. during __init__ all fields will be divided into ObjectExporters depending on field type.
        ObjectExporter is a class that describes field headers and values
    """
    fields = ()
    exporters = {}
    field_exporters = None

    def __init__(self, qs, fields=()):
        self.qs = qs
        if self.model is None:
            raise NotImplementedError()

        self.fields = fields or self.fields
        self.init_field_exporters()

    def get_queryset(self):
        """Hook to annotate queryset"""
        return self.qs

    def init_field_exporters(self):
        self.field_exporters: [ObjectExporter] = list()
        non_relation_fields = []

        for name in self.fields:
            field = self.get_field(name)

            if not field.is_relation:
                non_relation_fields.append(name)
                continue

            is_m2o = isinstance(field, models.ManyToOneRel)  # related fks
            is_m2m = isinstance(field, models.ManyToManyField)
            is_o2o = isinstance(field, models.OneToOneField)
            is_fk = isinstance(field, models.ForeignKey)

            if is_m2o or is_fk or is_m2m or is_o2o:
                field_exporter_class = self.exporters.get(field.name)
                if field_exporter_class is None:
                    raise ValueError('Exporter for field {} is not specified in {}'.format(
                        name, self.__class__.__name__
                    ))

                self.field_exporters.append(field_exporter_class(name=field.name))

            else:
                raise ValueError('Field {} of type {} is unsupported by exporter {}'.format(
                    name, type(field), self.__class__.__name__
                ))

        # exporter for all non relation fields
        non_relation_exporter = ObjectExporter(model=self.model, fields=tuple(non_relation_fields))
        self.field_exporters.insert(0, non_relation_exporter)

    def get_field_exporter_max_num(self, field_exporter: ObjectExporter):
        """A method to return max number of FieldExporter objects in queryset"""
        if not field_exporter.multiple:
            # default value: 1
            return

        field = field_exporter.name
        count_name = '{}_num'.format(field)
        number = self.qs.annotate(
            **{count_name: models.Count(field)}
        ).aggregate(max_num=models.Max(count_name))['max_num']

        field_exporter.max_num = number or 1

    def define_start_cols(self, start=1):
        """A method to declare start column for every field exporter"""
        previous = None
        for field_exporter in self.field_exporters:
            self.get_field_exporter_max_num(field_exporter)
            if previous:
                start += previous.get_size() * previous.max_num

            field_exporter.start_col = start
            previous = field_exporter
