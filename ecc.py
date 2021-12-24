
from field import Field
from prime import random_prime

p = random_prime(20)
print("p", p)

f = Field(p)

print(f.add(7, 10))
print(f.subtract(7, 10))
print(f.subtract(10, 7))
print(f.multiply(7, 10))
print(f.divide(7, 10))
print(f.multiply(f.divide(7, 10), 10))

for i in range(100):
    a = f.random()
    b = f.random_not_zero()
    c = f.multiply(f.divide(a, b), b)
    if a != c:
        print(a, b, c)

class EllipticCurve:
    ZERO = (0, 0)

    def __init__(self, f, a, b, G):
        self.f = f
        self.a = a
        self.b = b
        self.G = G

    def is_on_curve(self, a):
        if self.is_zero(a):
            return True

        x, y = a
        y_squared = self.f.multiply(y, y)
        x_cubed = self.f.multiply(self.f.multiply(x, x), x)
        ax = self.f.multiply(self.a, x)
        right = self.f.add(self.f.add(x_cubed, ax), self.b)
        return y_squared == right

    def is_zero(self, a):
        return a == self.ZERO

    def negate(self, a):
        return (a[0], self.f.negate(a[1]))

    def add(self, a, b):
        if self.is_zero(a):
            return b
        if self.is_zero(b):
            return a
        if a == self.negate(b):
            return self.ZERO
        if a == b:
            # Point doubling.
            dy = self.f.add(self.f.multiply(self.f.multiply(3, a[0]), a[0]), self.a)
            dx = self.f.multiply(2, a[1])
        else:
            # Distinct points.
            dx = self.f.subtract(b[0], a[0])
            dy = self.f.subtract(b[1], a[1])
        slope = self.f.divide(dy, dx)
        xr = self.f.subtract(self.f.subtract(self.f.multiply(slope, slope), a[0]), b[0])
        yr = self.f.subtract(self.f.multiply(slope, self.f.subtract(a[0], xr)), a[1])
        return (xr, yr)

    def multiply(self, a, n):
        s = self.ZERO

        while n != 0:
            if (n & 1) != 0:
                s = self.add(s, a)

            n >>= 1
            a = self.add(a, a)

        return s


# https://en.bitcoin.it/wiki/Secp256k1
p = 2**256 - 2**32 - 2**9 - 2**8 - 2**7 - 2**6 - 2**4 - 1
f = Field(p)
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
e = EllipticCurve(f, 0, 7, (Gx, Gy))

print(e.G)
g2 = e.add(e.G, e.G)
print(g2, e.is_on_curve(g2))
g3_1 = e.add(g2, e.G)
g3_2 = e.add(e.G, g2)
g4_1 = e.add(g3_1, e.G)
g4_2 = e.add(e.G, g3_1)
g4_3 = e.add(g2, g2)
print(g4_1 == g4_2)
print(g4_1 == g4_3)
negG = e.negate(e.G)

print("---")
print(e.ZERO == e.multiply(e.G, 0))
print(e.G == e.multiply(e.G, 1))
print(g2 == e.multiply(e.G, 2))
print(g3_1 == e.multiply(e.G, 3))

q1 = e.multiply(e.G, 4)
q2 = q1
for i in range(4):
    q2 = e.add(q2, negG)
print(q2)

print("---")

q = e.ZERO
for k in range(5):
    print("k =", k)
    print("x =", hex(q[0])[2:].upper())
    print("y =", hex(q[1])[2:].upper())
    print(e.is_on_curve(q))
    print()
    q = e.add(q, e.G)

e.multiply(e.G, 89329329329382389349238432984379239432)
