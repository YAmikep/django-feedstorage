# Python stdlib
import os
from datetime import timedelta, tzinfo, datetime

# Django
from django.test import TestCase

# Internal
from ...utils.loggers import windows_safe, make_safe, to_unicode


class LoggersPathUtilsKnownValues(TestCase):

    def test_windows_safe(self):
        s = 'http://www.djangoproject.com'
        s_windows = 'http;//www.djangoproject.com'
        s_safe = windows_safe(s)

        if os.name == 'nt':
            self.assertEqual(s_safe, s_windows)
        else:
            self.assertEqual(s_safe, s)

    def test_make_safe(self):
        s = 'http://www.djangoproject.com/'
        s_windows_safe = 'http;__www.djangoproject.com_'
        s_safe = 'http:__www.djangoproject.com_'
        result = make_safe(s)

        if os.name == 'nt':
            self.assertEqual(result, s_windows_safe)
        else:
            self.assertEqual(result, s_safe)


class LoggersUnicodeUtilsTestCase(TestCase):

    def test_date(self):
        date_format = '%Y-%m-%dT%H:%M:%S.%f'
        date_string = u'2012-04-15T14:36:40.584000'
        a_date = datetime.strptime(date_string, date_format)

        u_date_converted = to_unicode(a_date, date_format=date_format)

        self.assertEqual(date_string, u_date_converted)

    def test_date_with_tz(self):
        date_format = '%Y-%m-%dT%H:%M:%S.%f%z'
        date_string = u'2012-11-21T16:30:25.322000+0100'

        class GMT1(tzinfo):
            def utcoffset(self, dt):
                return timedelta(hours=1) + self.dst(dt)

            def tzname(self, dt):
                return "GMT +1"

            def dst(self, dt):
                return timedelta(0)

        a_date = datetime(2012, 11, 21, 16, 30, 25, 322000, tzinfo=GMT1())

        u_date_converted = to_unicode(a_date, date_format=date_format)

        self.assertEqual(date_string, u_date_converted)

    def test_int(self):
        a = 7
        u_a = u'7'

        u_int_converted = to_unicode(a)

        self.assertEqual(u_a, u_int_converted)

    def test_boolean(self):
        a = True
        b = False
        u_a = u'True'
        u_b = u'False'

        u1_int_converted = to_unicode(a)
        u2_int_converted = to_unicode(b)

        self.assertEqual(u_a, u1_int_converted)
        self.assertEqual(u_b, u2_int_converted)
