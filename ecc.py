
# Elliptic curve math.

from field import Field, FieldValue

class EllipticCurve:
    def __init__(self, f, a, b, G):
        self.f = f
        self.a = a
        self.b = b
        self.G = EllipticCurveValue(self, G)
        self.ZERO = EllipticCurveValue(self, (self.f.value(0), self.f.value(0)))

    def __eq__(self, o):
        # Can't compare G directly, causes infinite regress.
        return self.f.size == o.f.size and \
                self.a == o.a and \
                self.b == o.b and \
                self.G.value[0] == o.G.value[0] and \
                self.G.value[1] == o.G.value[1]

    # Takes tuple of FieldValue.
    def value(self, value):
        return EllipticCurveValue(self, value)

    @staticmethod
    def secp256k1():
        # https://en.bitcoin.it/wiki/Secp256k1
        p = 2**256 - 2**32 - 2**9 - 2**8 - 2**7 - 2**6 - 2**4 - 1
        f = Field(p)
        Gx = f.value(0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798)
        Gy = f.value(0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)

        return EllipticCurve(f, 0, 7, (Gx, Gy))

class EllipticCurveValue:
    # Value is tuple of two FieldValue
    def __init__(self, e, value):
        self.e = e

        if not isinstance(value, tuple):
            raise Exception("value is not a tuple: " + repr(value) + " of type " + str(type(value)))
        if len(value) != 2:
            raise Exception("tuple is not of length 2: " + str(len(value)))
        if not isinstance(value[0], FieldValue):
            raise Exception("value[0] is not a FieldValue:" + repr(value[0]))
        if not isinstance(value[1], FieldValue):
            raise Exception("value[1] is not a FieldValue:" + repr(value[1]))

        self.value = value

    def is_on_curve(self):
        if self == 0:
            return True

        x, y = self.value
        return y*y == x*x*x + self.e.a*x + self.e.b

    def __add__(self, o):
        assert self.e == o.e

        if self == 0:
            return o
        if o == 0:
            return self
        if self == -o:
            return self.e.ZERO

        a = self.value
        b = o.value
        if a == b:
            # Point doubling.
            dy = 3*a[0]*a[0] + self.e.a
            dx = 2*a[1]
        else:
            # Distinct points.
            dx = b[0] - a[0]
            dy = b[1] - a[1]
        slope = dy / dx
        xr = slope*slope - a[0] - b[0]
        yr = slope*(a[0] - xr) - a[1]
        return EllipticCurveValue(self.e, (xr, yr))

    def __sub__(self, o):
        assert self.e == o.e
        return self + -o

    def __mul__(self, n):
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
        return self.e.value((self.value[0], -self.value[1]))

    def __eq__(self, o):
        if isinstance(o, int):
            if o == 0:
                return self.value[0].value == 0 and self.value[1].value == 0
            else:
                raise Exception("cannot compare with non-zero integer")

        assert self.e == o.e
        return self.value == o.value

    def __repr__(self):
        return "(" + repr(self.value[0]) + "," + repr(self.value[1]) + ")"

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
        print("x =", hex(q.value[0].value)[2:].upper())
        print("y =", hex(q.value[1].value)[2:].upper())
        print(q.is_on_curve())
        print()
        q += e.G

    print(e.G*89329329329382389349238432984379239432)
