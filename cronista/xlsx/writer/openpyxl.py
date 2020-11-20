from urllib.parse import quote

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.worksheet.cell_range import CellRange
from openpyxl.writer.excel import save_virtual_workbook

from cronista.base import ExporterWriter


#
# class _MaxColRow(object):
#
#     def __init__(self):
#         self._max_col = 0
#         self._max_row = 0
#
#     @property
#     def max_col(self):
#         return self._max_col
#
#     @max_col.setter
#     def max_col(self, value):
#         if value > self._max_col:
#             self._max_col = value
#
#     @property
#     def max_row(self):
#         return self._max_row
#
#     @max_row.setter
#     def max_row(self, value):
#         if value > self._max_row:
#             self._max_row = value


class OpenPyXlWriter(ExporterWriter):
    default_value = '-'

    def __init__(self):
        super().__init__()
        self.wb = Workbook()
        self.ws = self.wb.active

    def write(self, x, y, value):
        value = value or self.default_value
        self.ws.cell(row=y, column=x, value=str(value))

    def move_left(self, x_from, steps):
        print('move!!!', x_from, steps)
        print(
            f'min_col={x_from}',
            f'min_row=3',
            f'max_col={self.ws.max_column}',
            f'max_row={self.ws.max_row},\n\n'
        )
        max_col = self.ws.max_column
        if x_from > self.ws.max_column:
            max_col = x_from

        c = CellRange(
            min_col=x_from,
            min_row=3,
            max_col=max_col,
            max_row=self.ws.max_row
        )
        self.ws.move_range(c, rows=0, cols=steps)

    def duplicate_range(self, min_col, min_row, max_col, max_row, row_shift=0, col_shift=0):
        if max_col is None:
            max_col = self.ws.max_column

        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                value = self.ws.cell(row=row, column=col).value
                self.write(
                    x=col + col_shift,
                    y=row + row_shift,
                    value=value,
                )

    def merge_range(self, min_col, min_row, max_col, max_row):
        pass

    def freeze_panes(self, col, row):
        cell = self.ws.cell(row=row, column=col)
        self.ws.freeze_panes = cell

    def to_file(self, filename='export'):
        self.wb.save(filename)

    def to_response(self, filename='export'):
        filename = quote('{}.xlsx'.format(filename))
        response = HttpResponse(
            content=save_virtual_workbook(self.wb),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
        return response
