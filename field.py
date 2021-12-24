
from common import find_inverse
from random import randrange

# Finite field math.
class Field:
    def __init__(self, size):
        self.size = size

    def value(self, a):
        return FieldValue(self, a)

    def add(self, a, b):
        return (a + b) % self.size

    def subtract(self, a, b):
        return (a - b + self.size) % self.size

    def multiply(self, a, b):
        return (a * b) % self.size

    def divide(self, a, b):
        return self.multiply(a, self.invert(b))

    def negate(self, a):
        return self.subtract(0, a)

    def invert(self, n):
        if n == 0:
            raise Exception("inverse of zero")

        return find_inverse(n, self.size)

    def random(self):
        return randrange(0, self.size)

    def random_not_zero(self):
        return randrange(1, self.size)

# Value in a finite field.
class FieldValue:
    def __init__(self, f, value):
        self.f = f
        self.value = value

    def __repr__(self):
        return str(self.value)

    def __add__(self, o):
        if isinstance(o, int):
            o = self.f.value(o)
        self._checkField(o)
        return FieldValue(self.f, self.f.add(self.value, o.value))

    def __sub__(self, o):
        if isinstance(o, int):
            o = self.f.value(o)
        self._checkField(o)
        return FieldValue(self.f, self.f.subtract(self.value, o.value))

    def __mul__(self, o):
        if isinstance(o, int):
            o = self.f.value(o)
        self._checkField(o)
        return FieldValue(self.f, self.f.multiply(self.value, o.value))

    def __rmul__(self, o):
        return self*o

    def __truediv__(self, o):
        if isinstance(o, int):
            o = self.f.value(o)
        self._checkField(o)
        return FieldValue(self.f, self.f.divide(self.value, o.value))

    def __neg__(self):
        return FieldValue(self.f, self.f.negate(self.value))

    def __eq__(self, o):
        if isinstance(o, int):
            o = self.f.value(o)
        self._checkField(o)
        return self.value == o.value

    def _checkField(self, o):
        assert self.f.size == o.f.size
