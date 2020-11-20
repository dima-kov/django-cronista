from unittest import TestCase

from cronista.base.shift import Shift


class ShiftTestCase(TestCase):

    def test(self):
        s_start = Shift()
        self.assertEqual(s_start.col, 0)
        self.assertEqual(s_start.row, 0)

        s_start += Shift(row=30)
        self.assertEqual(s_start.col, 0)
        self.assertEqual(s_start.row, 30)
