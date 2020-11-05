from cronista.base.mixins import ModelMixin


class ObjectExporter(ModelMixin):
    """
    A class that describes export data for one object
    :parameter name
    """
    name = None
    fields = ()
    multiple = False

    max_num = 1
    start_col = 1

    def __init__(self, model=None, name=None, fields=()):
        self.model = model or self.model
        self.name = name or self.name
        self.fields = self.fields + fields

    def get_size(self):
        """Returns number of fields to export"""
        return len(self.fields)

    def get_end_col(self):
        return self.start_col + self.get_size() * self.max_num - 1

    def get_fields_verbose_names(self):
        return [self.get_model_field_verbose_name(f) for f in self.fields]

    def get_data_set(self, obj):
        for f in self.fields:
            yield getattr(obj, f)


class MultipleObjectsExporter(ObjectExporter):
    multiple = True

    def get_data_set(self, qs):
        for obj in qs:
            for value in super().get_data_set(obj):
                yield value
