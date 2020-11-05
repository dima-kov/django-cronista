from django.db import models


class ModelFieldMixin:
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
