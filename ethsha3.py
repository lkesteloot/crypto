
# Ethereum-flavor sha3.

# "pysha3" module:
from sha3 import keccak_256

# Number of bytes in the result of ethsha3().
ETHSHA3_LENGTH = 32

# A hash result with all zero bytes. Used to indicate "no hash".
ZERO_HASH = b"\x00"*ETHSHA3_LENGTH

# Return the length-32 bytes object for the hash of the bytes parameter.
def hash(b):
    h = keccak_256()
    h.update(b)
    return h.digest()

EMPTY_STRING_HASH = hash(b"")
