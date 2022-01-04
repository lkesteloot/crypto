
import rlp
import eth

blocks_binary = open("/Users/lk/go/bin/out-all", "rb").read()

for block_list in rlp.decode_multiple(blocks_binary):
    b = eth.Block.from_list(block_list)

    if b.header.number == 46388:
        break

    if len(b.transactions) > 0:
        print(b.header.number, len(b.transactions))
        # sender = 0xa1e4380a3b1f749673e270229993ee55f35663b4
        if b.header.number == 46147:
            b.dump()
            break

