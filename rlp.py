
# Ethereum Recursive Length Prefix encoding and decoding.
# https://eth.wiki/fundamentals/rlp

# Convert an integer to big-endian with initial zero bytes stripped off.
def _int_to_bytearray(n):
    n = n.to_bytes(8, "big")
    return n[:-1].lstrip(b"\x00") + n[-1:]

# Convert a big-endian bytearray version of an int to the int.
def _bytearray_to_int(b):
    return int.from_bytes(b, "big")


# Data is hierarchy of bytearrays, bytes, lists, and tuples. Convert your
# non-bytearray data to bytearrays or bytes first. Returns an encoded bytearray.
def encode_rlp(data):
    if isinstance(data, bytearray) or isinstance(data, bytes):
        if len(data) == 1 and data[0] < 0x80:
            # Byte is its own encoding. First byte is [0x00, 0x7F].
            return bytes(data)
        if len(data) <= 55:
            # Simple length plus data. First byte is [0x80, 0xB7].
            return bytes([0x80 + len(data)]) + data
        # Length of length, then length, then data. First byte is [0xB8, 0xBF].
        length = _int_to_bytearray(len(data))
        return bytes([0xB7 + len(length)]) + length + data
    elif isinstance(data, list) or isinstance(data, tuple):
        contents = b"".join(encode_rlp(x) for x in data)
        if len(contents) <= 55:
            # Simple length plus data. First byte is [0xC0, 0xF7].
            return bytes([0xC0 + len(contents)]) + contents
        # Length of length, then length, then data. First byte is [0xF8, 0xFF].
        length = _int_to_bytearray(len(contents))
        return bytes([0xF7 + len(length)]) + length + contents
    else:
        raise Exception("can only RLP-encode bytearray or list")


# Decodes a bytearray that was encoded by RLP. Returns a hierarchy of
# bytearrays and lists, and the number of bytes consumed.
def decode_rlp(b):
    # Byte array.
    if b[0] <= 0x7F:
        return b[:1], 1
    if b[0] <= 0xB7:
        length = b[0] - 0x80
        return b[1:length + 1], length + 1
    if b[0] <= 0xBF:
        length_of_length = b[0] - 0xB7
        length = _bytearray_to_int(b[1:length_of_length + 1])
        size = length_of_length + 1 + length
        return b[length_of_length + 1:size], size

    # List.
    if b[0] <= 0xF7:
        length = b[0] - 0xC0
        index = 1
    else:
        length_of_length = b[0] - 0xF7
        length = _bytearray_to_int(b[1:length_of_length + 1])
        index = length_of_length + 1

    items = []
    while length > 0:
        item, size = decode_rlp(b[index:])
        index += size
        length -= size
        items.append(item)
    return items, index


def _test(a):
    # print(a)
    b = encode_rlp(a)
    print(a, "=>", b)
    c, size = decode_rlp(b)
    # print(c, size)

    print(c == a, size == len(b))

if __name__ == "__main__":
    # https://eth.wiki/fundamentals/rlp#examples
    _test(b"dog")
    _test([b"cat", b"dog"])
    _test(b"")  # also null
    _test(b"\x00")
    _test(b"")  # "the integer 0" ?
    _test(b"\x0F")
    _test(b"\x04\x00")
    _test([ [], [[]], [ [], [[]] ] ])
    _test(b"Lorem ipsum dolor sit amet, consectetur adipisicing elit")

