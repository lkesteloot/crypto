
# Functions for dealing with nybbles.

# Get the ith nybble of byte array b.
def get_nybble(b, i):
    v = b[i >> 1]
    if (i & 1) == 0:
        v >>= 4
    return v & 0x0F

# Converts bytes to a byte array of nybbles. "begin" and "end" are
# nybble indexes, inclusive and exclusive respectively.
def bytes_to_nybbles(b, begin=0, end=None):
    if end is None:
        end = len(b)*2

    return bytes(get_nybble(b, i) for i in range(begin, end))

# Converts nybbles to bytes. "begin" and "end" are nybble indexes,
# inclusive and exclusive respectively. If this is an odd number
# of nybbles, the last byte will have zero for its least significant
# nybble.
def nybbles_to_bytes(ny, begin=0, end=None):
    if end is None:
        end = len(ny)

    byte_count = (end - begin + 1)//2
    return bytes(
            (ny[begin + i*2] << 4) | (ny[begin + i*2 + 1] if begin + i*2 + 1 < end else 0)
            for i in range(byte_count))

# Takes two byte arrays (in principle nybble arrays, but values aren't limited
# to nybbles). Returns the tuple (common, a_left, b_left), where "common" is a
# byte array of the common prefix, and "a_left" and "b_left" are the byte
# arrays of what's left after the common prefix. Any or all of the three may
# be empty.
def common_prefix(a, b):
    m = min(len(a), len(b))

    i = 0
    while i < m and a[i] == b[i]:
        i += 1

    return a[:i], a[i:], b[i:]

if __name__ == "__main__":
    # Bytes to nybbles.
    assert bytes_to_nybbles(b"\x12\x34\x56") == b"\x01\x02\x03\x04\x05\x06"
    assert bytes_to_nybbles(b"\x12\x34\x56", 1) == b"\x02\x03\x04\x05\x06"
    assert bytes_to_nybbles(b"\x12\x34\x56", 1, 3) == b"\x02\x03"

    # Nybbles to bytes.
    assert nybbles_to_bytes(b"\x01\x02\x03\x04\x05\x06") == b"\x12\x34\x56"
    assert nybbles_to_bytes(b"\x01\x02\x03\x04\x05\x06", 1) == b"\x23\x45\x60"
    assert nybbles_to_bytes(b"\x01\x02\x03\x04\x05\x06", 1, 3) == b"\x23"
    assert nybbles_to_bytes(b"\x01\x02\x03\x04\x05\x06", 1, 4) == b"\x23\x40"
    assert nybbles_to_bytes(b"\x01\x02\x03\x04\x05\x06", 1, 5) == b"\x23\x45"

    # Common prefix.
    assert common_prefix(b"\x01\x02\x03", b"\x01\x02\x04") == (b"\x01\x02", b"\x03", b"\x04")
    assert common_prefix(b"\x01\x02", b"\x01\x02\x04") == (b"\x01\x02", b"", b"\x04")
    assert common_prefix(b"\x01\x02\x03", b"\x01\x02") == (b"\x01\x02", b"\x03", b"")
    assert common_prefix(b"\x01\x02", b"\x01\x02") == (b"\x01\x02", b"", b"")
    assert common_prefix(b"\x01\x02\x03", b"") == (b"", b"\x01\x02\x03", b"")

    print("All good.")

