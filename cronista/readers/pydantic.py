from pydantic.fields import ModelField

from cronista.base import ModelReader


class PydanticModelReader(ModelReader):

    def get_field_name(self, field_name: str):
        return self._get_model_field(field_name).field_info.title

    def get_field_value(self, obj, field_name: str):
        return obj[field_name]

    def get_related_field_value(self, obj, field_name: str):
        value = self.get_field_value(obj, field_name)

        is_list = isinstance(value, list)
        is_dict = isinstance(value, dict)

        if is_list:
            data = value
        elif is_dict:
            data = [value]
        else:
            raise ValueError(f'Field {field_name} is not supported by model reader {self.__class__.__name__}')

        return data

    def _get_model_field(self, field_name) -> ModelField:
        return self.model.__fields__[field_name]
