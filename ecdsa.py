
# Elliptic curve DSA.
# https://en.wikipedia.org/wiki/Elliptic_Curve_Digital_Signature_Algorithm
# https://cryptobook.nakov.com/digital-signatures/ecdsa-sign-verify-messages

import math
import random
import ecc
import ethsha3
from field import Field

V_VALUE_EVEN = 27
V_VALUE_ODD = 28

def sign_message(ec, pr, e):
    if isinstance(e, bytes) or isinstance(e, bytearray):
        e = int.from_bytes(ethsha3.ethsha3(e), "big")

    z = e
    z_bits = math.ceil(math.log2(z))
    n_bits = math.ceil(math.log2(ec.n))
    assert z_bits <= n_bits

    while True:
        k = random.randrange(1, ec.n)
        p1 = ec.G*k
        r = f.value(p1.x)
        if r == 0:
            continue
        s = (z + r*pr)/k
        if s == 0:
            continue

        v = V_VALUE_EVEN if p1.y.value % 2 == 0 else V_VALUE_ODD

        return v, r, s

def verify_signature(ec, pu, e, v, r, s):
    if isinstance(e, bytes) or isinstance(e, bytearray):
        e = int.from_bytes(ethsha3.ethsha3(e), "big")

    z = e
    z_bits = math.ceil(math.log2(z))
    n_bits = math.ceil(math.log2(ec.n))
    assert z_bits <= n_bits

    u1 = z/s
    u2 = r/s
    p2 = ec.G*u1 + pu*u2

    return r == f.value(p2.x)

def recover_public_key(ec, e, v, r, s):
    if isinstance(e, bytes) or isinstance(e, bytearray):
        e = int.from_bytes(ethsha3.ethsha3(e), "big")

    z = e
    z_bits = math.ceil(math.log2(z))
    n_bits = math.ceil(math.log2(ec.n))
    assert z_bits <= n_bits

    x1 = ec.f.value(r)
    y1 = ec.find_y_for_x(x1, v == V_VALUE_EVEN)
    R = ec.value(x1, y1)
    u1 = -(z/r)
    u2 = s/r
    return ec.G*u1 + R*u2

if __name__ == "__main__":
    ec = ecc.EllipticCurve.secp256k1()
    f = Field(ec.n)

    pr, pu = ec.generate_key_pair()

    message = b"Hello!"

    v, r, s = sign_message(ec, pr, message)
    print(v, r, s)

    print(verify_signature(ec, pu, message, v, r, s))

    recovered_pu = recover_public_key(ec, message, v, r, s)
    print(recovered_pu == pu)

