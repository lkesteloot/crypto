
# Various data structures for Ethereum.

from datetime import datetime
import random
import ecc
import rlp
import mpt
import ecdsa
from ethsha3 import ethsha3

WEI_PER_ETHER = 10**18
INDENT = "    "

SECP256K1 = ecc.EllipticCurve.secp256k1()

STRING_KEYS = set(["extraData"])
DATE_KEYS = set(["timestamp"])
PRICE_KEYS = set(["gasPrice", "value"])

# First block number of each named protocol update
HOMESTEAD = 1150000
TANGERINE_WHISTLE = 2463000
SPURIOUS_DRAGON = 2675000
BYZANTIUM = 4370000
CONSTANTINOPLE = 7280000
PETERSBURG = 7280000
ISTANBUL = 9069000
MUIR_GLACIER = 9200000
BERLIN = 12244000
LONDON = 12965000
ARROW_GLACIER = 13773000

def all_ascii(b):
    for ch in b:
        if ch < 32 or ch >= 127:
            return False
    return True

def dump_string(v, key):
    if isinstance(v, bytes) or isinstance(v, bytearray):
        if key in STRING_KEYS and all_ascii(v):
            v = '"' + v.decode("ascii") + '"'
        elif len(v) == 0:
            v = "(empty)"
        else:
            v = v.hex()
            if len(v) > 64:
                v = v[:64] + "..."
            v = "0x" + v
    elif isinstance(v, int):
        if key in DATE_KEYS:
            if v == 0:
                v = "Missing timestamp"
            else:
                v = datetime.fromtimestamp(v)
        elif key in PRICE_KEYS:
            exp = 0
            while v > 0 and v % 1000 == 0:
                v //= 1000
                exp += 3
            if exp > 0:
                v = "{:,}e{} Wei".format(v, exp)
            else:
                v = "{:,} Wei".format(v)

    return str(v)

def public_key_to_address(pu):
    # TODO not sure this is right, can't find formal definition of ECDSAPUBKEY:
    public_key_bytes = pu.x.value.to_bytes(32, "big") + pu.y.value.to_bytes(32, "big")
    return ethsha3(public_key_bytes)[-20:] # Right-most 160 bits.

class Account:
    def __init__(self, nonce, balance, storage_root, code_hash):
        assert isinstance(nonce, int)
        assert isinstance(balance, int)
        assert isinstance(storage_root, bytes)
        assert isinstance(code_hash, bytes)

        self.nonce = nonce
        self.balance = balance
        self.storage_root = storage_root
        self.code_hash = code_hash

    def debit(self, amount):
        assert amount >= 0
        if self.balance < amount:
            print("overdraft", self, amount)
        assert self.balance >= amount
        return Account(self.nonce, self.balance - amount, self.storage_root, self.code_hash)

    def credit(self, amount):
        assert amount >= 0
        return Account(self.nonce, self.balance + amount, self.storage_root, self.code_hash)

    def encode(self):
        v = [rlp.encode_int(self.nonce), rlp.encode_int(self.balance),
                self.storage_root, self.code_hash]
        return rlp.encode(v)

    def __repr__(self):
        return "Account[%d,%d,%s,%s]" % (self.nonce, self.balance,
                self.storage_root.hex(), self.code_hash.hex())

    def __eq__(self, o):
        return self.nonce == o.nonce and \
                self.balance == o.balance and \
                self.storage_root == o.storage_root and \
                self.code_hash == o.code_hash

    @staticmethod
    def decode(v):
        v = rlp.decode(v)
        assert isinstance(v, list)
        assert len(v) == 4
        return Account(
                rlp.decode_int(v[0]),
                rlp.decode_int(v[1]),
                v[2], v[3])

    # Parse an account hex string to a bytes. The string must represent 20 bytes
    # (have 40 characters) and may include an initial "0x".
    @staticmethod
    def parse_address(hex_address):
        return int(hex_address, 16).to_bytes(20, "big")

class Transaction:
    def __init__(self, nonce, gasPrice, gasLimit, toAddress, value, data, v, r, s):
        self.nonce = nonce
        self.gasPrice = gasPrice
        self.gasLimit = gasLimit
        self.toAddress = toAddress
        self.value = value
        self.data = data
        self.v = v
        self.r = r
        self.s = s
        self.sender = self.compute_sender()

    @staticmethod
    def from_list(v):
        assert isinstance(v, list) or isinstance(v, tuple)
        assert len(v) == 9

        return Transaction(rlp.decode_int(v[0]), rlp.decode_int(v[1]), rlp.decode_int(v[2]), v[3],
                rlp.decode_int(v[4]), v[5], rlp.decode_int(v[6]),
                rlp.decode_int(v[7]), rlp.decode_int(v[8]))

    def transaction_hash(self):
        data = [
                rlp.encode_int(self.nonce),
                rlp.encode_int(self.gasPrice),
                rlp.encode_int(self.gasLimit),
                self.toAddress,
                rlp.encode_int(self.value),
                self.data,
        ]
        assert self.v == 27 or self.v == 28 # else we have to add three things to "data".
        encoded_data = rlp.encode(data)
        return ethsha3(encoded_data)

    def compute_sender(self):
        e = int.from_bytes(self.transaction_hash(), "big")
        pu = ecdsa.recover_public_key(SECP256K1, e, self.v, self.r, self.s)
        # assert ecdsa.verify_signature(SECP256K1, pu, e, self.v, self.r, self.s)
        return public_key_to_address(pu)

    def dump(self, indent=""):
        for key, value in vars(self).items():
            print("%s%s = %s" % (indent, key, dump_string(value, key)))

class BlockHeader:
    def __init__(self, parentHash, ommersHash, beneficiary, stateRoot, transactionsRoot,
            receiptsRoot, logsBloom, difficulty, number, gasLimit, gasUsed, timestamp,
            extraData, mixHash, nonce):

        self.parentHash = parentHash
        self.ommersHash = ommersHash
        self.beneficiary = beneficiary
        self.stateRoot = stateRoot
        self.transactionsRoot = transactionsRoot
        self.receiptsRoot = receiptsRoot
        self.logsBloom = logsBloom
        self.difficulty = difficulty
        self.number = number
        self.gasLimit = gasLimit
        self.gasUsed = gasUsed
        self.timestamp = timestamp
        self.extraData = extraData
        self.mixHash = mixHash
        self.nonce = nonce

    @staticmethod
    def from_list(v):
        assert isinstance(v, list) or isinstance(v, tuple)
        assert len(v) == 15

        return BlockHeader(v[0], v[1], v[2], v[3], v[4], v[5], v[6], rlp.decode_int(v[7]),
                rlp.decode_int(v[8]), rlp.decode_int(v[9]), rlp.decode_int(v[10]),
                rlp.decode_int(v[11]), v[12], v[13], v[14])

    def dump(self, indent=""):
        for key, value in vars(self).items():
            print("%s%s = %s" % (indent, key, dump_string(value, key)))

    def compute_hash(self):
        v = [
                self.parentHash,
                self.ommersHash,
                self.beneficiary,
                self.stateRoot,
                self.transactionsRoot,
                self.receiptsRoot,
                self.logsBloom,
                rlp.encode_int(self.difficulty),
                rlp.encode_int(self.number),
                rlp.encode_int(self.gasLimit),
                rlp.encode_int(self.gasUsed),
                rlp.encode_int(self.timestamp),
                self.extraData,
                self.mixHash,
                self.nonce,
        ]
        b = rlp.encode(v)
        return ethsha3(b)

class Block:
    # https://ethereum.org/en/developers/docs/blocks/
    def __init__(self, header, transactions, ommers):
        self.header = header
        self.transactions = transactions
        self.ommers = ommers

    @staticmethod
    def decode(b):
        v = rlp.decode(b)
        return Block.from_list(v)

    @staticmethod
    def from_list(v):
        assert isinstance(v, list) or isinstance(v, tuple)
        assert len(v) == 3

        header = BlockHeader.from_list(v[0])
        transactions = [Transaction.from_list(t) for t in v[1]]
        ommers = [BlockHeader.from_list(h) for h in v[2]]

        return Block(header, transactions, ommers)

    def dump(self, indent=""):
        print(indent + "Block %d:" % self.header.number)
        indent += INDENT
        print(indent + "Header:")
        self.header.dump(indent + INDENT)
        print(indent + "Transactions (%d):" % len(self.transactions))
        for transaction in self.transactions:
            transaction.dump(indent + INDENT)
        print(indent + "Ommers (%d):" % len(self.ommers))

class EthereumVirtualMachine:
    def __init__(self):
        # Underlying storage.
        self.hash_table = mpt.HashTable()

        # Storage of current state.
        self.state = mpt.MerklePatriciaTrie(self.hash_table)

        self.head_block_hash = b"\0"*32

    def process_block(self, b):
        assert b.header.parentHash == self.head_block_hash

        # The genesis block has implicit hard-coded transactions.
        if b.header.number == 0:
            assert len(b.transactions) == 0
            assert b.header.parentHash == b"\0"*32

            # Read genesis allocations. See genesis.go.
            print("Adding genesis transactions...")
            alloc = rlp.decode(open("genesis_mainnet_alloc.rlp", "rb").read())
            for address, value in alloc:
                # Rare case where there are leading zero bytes missing in the binary encoding.
                if len(address) < 20:
                    address = b"\0"*(20 - len(address)) + address

                # Process fake transaction.
                self.add_value_to_account(address, rlp.decode_int(value))

        # Process transactions.
        for transaction in b.transactions:
            self.add_value_to_account(transaction.sender, -transaction.value)
            self.add_value_to_account(transaction.toAddress, transaction.value)
            self.add_value_to_account(bloc.header.beneficiary, transaction.value)

        # Reward miner of this block.
        r_block = 5 if b.header.number < BYZANTIUM else 3 if b.header.number < CONSTANTINOPLE else 2
        r_block *= WEI_PER_ETHER
        r = r_block + len(b.ommers)*r_block//32
        if r != 0:
            self.add_value_to_account(b.header.beneficiary, r)

        # Reward miners of ommer blocks.
        for u in b.ommers:
            diff_i = u.number - b.header.number
            r = r_block + diff_i*r_block//8
            if r != 0:
                self.add_value_to_account(u.beneficiary, r)

        self.head_block_hash = b.header.compute_hash()

        print(b.header.stateRoot.hex(), self.state.root.hex())
        assert b.header.stateRoot == self.state.root

    def add_value_to_account(self, address, value):
        account = self.get_account(address)
        if account is None:
            account = Account(0, 0, b"", b"")
        if address.endswith(b"\x9b\x68\xc7\x88\x5c"): # TODO delete
            print("add_value_to_account", "0x" + address.hex(), value, account)
        if value > 0:
            account = account.credit(value)
        else:
            account = account.debit(-value)
        self.state = self.state.set(address, account.encode())

    def get_account(self, address):
        b = self.state.get(address)
        if b is mpt.NO_VALUE:
            return None
        else:
            return Account.decode(b)

    def dump_account(self, address):
        account = self.get_account(address)
        print("0x%s = %s" % (address.hex(), account))

    def dump(self, indent=""):
        print("%sEthereumVirtualMachine:" % indent)
        indent += INDENT
        print("%sHash of latest block: %s" % (indent, self.head_block_hash.hex()))
        print("%sEntries in hash table: %d" % (indent, len(self.hash_table)))
        print("%sEntries in state: %d" % (indent, len(self.state)))

