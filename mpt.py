
# Implementation of Merkle Patricia Trie.
# https://eth.wiki/en/fundamentals/patricia-tree

import json
import rlp
import hexprefix
import nybbles
from ethsha3 import ethsha3, ETHSHA3_LENGTH
from testing import random_bytes

NO_HASH = b""
NO_VALUE = b""
INDENT = "    "

# Get the nybble_index for the b bytes object, where 0 means the
# most significant nybble of the first byte, 1 is the least significant,
# etc.
def _get_nybble(b, nybble_index):
    byte = b[nybble_index//2]
    if nybble_index % 2 == 0:
        byte >>= 4
    nybble = byte & 0x0F
    return nybble

# Whether the hexprefix represents a leaf.
def _is_leaf(hp):
    return hexprefix.get_flag(hp)

# Whether the hexprefix represents an extension.
def _is_extension(hp):
    return not hexprefix.get_flag(hp)

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
        new_root = self._set(nybbles.bytes_to_nybbles(key), self.root, 0, value)
        return MerklePatriciaTrie(self.key_value_store, new_root)

    # Returns the value for the key (which are both bytes objects), or NO_VALUE
    # if this object does not contain the key.
    def get(self, key):
        assert isinstance(key, bytes)
        return self._get(key, self.root, 0)

    # Recurse to set the value for the root.
    #
    # key: the key in nybble format (one byte per nybble in the original key).
    # root: the root we're replacing (NO_HASH or a bytes hash).
    # nybble_index: the number of nybbles processed so far.
    # value: the value to insert at this key.
    # value_is_hash: whether the value is a value or a hash of a sub-tree.
    def _set(self, key, root, nybble_index, value, value_is_hash=False):
        if root == NO_HASH:
            if nybble_index == len(key) and value_is_hash:
                # No key left to encode, just use value.
                return value
            else:
                # Make leaf or extension.
                v = [hexprefix.nybbles_to_hp(key[nybble_index:], 0 if value_is_hash else 1),
                        value]
        else:
            v = self._get_from_store(root)
            if len(v) == 2:
                # Leaf or extension.
                old_key_ny = hexprefix.hp_to_nybbles(v[0])
                new_key_ny = key[nybble_index:]
                prefix, old_key_left, new_key_left = nybbles.common_prefix(old_key_ny, new_key_ny)
                # print("common_prefix", prefix.hex(), old_key_left.hex(), new_key_left.hex())
                if _is_leaf(v[0]) and old_key_left == b"" and new_key_left == b"":
                    # Replace value in existing leaf.
                    assert not value_is_hash # Not sure if this can happen.
                    v[-1] = value
                else:
                    # Keys don't match. We must make a branch here.
                    if _is_leaf(v[0]) or old_key_left != b"":
                        # Old key was a leaf, or a longer extension than our prefix.
                        # Create a branch for the prefix.
                        branch = [NO_HASH]*16 + [NO_VALUE]

                        if _is_leaf(v[0]) and old_key_left == b"":
                            # Put old leaf value in this branch since key matches.
                            branch[-1] = v[1]
                        else:
                            # Put old value as sub-tree.
                            old_key = key[:nybble_index] + prefix + old_key_left
                            branch[old_key_left[0]] = self._set(old_key, branch[old_key_left[0]],
                                    nybble_index + 1 + len(prefix), v[1],
                                    value_is_hash=_is_extension(v[0]))
                    else:
                        # It's an extension and the old key is already
                        # of the right length. Use existing branch.
                        branch = self._get_from_store(v[1])
                        assert len(branch) == 17

                    if new_key_left == b"":
                        # Put new value in this branch since key matches.
                        assert not value_is_hash # Not sure if this can happen.
                        branch[-1] = value
                    else:
                        # Put new value as sub-tree.
                        assert not value_is_hash # Not sure if this can happen.
                        branch[new_key_left[0]] = self._set(key, branch[new_key_left[0]],
                                nybble_index + 1 + len(prefix), value, value_is_hash=value_is_hash)
                    # print("branch", branch)

                    if prefix == b"":
                        # No prefix, use branch directly.
                        v = branch
                    else:
                        # Make extension with prefix.
                        v = [hexprefix.nybbles_to_hp(prefix, 0),
                                self._put_in_store(branch, True)]
            else:
                assert len(v) == 17

                if nybble_index == len(key):
                    # Done recursing, set value.
                    assert not value_is_hash # Not sure if this can happen.
                    v[-1] = value
                    new_root = root
                else:
                    nybble = key[nybble_index]
                    old_root = v[nybble]
                    assert not value_is_hash # Not sure if this can happen.
                    new_root = self._set(key, old_root, nybble_index + 1, value, value_is_hash=value_is_hash)
                    v[nybble] = new_root

        return self._put_in_store(v, nybble_index != 0)

    # Recurse to get the value for the root. Assumes that "nybble_index" nybbles
    # have already been processed. The root is either NO_HASH or a bytes hash.
    def _get(self, key, root, nybble_index):
        if root == NO_HASH:
            # Value not in data structure.
            return NO_VALUE

        v = self._get_from_store(root)
        if len(v) == 2:
            # Leaf or extension.
            advance, hp_left, b_left = hexprefix.common_prefix(v[0], key, nybble_index)
            if _is_leaf(v[0]):
                # Leaf.
                return v[1] if hp_left == 0 and b_left == 0 else NO_VALUE
            else:
                # Extension.
                if hp_left != 0:
                    return NO_VALUE
                return self._get(key, v[1], nybble_index + advance)
        else:
            assert len(v) == 17

            if nybble_index == len(key)*2:
                # Done recursing, find value.
                return v[-1]
            else:
                nybble = _get_nybble(key, nybble_index)
                new_root = v[nybble]
                return self._get(key, new_root, nybble_index + 1)

    # Given a value, if it's a list, return it. Otherwise assume it's a hash
    # and look up the list in the store.
    def _get_from_store(self, v):
        if isinstance(v, list) or isinstance(v, tuple):
            return v
        else:
            k = self.key_value_store.get(v)
            return rlp.decode(k)

    # Given a value, either returns it (if its RLP is short and we're
    # optimizing) or stores it by the hash of its RLP.
    def _put_in_store(self, v, optimize):
        k = rlp.encode(v)
        if optimize and len(k) < ETHSHA3_LENGTH:
            return v
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
            v = self._get_from_store(r)
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
            v = self._get_from_store(r)
            assert len(v) == 17
            if v[-1] != NO_VALUE:
                count += 1
            for i in range(16):
                count += self._get_len(v[i])

        return count

    def _fill_repr(self, parts, r, path, is_byte):
        if r != NO_HASH:
            v = self._get_from_store(r)
            if is_byte and v[-1] != NO_VALUE:
                parts.append(path.hex() + " = " + v[-1].hex())
            for i in range(16):
                if is_byte:
                    new_path = path + bytes([i << 4])
                else:
                    new_path = path[:-1] + bytes([path[-1] | i])

                self._fill_repr(parts, v[i], new_path, not is_byte)

    def dump(self):
        print("--- Dump of MPT")
        self._dump(self.root)

    def _dump(self, node, indent=""):
        print("%sRoot: %s" % (indent, self._value_to_string(node)))
        if node != NO_HASH:
            v = self._get_from_store(node)
            if len(v) == 2:
                if _is_leaf(v[0]):
                    print("%sLeaf: %s %s (%s)" % (indent, v[0].hex(), v[1].hex(), v[1]))
                else:
                    print("%sExtension: %s %s" % (indent, v[0].hex(), self._value_to_string(v[1])))
                    self._dump(v[1], indent + INDENT)
            else:
                assert len(v) == 17
                print("%sBranch: %s (%s)" % (indent, v[-1].hex(), v[-1]))
                for i in range(16):
                    if v[i] != NO_HASH:
                        print("%sChild for %x:" % (indent, i))
                        self._dump(v[i], indent + INDENT)

    def _value_to_string(self, v):
        if isinstance(v, list) or isinstance(v, tuple):
            return str(v)
        assert isinstance(v, bytes)
        return v.hex() if v != NO_HASH else "()"

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

def _unit_tests():
    hash_table = HashTable()

    v1 = b"xyz"
    v2 = b"ijk"
    v3 = b"rst"

    # Simple cases.
    m1 = MerklePatriciaTrie(hash_table)
    k = b"abc"
    m2 = m1.set(k, v1)
    assert m1.get(k) == NO_VALUE
    assert m2.get(k) == v1

    m3 = m2.set(k, v2)
    assert m1.get(k) == NO_VALUE
    assert m2.get(k) == v1
    assert m3.get(k) == v2

    # Replacing a leaf.
    k1 = b"\x12\x34"
    m2 = m1.set(k1, v1) # Makes a leaf
    m3 = m2.set(k1, v2) # Replaces value in leaf.
    assert m2.get(k1) == v1
    assert m3.get(k1) == v2

    k2 = k1 + b"\x56\x78" # k2 is longer
    m3 = m2.set(k2, v2) # Replace leaf with extension, add branch, and two more leaves.
    assert m3.get(k1) == v1
    assert m3.get(k2) == v2

    k2 = k1[:1] # k2 is shorter
    m3 = m2.set(k2, v2) # Replace leaf with shorter extension, add branch, and two more leaves.
    assert m3.get(k1) == v1
    assert m3.get(k2) == v2

    k2 = k1[:1] + b"\x9A" # k1 and k2 diverge
    m3 = m2.set(k2, v2) # Replace leaf with shorter extension, add branch, and two more leaves.
    assert m3.get(k1) == v1
    assert m3.get(k2) == v2

    # Replacing an extension.
    # print("---------------------")
    k1 = b"\x12\x34\x56"
    k2 = k1[:2] + b"\x78"
    m2 = m1.set(k1, v1) # Makes a leaf
    m3 = m2.set(k2, v2) # Make extension and two leaves.
    # m3.dump()
    assert m3.get(k1) == v1
    assert m3.get(k2) == v2

    # print("---------------------")
    k3 = k1[:1] + b"\x9A"
    m3 = m3.set(k3, v3) # Break extension.
    # m3.dump()
    assert m3.get(k1) == v1
    assert m3.get(k2) == v2
    assert m3.get(k3) == v3

    print("Unit tests good.")

def _random_tests():
    # Random insertions.
    while True:
        hash_table = HashTable()
        m = MerklePatriciaTrie(hash_table)
        q = {}
        kvs = []
        for i in range(1000):
            k = random_bytes(0, 64)
            v = random_bytes(1, 400)
            kvs.append((k, v))
            q[k] = v
            m = m.set(k, v)
        for k, v in q.items():
            if m.get(k) != v:
                print(k.hex(), m.get(k).hex(), v.hex())
                # Reconstruct tree, dumping each step.
                hash_table2 = HashTable()
                m2 = MerklePatriciaTrie(hash_table2)
                for k, v in kvs:
                    print("------------------------------------")
                    print("Inserting", k.hex(), v.hex())
                    m2 = m2.set(k, v)
                    m2.dump()
                import sys
                sys.exit(0)

            assert m.get(k) == v
        break

    print("Random tests good.")

def _my_tests():
    _unit_tests()
    _random_tests()

def _load_standard_test(filename):
    with open("../../others/eth_tests/TrieTests/" + filename) as f:
        return json.load(f)

def _to_bytes(s):
    if s is None:
        return b""
    if s.startswith("0x"):
        return bytes.fromhex(s[2:])
    return s.encode()

def _standard_test(filename, secured, kv):
    print(f"Testing {filename}:")
    tests = _load_standard_test(filename)

    for name, test in tests.items():
        store = HashTable()
        trie = MerklePatriciaTrie(store)

        if kv:
            items = test["in"].items()
        else:
            items = test["in"]
        for key, value in items:
            # trie.dump() # TODO remove
            trie = trie.set(_to_bytes(key), _to_bytes(value))

        actual = trie.root
        # trie.dump() # TODO remove
        expected = bytes.fromhex(test["root"][2:])
        if actual == expected:
            print(f"    {name}: passed")
        else:
            print(f"    {name}: failed ({actual.hex()} != {expected.hex()})")

def _standard_tests():
    #_standard_test("hex_encoded_securetrie_test.json", True, True)
    #_standard_test("trietest_secureTrie.json", True, False)
    #_standard_test("trieanyorder_secureTrie.json", True, True)
    _standard_test("trietest.json", False, False)
    _standard_test("trieanyorder.json", False, True)

if __name__ == "__main__":
    _my_tests()
    _standard_tests()
