
# Ethereum Recursive Length Prefix encoding and decoding.
# https://eth.wiki/fundamentals/rlp

# Convert an integer to big-endian with initial zero bytes stripped off.
def encode_int(n):
    return n.to_bytes(32, "big").lstrip(b"\x00")

# Convert a big-endian bytearray version of an int to the int.
def decode_int(b):
    # This properly handles an empty array as "0".
    return int.from_bytes(b, "big")

# Data is hierarchy of bytearrays, bytes, lists, and tuples. Convert your
# non-bytearray data to bytearrays or bytes first. Returns an encoded bytearray.
def encode(data):
    if isinstance(data, bytearray) or isinstance(data, bytes):
        if len(data) == 1 and data[0] < 0x80:
            # Byte is its own encoding. First byte is [0x00, 0x7F].
            return bytes(data)
        if len(data) <= 55:
            # Simple length plus data. First byte is [0x80, 0xB7].
            return bytes([0x80 + len(data)]) + data
        # Length of length, then length, then data. First byte is [0xB8, 0xBF].
        length = encode_int(len(data))
        return bytes([0xB7 + len(length)]) + length + data
    elif isinstance(data, list) or isinstance(data, tuple):
        contents = b"".join(encode(x) for x in data)
        if len(contents) <= 55:
            # Simple length plus data. First byte is [0xC0, 0xF7].
            return bytes([0xC0 + len(contents)]) + contents
        # Length of length, then length, then data. First byte is [0xF8, 0xFF].
        length = encode_int(len(contents))
        return bytes([0xF7 + len(length)]) + length + contents
    else:
        raise Exception("can only RLP-encode bytearray or list")

# Decodes a bytearray that was encoded by RLP. Returns a hierarchy of
# bytearrays and lists, and the number of bytes consumed. Starts at byte "start".
def _decode(b, start=0):
    # Byte array.
    if b[start] <= 0x7F:
        return b[start:start + 1], 1
    if b[start] <= 0xB7:
        length = b[start] - 0x80
        return b[start + 1:start + length + 1], length + 1
    if b[start] <= 0xBF:
        length_of_length = b[start] - 0xB7
        length = decode_int(b[start + 1:start + length_of_length + 1])
        size = length_of_length + 1 + length
        return b[start + length_of_length + 1:start + size], size

    # List.
    if b[start] <= 0xF7:
        length = b[start] - 0xC0
        index = 1
    else:
        length_of_length = b[start] - 0xF7
        length = decode_int(b[start + 1:start + length_of_length + 1])
        index = length_of_length + 1

    items = []
    while length > 0:
        item, size = _decode(b, start + index)
        index += size
        length -= size
        items.append(item)
    return items, index

# Decodes a bytearray that was encoded by RLP. Returns a hierarchy of
# bytearrays and lists.
def decode(b):
    data, size = _decode(b)
    assert size == len(b)
    return data

# Decode a sequence of RLP data structures, yielding each one.
def decode_multiple(b):
    index = 0

    while index < len(b):
        data, size = _decode(b, index)
        yield data
        index += size

def dump_data(d, indent=""):
    if isinstance(d, list) or isinstance(d, tuple):
        print("%sList (%d):" % (indent, len(d)))
        for i in range(len(d)):
            dump_data(d[i], indent + "  ")
    elif isinstance(d, bytes) or isinstance(d, bytearrays):
        h = d.hex()
        if len(h) > 64:
            h = h[:64] + "..."
        print("%sBinary (%d bytes, 0x%s)" % (indent, len(d), h))
    else:
        print(indent + "Unknown type: " + str(type(d)))

def _test(a):
    # print(a)
    b = encode(a)
    print(a, "=>", b)
    c, size = _decode(b)
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

