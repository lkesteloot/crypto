
# Hex-prefix encoding. See Appending C of the Ethereum Yellow Paper.

import nybbles

# Flags in the first byte.
_ODD_FLAG = 0x10
_T_FLAG = 0x20

# Encode a sequence of nybbles from the byte array "b", starting at
# nybble index "begin" (inclusive) until "end" (exclusive). Nybbles
# are considered big-endian (high nybble first). The "t" parameter
# is encoded in the first nybble (see spec).
def bytes_to_hp(b, begin, end, t):
    nybble_count = end - begin
    out = bytearray(nybble_count // 2 + 1)
    if t != 0:
        out[0] |= _T_FLAG

    if nybble_count % 2 != 0:
        out[0] |= _ODD_FLAG
        o = 1
    else:
        o = 2

    for i in range(begin, end):
        v = nybbles.get_nybble(b, i)
        out[o // 2] |= v << 4 if o % 2 == 0 else v
        o += 1

    return bytes(out)

# Converts an array of nybbles (as a bytes) to a hex prefix.
def nybbles_to_hp(ny, t):
    assert isinstance(ny, bytes)

    t_flag = _T_FLAG if t != 0 else 0

    if len(ny) % 2 == 0:
        ny = bytes([t_flag >> 4, 0]) + ny
    else:
        ny = bytes([(t_flag | _ODD_FLAG) >> 4]) + ny

    return nybbles.nybbles_to_bytes(ny)

# Converts a hex prefix to an array of nybbles (as a bytes).
def hp_to_nybbles(hp):
    ny = nybbles.bytes_to_nybbles(hp)

    if _is_odd_nybble_count(hp):
        ny = ny[1:]
    else:
        ny = ny[2:]

    return ny

# Whether the t that was passed in to this hp was non-zero.
def get_flag(hp):
    assert isinstance(hp, bytes)
    return (hp[0] & _T_FLAG) != 0

# Return a (count, hp_left, b_left) tuple, where "count" is the number of
# prefix nybbles hp and b (starting at b_begin) have in
# common, "hp_left" is the number of nybbles left in hp, and
# "b_left" is the number of nybbles left in b.
def common_prefix(hp, b, b_begin):
    assert isinstance(hp, bytes)
    assert isinstance(b, bytes)

    hp_count = _get_nybble_count(hp)
    b_count = len(b)*2 - b_begin
    count = min(hp_count, b_count)

    for i in range(count):
        hp_nybble = _get_hp_nybble(hp, i)
        b_nybble = nybbles.get_nybble(b, b_begin + i)

        if hp_nybble != b_nybble:
            return i, hp_count - i, b_count - i

    return count, hp_count - count, b_count - count

# The number of nybbles in the hp.
def _get_nybble_count(hp):
    return (len(hp) - 1)*2 + (1 if _is_odd_nybble_count(hp) else 0)

# Whether the hp has an odd number of nybbles.
def _is_odd_nybble_count(hp):
    return (hp[0] & _ODD_FLAG) != 0

# Get the ith nybble of hp b.
def _get_hp_nybble(hp, i):
    return nybbles.get_nybble(hp, i + (1 if _is_odd_nybble_count(hp) else 2))

if __name__ == "__main__":
    b = bytes([0x12, 0x34, 0x56, 0x78])

    # Degenerate cases.
    assert bytes_to_hp(b, 4, 4, 0) == b"\x00"
    assert bytes_to_hp(b, 4, 4, 1) == b"\x20"

    # Easy cases.
    assert bytes_to_hp(b, 0, 8, 0) == b"\x00" + b
    assert bytes_to_hp(b, 0, 8, 1) == b"\x20" + b
    assert bytes_to_hp(b, 0, 6, 0) == b"\x00" + b[:3]
    assert bytes_to_hp(b, 0, 6, 1) == b"\x20" + b[:3]
    assert bytes_to_hp(b, 2, 8, 0) == b"\x00" + b[1:]
    assert bytes_to_hp(b, 2, 8, 1) == b"\x20" + b[1:]
    assert bytes_to_hp(b, 2, 6, 0) == b"\x00" + b[1:3]
    assert bytes_to_hp(b, 2, 6, 1) == b"\x20" + b[1:3]

    # Harder cases.
    assert bytes_to_hp(b, 1, 8, 0) == b"\x12\x34\x56\x78"
    assert bytes_to_hp(b, 1, 8, 1) == b"\x32\x34\x56\x78"
    assert bytes_to_hp(b, 0, 7, 0) == b"\x11\x23\x45\x67"
    assert bytes_to_hp(b, 0, 7, 1) == b"\x31\x23\x45\x67"
    assert bytes_to_hp(b, 1, 7, 0) == b"\x00\x23\x45\x67"
    assert bytes_to_hp(b, 1, 7, 1) == b"\x20\x23\x45\x67"
    assert bytes_to_hp(b, 3, 6, 0) == b"\x14\x56"
    assert bytes_to_hp(b, 3, 7, 0) == b"\x00\x45\x67"
    assert bytes_to_hp(b, 4, 7, 0) == b"\x15\x67"

    # Flag.
    assert not get_flag(bytes_to_hp(b, 0, 8, 0))
    assert get_flag(bytes_to_hp(b, 0, 8, 1))

    # Common prefix.
    assert common_prefix(bytes_to_hp(b, 0, 8, 0), b"\x12\x34\x56\x78", 0) == (8, 0, 0)
    assert common_prefix(bytes_to_hp(b, 0, 4, 0), b"\x12\x34\x56\x78", 0) == (4, 0, 4)
    assert common_prefix(bytes_to_hp(b, 4, 8, 0), b"\x12\x34\x56\x78", 0) == (0, 4, 8)
    assert common_prefix(bytes_to_hp(b, 4, 8, 0), b"\x12\x34\x56\x78", 4) == (4, 0, 0)
    assert common_prefix(bytes_to_hp(b, 4, 8, 0), b"\x12\x34\x56\x79", 4) == (3, 1, 1)
    assert common_prefix(bytes_to_hp(b, 0, 8, 0), b"\x12", 0) == (2, 6, 0)

    # Nybbles to hex prefix.
    assert nybbles_to_hp(b"\x01\x02\x03\x04", 0) == b"\x00\x12\x34"
    assert nybbles_to_hp(b"\x01\x02\x03\x04", 1) == b"\x20\x12\x34"
    assert nybbles_to_hp(b"\x01\x02\x03", 0) == b"\x11\x23"
    assert nybbles_to_hp(b"\x01\x02\x03", 1) == b"\x31\x23"

    # Hex prefix to nybbles.
    assert hp_to_nybbles(b"\x00\x12\x34") == b"\x01\x02\x03\x04"
    assert hp_to_nybbles(b"\x20\x12\x34") == b"\x01\x02\x03\x04"
    assert hp_to_nybbles(b"\x11\x23") == b"\x01\x02\x03"
    assert hp_to_nybbles(b"\x31\x23") == b"\x01\x02\x03"

    print("All good.")

