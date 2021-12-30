
# Ethereum-flavor sha3.

# "pysha3" module:
from sha3 import keccak_256

# Return the bytes object for the hash of the bytes parameter.
def ethsha3(b):
    h = keccak_256()
    h.update(b)
    return h.digest()

