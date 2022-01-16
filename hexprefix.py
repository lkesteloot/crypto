
# Hex-prefix encoding. See Appending C of the Ethereum Yellow Paper.

# Encode a sequence of nybbles from the byte array "b", starting at
# nybble index "begin" (inclusive) until "end" (exclusive). Nybbles
# are considered big-endian (high nybble first). The "t" parameter
# is encoded in the first nybble (see spec).
def encode(b, begin, end, t):
    nybble_count = end - begin
    out = bytearray(nybble_count // 2 + 1)
    if t != 0:
        out[0] |= 0x20

    if nybble_count % 2 != 0:
        out[0] |= 0x10
        o = 1
    else:
        o = 2

    for i in range(begin, end):
        v = b[i // 2]
        if i % 2 == 0:
            v >>= 4
        v &= 0x0F

        out[o // 2] |= v << 4 if o % 2 == 0 else v

        o += 1

    return bytes(out)

if __name__ == "__main__":
    b = bytes([0x12, 0x34, 0x56, 0x78])

    # Degenerate cases.
    assert encode(b, 4, 4, 0) == b"\x00"
    assert encode(b, 4, 4, 1) == b"\x20"

    # Easy cases.
    assert encode(b, 0, 8, 0) == b"\x00" + b
    assert encode(b, 0, 8, 1) == b"\x20" + b
    assert encode(b, 0, 6, 0) == b"\x00" + b[:3]
    assert encode(b, 0, 6, 1) == b"\x20" + b[:3]
    assert encode(b, 2, 8, 0) == b"\x00" + b[1:]
    assert encode(b, 2, 8, 1) == b"\x20" + b[1:]
    assert encode(b, 2, 6, 0) == b"\x00" + b[1:3]
    assert encode(b, 2, 6, 1) == b"\x20" + b[1:3]

    # Harder cases.
    assert encode(b, 1, 8, 0) == b"\x12\x34\x56\x78"
    assert encode(b, 1, 8, 1) == b"\x32\x34\x56\x78"
    assert encode(b, 0, 7, 0) == b"\x11\x23\x45\x67"
    assert encode(b, 0, 7, 1) == b"\x31\x23\x45\x67"
    assert encode(b, 1, 7, 0) == b"\x00\x23\x45\x67"
    assert encode(b, 1, 7, 1) == b"\x20\x23\x45\x67"
    assert encode(b, 3, 6, 0) == b"\x14\x56"
    assert encode(b, 3, 7, 0) == b"\x00\x45\x67"
    assert encode(b, 4, 7, 0) == b"\x15\x67"

