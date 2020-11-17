import abc


class BaseExporter(abc.ABC):

    def export(self, *args, **kwargs):
        raise NotImplementedError()

    def as_http_response(self):
        raise NotImplementedError()

    def as_file(self):
        raise NotImplementedError()
