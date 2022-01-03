
# Elliptic curve math.

from field import Field, FieldValue
import random

class EllipticCurve:
    def __init__(self, f, a, b, Gx, Gy, n):
        self.f = f
        self.a = a
        self.b = b
        self.G = EllipticCurveValue(self, Gx, Gy)
        self.ZERO = EllipticCurveValue(self, self.f.value(0), self.f.value(0))
        self.n = n # Order of G (i.e., G x n = 0)

    def __eq__(self, o):
        # Can't compare G directly, causes infinite regress.
        return self.f.size == o.f.size and \
                self.a == o.a and \
                self.b == o.b and \
                self.G.x == o.G.x and \
                self.G.y == o.G.y

    # Takes tuple of FieldValue.
    def value(self, x, y):
        return EllipticCurveValue(self, x, y)

    # Return a private key and public key.
    def generate_key_pair(self):
        pr = random.randrange(1, self.n)
        pu = self.G*pr
        return pr, pu

    def find_y_for_x(self, x, is_even):
        y_squared = x*x*x + self.a*x + self.b
        y = y_squared.sqrt()
        if (y.value % 2 == 0) != is_even:
            y = -y
        return y

    @staticmethod
    def secp256k1():
        # https://en.bitcoin.it/wiki/Secp256k1
        p = 2**256 - 2**32 - 2**9 - 2**8 - 2**7 - 2**6 - 2**4 - 1
        f = Field(p)
        Gx = f.value(0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798)
        Gy = f.value(0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)
        n = 115792089237316195423570985008687907852837564279074904382605163141518161494337

        return EllipticCurve(f, 0, 7, Gx, Gy, n)

class EllipticCurveValue:
    # Value is tuple of two FieldValue
    def __init__(self, e, x, y):
        self.e = e

        if not isinstance(x, FieldValue):
            raise Exception("x is not a FieldValue:" + repr(x))
        if not isinstance(y, FieldValue):
            raise Exception("y is not a FieldValue:" + repr(y))

        self.x = x
        self.y = y

    def is_on_curve(self):
        if self == 0:
            return True

        x, y = self.x, self.y
        return y*y == x*x*x + self.e.a*x + self.e.b

    def __add__(self, o):
        assert self.e == o.e

        if self == 0:
            return o
        if o == 0:
            return self
        if self == -o:
            return self.e.ZERO

        if self == o:
            # Point doubling.
            dy = 3*self.x*self.x + self.e.a
            dx = 2*self.y
        else:
            # Distinct points.
            dx = o.x - self.x
            dy = o.y - self.y
        slope = dy / dx
        xr = slope*slope - self.x - o.x
        yr = slope*(self.x - xr) - self.y
        return EllipticCurveValue(self.e, xr, yr)

    def __sub__(self, o):
        assert self.e == o.e
        return self + -o

    def __mul__(self, n):
        if isinstance(n, FieldValue):
            n = n.value

        assert isinstance(n, int)

        s = self.e.ZERO
        a = self

        while n != 0:
            if (n & 1) != 0:
                s = s + a

            n >>= 1
            a = a + a

        return s

    def __neg__(self):
        return self.e.value(self.x, -self.y)

    def __eq__(self, o):
        if isinstance(o, int):
            if o == 0:
                return self.x.value == 0 and self.y.value == 0
            else:
                raise Exception("cannot compare with non-zero integer")

        assert self.e == o.e
        return self.x == o.x and self.y == o.y

    def __repr__(self):
        return "(" + repr(self.x) + "," + repr(self.y) + ")"

if __name__ == "__main__":
    e = EllipticCurve.secp256k1()

    print(e.G, e.G.is_on_curve())
    g2 = e.G + e.G
    print(g2, g2.is_on_curve())
    g3_1 = g2 + e.G
    g3_2 = e.G + g2
    g4_1 = g3_1 + e.G
    g4_2 = e.G + g3_1
    g4_3 = g2 + g2
    print(g4_1 == g4_2)
    print(g4_1 == g4_3)
    negG = -e.G

    print("---")
    print(e.ZERO == e.G*0)
    print(e.G == e.G*1)
    print(g2 == e.G*2)
    print(g3_1 == e.G*3)

    q1 = e.G*4
    q2 = q1
    for i in range(4):
        q2 = q2 - e.G
    print(q2)

    print("---")

    q = e.ZERO
    for k in range(5):
        print("k =", k)
        print("x =", hex(q.x.value)[2:].upper())
        print("y =", hex(q.y.value)[2:].upper())
        print(q.is_on_curve())
        print()
        q += e.G

    print(e.G*89329329329382389349238432984379239432)
    print(e.G*e.n)
