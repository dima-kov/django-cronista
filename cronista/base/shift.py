class Shift(object):
    def __init__(self, row=0, col=0):
        self.row = row
        self.col = col

    def __str__(self):
        return f'<Shift row={self.row}, col={self.col}>'

    def __repr__(self):
        return self.__str__()

    def increase_row(self, value):
        self.row += value

    def increase_col(self, value):
        self.col += value

    def __add__(self, other: 'Shift'):
        if not isinstance(other, Shift):
            raise TypeError(f'Shift other ({other}) should be instance of Shift')

        return Shift(
            row=other.row + self.row,
            col=other.col + self.col,
        )
