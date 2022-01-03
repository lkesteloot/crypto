
import rlp
import eth

blocks_binary = open("/Users/lk/go/bin/out-all", "rb").read()

for block_list in rlp.decode_multiple(blocks_binary):
    b = eth.Block.from_list(block_list)
    if len(b.transactions) > 0 and b.header.number == 46147:
        b.dump()

