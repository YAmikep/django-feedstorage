# Django
from django.test import TestCase

# Internal
from ...utils.http import _return


class ReturnUtilKnownValues(TestCase):

    def test_several_values(self):
        known = ('val1', 4)
        result = _return((True, 'val1'), (False, 'val2'), (False, 'val3'), (True, 4))

        self.assertEqual(known, result)

    def test_one_value(self):
        known = 4
        result = _return((False, 'val1'), (False, 'val2'), (False, 'val3'), (True, 4))

        self.assertEqual(known, result)
