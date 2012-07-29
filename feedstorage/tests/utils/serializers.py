# Django
from django.test import TestCase

# Internal
from ...utils.serializers import serialize_function, deserialize_function, SerializationFailed, DeserializationFailed


def func1(a):
    return a


class A(object):
    @classmethod
    def classmethod1(cls, a):
        return a


class SerializationDeserializationKnownValues(TestCase):

    def test_function(self):
        f = func1
        ser_f = serialize_function(f)
        g = deserialize_function(ser_f)
        v_a = f(9)
        v_b = g(9)

        self.assertEqual(v_a, v_b)

    def test_classmethod(self):
        f = A.classmethod1
        ser_f = serialize_function(f)
        g = deserialize_function(ser_f)
        v_a = f(9)
        v_b = g(9)

        self.assertEqual(v_a, v_b)

    def test_string_serialization_failed(self):
        f = 'not a function'
        self.assertRaises(SerializationFailed, serialize_function, f)

    def test_none_serialization_failed(self):
        f = None
        self.assertRaises(SerializationFailed, serialize_function, f)

    def test_string_deserialization_failed(self):
        f = 'not a function'
        self.assertRaises(DeserializationFailed, deserialize_function, f)

    def test_none_deserialization_failed(self):
        f = None
        self.assertRaises(DeserializationFailed, deserialize_function, f)
