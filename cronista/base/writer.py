import abc


class ExportWriter(abc.ABC):
    def write(self, x, y, value):
        raise NotImplementedError()

    def move_left(self, x_from, steps):
        """
        Method should implement logic of moving all data from x_from for steps
        """
        raise NotImplementedError()
