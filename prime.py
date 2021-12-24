
from random import randrange

# Miller-Rabin primality test
def is_prime_miller(n):
    if n == 2: return True
    if n < 2 or n % 2 == 0: return False

    # Find r and d such that n = 2^r * d,
    # with d being odd.
    d = n - 1
    r = 0
    while d % 2 == 0:
        r += 1
        d = d//2

    # Taken from wikipedia:
    # https://en.wikipedia.org/wiki/Miller%E2%80%93Rabin_primality_test
    bases_list = [
            (2047, [2]),
            (1373653, [2, 3]),
            (9080191, [31, 73]),
            (25326001, [2, 3, 5]),
            (3215031751, [2, 3, 5, 7]),
            (4759123141, [2, 7, 61]),
            (1122004669633, [2, 13, 23, 1662803]),
            (2152302898747, [2, 3, 5, 7, 11]),
            (3474749660383, [2, 3, 5, 7, 11, 13]),
            (341550071728321, [2, 3, 5, 7, 11, 13, 17]),
            (3825123056546413051, [2, 3, 5, 7, 11, 13, 17, 19, 23]),
            (18446744073709551616, [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]),
            (318665857834031151167461, [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41])
        ]

    # Find which bases to use
    bases = None
    for b in bases_list:
        if n < b[0]:
            bases = b[1]
            break

    if bases == None:
        print("Number too large for deterministic Miller-Rabin primality test.")
        return None

    for a in bases:
        flag = 0
        x = pow(a, d, n)

        if x == 1 or x == n - 1:
            continue

        for _ in range(r-1):
            x = pow(x, 2, n)
            if x == n - 1:
                flag = 1
                break

        if flag:
            continue

        return False

    return True

# Make a random prime with this many digits.
def random_prime(num_digits):
    begin = 10**(num_digits - 1)
    end = 10**num_digits

    while True:
        value = randrange(begin, end)
        if is_prime_miller(value):
            return value

