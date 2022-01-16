
# Implementation of Merkle Patricia Trie.
# https://eth.wiki/en/fundamentals/patricia-tree

import rlp
from ethsha3 import ethsha3, ETHSHA3_LENGTH
from testing import random_bytes

NO_HASH = b""
NO_VALUE = b""

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
# if not NO_VALUE, is the value for that key. Missing children (in the first 16 entries)
# are represented by an empty byte array.
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

    # Returns the value for the key (which are both bytes objects), or NO_VALUE
    # if this object does not contain the key.
    def get(self, key):
        assert isinstance(key, bytes)
        return self._get(key, self.root, 0)

    # Recurse to set the value for the root. Assumes that "nybble_index" nybbles
    # have already been processed. The root is either NO_HASH or a bytes hash.
    def _set(self, key, root, nybble_index, value):
        if root == NO_HASH:
            v = [NO_HASH]*16 + [NO_VALUE]
        else:
            v = rlp.decode(self._get_from_store(root))
        assert len(v) == 17

        if nybble_index == len(key)*2:
            # Done recursing, set value.
            v[-1] = value
            new_root = root
        else:
            nybble = _get_nybble(key, nybble_index)
            old_root = v[nybble]
            new_root = self._set(key, old_root, nybble_index + 1, value)
            v[nybble] = new_root

        rlp_v = rlp.encode(v)
        rlp_root = self._put_in_store(rlp_v)

        return rlp_root

    # Recurse to get the value for the root. Assumes that "nybble_index" nybbles
    # have already been processed. The root is either NO_HASH or a bytes hash.
    def _get(self, key, root, nybble_index):
        if root == NO_HASH:
            # Value not in data structure.
            return NO_VALUE

        v = rlp.decode(self._get_from_store(root))
        assert len(v) == 17

        if nybble_index == len(key)*2:
            # Done recursing, find value.
            return v[-1]
        else:
            nybble = _get_nybble(key, nybble_index)
            new_root = v[nybble]
            return self._get(key, new_root, nybble_index + 1)

    def _get_from_store(self, k):
        if len(k) < ETHSHA3_LENGTH:
            return k
        else:
            return self.key_value_store.get(k)

    def _put_in_store(self, k):
        if len(k) < ETHSHA3_LENGTH:
            return k
        else:
            h = ethsha3(k)
            self.key_value_store.set(h, k)
            return h

    def items(self):
        items = []
        self._fill_items(items, self.root, b"", True)
        return items

    def _fill_items(self, items, r, path, is_byte):
        if r != NO_HASH:
            v = rlp.decode(self._get_from_store(r))
            assert len(v) == 17
            if is_byte and v[-1] != NO_VALUE:
                items.append((path, v[-1]))
            for i in range(16):
                if is_byte:
                    new_path = path + bytes([i << 4])
                else:
                    new_path = path[:-1] + bytes([path[-1] | i])

                self._fill_items(items, v[i], new_path, not is_byte)

    def __repr__(self):
        parts = []
        self._fill_repr(parts, self.root, b"", True)
        return "\n".join(parts)

    def __len__(self):
        return self._get_len(self.root)

    def _get_len(self, r):
        count = 0

        if r != NO_HASH:
            v = rlp.decode(self._get_from_store(r))
            assert len(v) == 17
            if v[-1] != NO_VALUE:
                count += 1
            for i in range(16):
                count += self._get_len(v[i])

        return count

    def _fill_repr(self, parts, r, path, is_byte):
        if r != NO_HASH:
            v = rlp.decode(self._get_from_store(r))
            if is_byte and v[-1] != NO_VALUE:
                parts.append(path.hex() + " = " + v[-1].hex())
            for i in range(16):
                if is_byte:
                    new_path = path + bytes([i << 4])
                else:
                    new_path = path[:-1] + bytes([path[-1] | i])

                self._fill_repr(parts, v[i], new_path, not is_byte)


# Straightforward hash table for bytes keys and values.
class HashTable:
    def __init__(self):
        self.m = {}
        self.default_value = object()

    def __len__(self):
        return len(self.m)

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
    assert m1.get(k) == NO_VALUE
    assert m2.get(k) == v1

    v2 = b"ijk"
    m3 = m2.set(k, v2)
    assert m1.get(k) == NO_VALUE
    assert m2.get(k) == v1
    assert m3.get(k) == v2

    # Random insertions.
    m = MerklePatriciaTrie(hash_table)
    q = {}
    for i in range(1000):
        k = random_bytes(0, 64)
        v = random_bytes(1, 400)
        q[k] = v
        m = m.set(k, v)
    for k, v in q.items():
        assert m.get(k) == v

    print("All good.")

