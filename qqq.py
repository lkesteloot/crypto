
import rlp
import eth

block_binary = open("/Users/lk/go/bin/out-1", "rb").read()

x = rlp.decode(block_binary)
rlp.dump_data(x)

b = eth.Block.decode(block_binary)
b.dump()

