
# Ethereum-flavor sha3.

# "pysha3" module:
from sha3 import keccak_256

# Number of bytes in the result of ethsha3().
ETHSHA3_LENGTH = 32

# Return the bytes object for the hash of the bytes parameter.
def ethsha3(b):
    h = keccak_256()
    h.update(b)
    return h.digest()

