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

    def to_response(self, filename='export'):
        raise NotImplementedError()

    def to_file(self, filename='export'):
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
