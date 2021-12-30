
# Implementation of Merkle Patricia Trie.
# https://eth.wiki/en/fundamentals/patricia-tree

from rlp import encode_rlp, decode_rlp
from ethsha3 import ethsha3
from testing import random_bytes

NO_HASH = b""

# Get the nybble_index for the b bytes object, where 0 means the
# most significant nybble of the first byte, 1 is the least significant,
# etc.
def _get_nybble(b, nybble_index):
    byte = b[nybble_index//2]
    if nybble_index % 2 == 0:
        byte >>= 4
    nybble = byte & 0x0F
    return nybble

# Implementation note: Each node is an RLP-encoded list of 17 elements. The first
# 16 are the roots of the sub-trees for the nybble in the trie, and the 17th element,
# if any, is the value for that key. Missing values are represented by not having
# a 17th element. Missing children (in the first 16 entries) are represented by
# an empty byte array.
class MerklePatriciaTrie:
    # key_value_store is a hash map with set(k,v) and get(k) methods.
    # Keys are fixed-length (256-bit) bytes objects.
    # Values are arbitrary bytes objects. The get() method throws on unknown key.
    # The root, if specified, is a 256-bit bytes object.
    def __init__(self, key_value_store, root=NO_HASH):
        self.key_value_store = key_value_store
        self.root = root

    # key and value are arbitrary bytes objects. Does not modify the current
    # object -- returns a new MerklePatriciaTrie object.
    def set(self, key, value):
        assert isinstance(key, bytes)
        assert isinstance(value, bytes)
        new_root = self._set(key, self.root, 0, value)
        return MerklePatriciaTrie(self.key_value_store, new_root)

    # Returns the value for the key (which are both bytes objects), or None
    # if this object does not contain the key.
    def get(self, key):
        assert isinstance(key, bytes)
        return self._get(key, self.root, 0)

    # Recurse to set the value for the root. Assumes that "nybble_index" nybbles
    # have already been processed. The root is either NO_HASH or a bytes hash.
    def _set(self, key, root, nybble_index, value):
        if root == NO_HASH:
            v = [NO_HASH]*16
        else:
            v = decode_rlp(self.key_value_store.get(root))[0]

        if nybble_index == len(key)*2:
            # Done recursing, set value.
            if len(v) == 16:
                v.append(value)
            else:
                v[-1] = value
            new_root = root
        else:
            nybble = _get_nybble(key, nybble_index)
            old_root = v[nybble]
            new_root = self._set(key, old_root, nybble_index + 1, value)
            v[nybble] = new_root

        rlp_v = encode_rlp(v)
        rlp_root = ethsha3(rlp_v)
        self.key_value_store.set(rlp_root, rlp_v)

        return rlp_root

    # Recurse to get the value for the root. Assumes that "nybble_index" nybbles
    # have already been processed. The root is either NO_HASH or a bytes hash.
    def _get(self, key, root, nybble_index):
        if root == NO_HASH:
            # Value not in data structure.
            return None

        v = decode_rlp(self.key_value_store.get(root))[0]

        if nybble_index == len(key)*2:
            # Done recursing, find value.
            return v[-1]
        else:
            nybble = _get_nybble(key, nybble_index)
            new_root = v[nybble]
            return self._get(key, new_root, nybble_index + 1)

# Straightforward hash table for bytes keys and values.
class HashTable:
    def __init__(self):
        self.m = {}
        self.default_value = object()

    def set(self, k, v):
        # Make sure these are immutable.
        assert isinstance(k, bytes)
        assert isinstance(v, bytes)
        self.m[k] = v

    def get(self, k):
        assert isinstance(k, bytes)
        v = self.m.get(k, self.default_value)
        if v is self.default_value:
            raise Exception("the hash map does not contain the key 0x" + k.hex())
        else:
            return v

if __name__ == "__main__":
    hash_table = HashTable()
    m1 = MerklePatriciaTrie(hash_table)
    k = b"abc"
    v1 = b"xyz"
    m2 = m1.set(k, v1)
    assert m1.get(k) == None
    assert m2.get(k) == v1

    v2 = b"ijk"
    m3 = m2.set(k, v2)
    assert m1.get(k) == None
    assert m2.get(k) == v1
    assert m3.get(k) == v2

    # Random insertions.
    m = MerklePatriciaTrie(hash_table)
    q = {}
    for i in range(1000):
        k = random_bytes(0, 64)
        v = random_bytes(0, 400)
        q[k] = v
        m = m.set(k, v)
    for k, v in q.items():
        assert m.get(k) == v

    print("All good.")

