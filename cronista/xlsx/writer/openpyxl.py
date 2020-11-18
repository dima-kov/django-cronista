from urllib.parse import quote

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.worksheet.cell_range import CellRange
from openpyxl.writer.excel import save_virtual_workbook

from cronista.base import ExporterWriter


class _MaxColRow(object):

    def __init__(self):
        self._max_col = 0
        self._max_row = 0

    @property
    def max_col(self):
        return self._max_col

    @max_col.setter
    def max_col(self, value):
        if value > self._max_col:
            self._max_col = value

    @property
    def max_row(self):
        return self._max_row

    @max_row.setter
    def max_row(self, value):
        if value > self._max_row:
            self._max_row = value


class OpenPyXlWriter(ExporterWriter, _MaxColRow):
    default_value = '-'

    def __init__(self):
        super().__init__()
        self.wb = Workbook()
        self.ws = self.wb.active

    def write(self, x, y, value):
        value = value or self.default_value
        self.ws.cell(row=y, column=x, value=str(value))
        self.max_col = x
        self.max_row = y

    def move_left(self, x_from, steps):
        print('move!!!', x_from, steps)
        c = CellRange(min_col=x_from, min_row=3, max_col=self.max_col + 100, max_row=self.max_row)
        self.ws.move_range(c, rows=0, cols=steps)

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
