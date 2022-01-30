
import rlp
import eth

blocks_binary = open("/Users/lk/go/bin/out-all", "rb").read()

e = eth.EthereumVirtualMachine()

# For block 46147
a1 = eth.Account.parse_address("a1e4380a3b1f749673e270229993ee55f35663b4")
a2 = eth.Account.parse_address("5df9b87991262f6ba471f09758cde1c0fc1de734")
be  = eth.Account.parse_address("e6a7a1d47ff21b6321162aea7c6cb457d5476bca")

for block_list in rlp.decode_multiple(blocks_binary):
    b = eth.Block.from_list(block_list)

    if b.header.number == 46147:
        b.dump()
        e.dump_account(a1)
        e.dump_account(a2)
        e.dump_account(be)

    e.process_block(b)

    # sender = 0xa1e4380a3b1f749673e270229993ee55f35663b4
    if b.header.number == 46147:
        e.dump_account(a1)
        e.dump_account(a2)
        e.dump_account(be)
        e.dump()
        break

