
# Various data structures for Ethereum.

import random
import ecc
import rlp
import mpt
from ethsha3 import ethsha3

WEI_PER_ETHER = 10**18

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
        return Account(self.nonce, self.balance - amount, self.storage_root, self.code_hash)

    def credit(self, amount):
        return Account(self.nonce, self.balance + amount, self.storage_root, self.code_hash)

    def encode(self):
        # TODO match real Eth encoding.
        v = [rlp.encode_int(self.nonce), rlp.encode_int(self.balance),
                self.storage_root, self.code_hash]
        return rlp.encode(v)

    def __repr__(self):
        return "Account[%d,%d,%s,%s]" % (self.nonce, self.balance,
                self.storage_root, self.code_hash)

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

class Transaction:
    def __init__(self, from_account, to_account, amount):
        assert isinstance(from_account, bytes)
        assert isinstance(to_account, bytes)
        assert isinstance(amount, int)

        self.from_account = from_account
        self.to_account = to_account
        self.amount = amount

class Block:
    # https://ethereum.org/en/developers/docs/blocks/
    def __init__(self, previous_block, state, transactions):
        # TODO should previous_block be a block or be hash of previous block?
        assert previous_block is None or isinstance(previous_block, Block)
        self.previous_block = previous_block
        # TODO this state is mutable, so really we should take the has and be able
        # to look up the hash somewhere.
        self.state = state
        # TODO don't store these.
        self.transactions = transactions

    def __repr__(self):
        parts = []
        for key, value in self.state.items():
            parts.append("0x" + key.hex() + " = " + str(Account.decode(value)))
        return ", ".join(parts)

class EthereumVirtualMachine:
    def __init__(self):
        self.SECP256K1 = ecc.EllipticCurve.secp256k1()
        self.hash_table = mpt.HashTable()
        self.head_block = Block(None, mpt.MerklePatriciaTrie(self.hash_table), [])

    def set_new_head_block(self, block):
        assert block.previous_block == self.head_block
        self.head_block = block

    # TODO clean up
    def make_new_account(self):
        private_key = random.randrange(1, self.SECP256K1.f.size)
        public_key = self.SECP256K1.G*private_key
        # TODO not sure this is right, can't find formal definition of ECDSAPUBKEY:
        public_key_bytes = public_key.value[0].value.to_bytes(32, "big") + public_key.value[1].value.to_bytes(32, "big")
        address = ethsha3(public_key_bytes)[-20:] # Right-most 160 bits.
        print("Just created address 0x" + address.hex())

        return private_key, address

    def mine_block(self, old_block, transactions):
        # Make up a block that wins the mining ether.
        _, address = self.make_new_account()

        mining_transaction = Transaction(mpt.NO_HASH, address, WEI_PER_ETHER)
        transactions = [mining_transaction] + transactions

        state = old_block.state

        for transaction in transactions:
            if transaction.from_account == mpt.NO_HASH:
                if transaction is not mining_transaction:
                    raise Exception("Can't transfer from null account")
            else:
                from_account = state.get(transaction.from_account)
                assert from_account is not None
                from_account = Account.decode(from_account)
                assert from_account.balance >= transaction.amount
                state = state.set(transaction.from_account, from_account.debit(transaction.amount).encode())

            to_account = state.get(transaction.to_account)
            if to_account == None:
                to_account = Account(0, 0, mpt.NO_HASH, mpt.NO_HASH)
            # TODO use address raw?
            state = state.set(transaction.to_account, to_account.credit(transaction.amount).encode())

        block = Block(self.head_block, state, transactions)

        return block

    def __repr__(self):
        return "EVM:\n   Block:\n" + repr(self.head_block)


if __name__ == "__main__":
    a = Account(5, 123, b"abc", b"do-re-mi")
    b = a.encode()
    c = Account.decode(b)
    assert a == c
    print("Account pass")

    evm = EthereumVirtualMachine()
    new_block = evm.mine_block(evm.head_block, [])
    evm.set_new_head_block(new_block)
    print(evm)
    t = evm.head_block.transactions[0]
    _, address = evm.make_new_account()
    new_block = evm.mine_block(evm.head_block, [
        Transaction(t.to_account, address, 1),
        ])
    evm.set_new_head_block(new_block)
    print(evm)

    print("EVM pass")

