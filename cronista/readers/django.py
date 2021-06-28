from django.db import models

from cronista.base import ModelReader


class DjangoModelReader(ModelReader):

    def get_field_name(self, field_name: str):
        field = self._get_model_field(field_name)
        if isinstance(field, models.ManyToOneRel):
            return field.related_model._meta.verbose_name_plural

        return field.verbose_name

    def get_field_value(self, obj, field_name: str):
        display_attr = f'get_{field_name}_display'
        is_choice = hasattr(obj, display_attr)
        if is_choice:
            return getattr(obj, display_attr)()

        field = self._get_model_field(field_name)
        value = getattr(obj, field_name)

        if isinstance(field, models.DateField):
            if not value:
                return
            return value.strftime("%d.%m.%Y")

        return value

    def get_related_field_value(self, obj, field_name: str):
        model_field = self._get_model_field(field_name)
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
                             f'not supported by mode reader {self.__class__.__name__}')

        return data

    def _get_model_field(self, field_name):
        return self.model._meta.get_field(field_name)
