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


class ModelFieldsExporter(ModelFieldMixin):
    fields = ()
    nested_exporters = {}

    def __init__(self, model: models.Model = None):
        self.model = model or self.model
        if self.model is None:
            raise NotImplementedError('Model must be specified')


class BaseQuerySetExporter(ModelFieldsExporter, BaseExporter):
    """
    A class used to declare an exporter
    :param model - django Model for export
    :param fields - fields to export
    :param exporters - a dict containing exporter classes for FK, O2O, M2M,
        related FK fields. Every exporter should be an instance of one
        class from fields.py module

    Execution:
    1. fields to export can be passed during __init__ or the fields declared on
        class level will be used;
    2. during __init__ all fields will be divided into ObjectExporters depending on field type.
        ObjectExporter is a class that describes field headers and values
    """

    def __init__(self, qs, fields=(), *args, **kwargs):
        self.qs = qs
        super().__init__(*args, **kwargs)

        self.fields = fields or self.fields
        self.model_exporters = self.init_model_exporters()

    def get_queryset(self):
        """Hook to annotate queryset"""
        return self.qs

    def init_model_exporters(self):
        """
        Returns list of model exporters

        First one is ModelExporter for not relation fields of model
        For every relation field (FK, M2M, O2O, reverse FK) a new model exporter is created
        """
        models_exporters: [ObjectExporter] = list()
        non_relation_fields = []

        for name in self.fields:
            model_field = self.get_model_field(name)

            if not model_field.is_relation:
                non_relation_fields.append(name)
                continue

            is_m2o = isinstance(model_field, models.ManyToOneRel)  # related fks
            is_m2m = isinstance(model_field, models.ManyToManyField)
            is_o2o = isinstance(model_field, models.OneToOneField)
            is_fk = isinstance(model_field, models.ForeignKey)

            if is_m2o or is_fk or is_m2m or is_o2o:
                field_exporter_class = self.nested_exporters.get(model_field.name)
                if field_exporter_class is None:
                    raise ValueError(
                        'Exporter for field {name} is not specified '
                        'in `nested_exporters` attribute of {exporter} class'.format(
                            name=name, exporter=self.__class__.__name__
                        ))

                models_exporters.append(field_exporter_class(name=model_field.name))

            else:
                raise ValueError('Field {name} of type {typ} is unsupported by exporter {exporter}'.format(
                    name=name,
                    typ=type(model_field),
                    exporter=self.__class__.__name__
                ))

        # exporter for all non relation fields
        non_relation_exporter = ObjectExporter(model=self.model, fields=tuple(non_relation_fields))
        models_exporters.insert(0, non_relation_exporter)
        return models_exporters

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
        for model_exporter in self.model_exporters:
            self.get_field_exporter_max_num(model_exporter)
            if previous:
                start += previous.get_size() * previous.max_num

            model_exporter.start_col = start
            previous = model_exporter
