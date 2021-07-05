import abc


class ExporterWriter(abc.ABC):
    """
    Class for every specific file write implementations
    """

    def write(self, x, y, value):
        """
        Method should implement logic of writing data
        """
        raise NotImplementedError()

    def move_left(self, x_from, steps):
        """
        Method should implement logic of moving all data from x_from for steps
        """
        raise NotImplementedError()

    def duplicate_range(self, min_col, min_row, max_col, max_row, row_shift=0, col_shift=0):
        """
        Method should implement copying all values from range defined by
        min_col, min_row, max_col, max_row
        to the range of the same dimension but with shift on row or col
        """
        raise NotImplementedError()

    def merge_range(self, min_col, min_row, max_col, max_row):
        """Method should merge range"""
        raise NotImplementedError()

    def freeze_panes(self, col, row):
        """Method should freeze range"""
        raise NotImplementedError()

    def to_response(self, filename='export'):
        raise NotImplementedError()

    def to_file(self, filename='export'):
        raise NotImplementedError()

    def to_binary(self):
        raise NotImplementedError()


class BaseExporter(abc.ABC):

    def __init__(self, exporter_writer: ExporterWriter):
        self.exporter_writer = exporter_writer

    def export(self, *args, **kwargs):
        raise NotImplementedError()

    def as_http_response(self, filename=None):
        return self.exporter_writer.to_response(filename)

    def as_file(self, filename=None):
        return self.exporter_writer.to_file(filename)

    def as_binary(self):
        return self.exporter_writer.to_binary()


class ModelReader(object):
    """
    All logic reading data from models, e.g. django model, pydantic model, etc
    """

    def __init__(self, model=None):
        self.model = model

    def get_field_name(self, field_name: str):
        raise NotImplementedError()

    def get_field_value(self, obj, field_name: str):
        raise NotImplementedError()

    def get_related_field_value(self, obj, field_name: str):
        raise NotImplementedError()
