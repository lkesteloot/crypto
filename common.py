
# Commonly-used routines.

def gcd(a, b):
    while b != 0:
        t = b
        b = a % b
        a = t
    return a

def lcm(a, b):
    return a*b//gcd(a, b)

def xgcd(a, b):
    """return (g, x, y) such that a*x + b*y = g = gcd(a, b)"""
    x0, x1, y0, y1 = 0, 1, 1, 0
    while a != 0:
        (q, a), b = divmod(b, a), a
        y0, y1 = y1, y0 - q * y1
        x0, x1 = x1, x0 - q * x1
    return b, x0, y0

def prime_factors(a):
    while a > 1:
        for i in range(2, a + 1):
            if a % i == 0:
                yield i
                a //= i

def are_relatively_prime(a, b):
    return gcd(a, b) == 1

# Find e such that ed % n = 1
def find_inverse(d, n):
    _, e, _ = xgcd(d, n)
    if e < 0:
        e += n
    return e
