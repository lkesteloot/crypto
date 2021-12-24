
# Messing around with RSA.

import random
from prime import is_prime_miller
from common import are_relatively_prime, find_inverse, lcm

# Two primes.
p = 37
q = 41
n = p*q
k = lcm(p - 1, q - 1) # Carmichael function

# 1 < d < n - 1, and d and k are relatively prime (so we can find an inverse).
while True:
    d = random.randrange(2, n - 1)
    if are_relatively_prime(d, k):
        break

# e * d = 1 (mod k)
e = find_inverse(d, k)

print(p, q, n, d, e, k)

m = random.randrange(1, n)
em = m**e % n
dm = em**d % n

print(m, em, dm, m == dm)


