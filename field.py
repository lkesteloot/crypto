
from common import find_inverse
from random import randrange

# Finite field math.
class Field:
    def __init__(self, size):
        self.size = size

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

