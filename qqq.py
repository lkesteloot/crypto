
import os.path
import rlp
import eth

SNAPSHOT_PATHNAME = "snapshot.json"

blocks_binary = open("/Users/lk/go/bin/out-all", "rb").read()

e = eth.EthereumVirtualMachine()
if os.path.exists(SNAPSHOT_PATHNAME):
    e.load_snapshot(SNAPSHOT_PATHNAME)

debug_block_number = 46402
sender = eth.Account.parse_address("a1e4380a3b1f749673e270229993ee55f35663b4")
recipient = eth.Account.parse_address("c9d4035f4a9226d50f79b73aafb5d874a1b6537e")
beneficiary = eth.Account.parse_address("bb7b8287f3f0a933474a79eae42cbca977791171")

for block_list in rlp.decode_multiple(blocks_binary):
    b = eth.Block.from_list(block_list)

    if e.should_skip_block(b.header.number):
        #print("Skipping block %d, older than most recent %d" %
        #        (b.header.number, e.head_block_number))
        continue

    if b.header.number == debug_block_number:
        b.dump()
        e.dump_account(sender)
        e.dump_account(recipient)
        e.dump_account(beneficiary)

    e.process_block(b)

    # sender = 0xa1e4380a3b1f749673e270229993ee55f35663b4
    if b.header.number == debug_block_number:
        e.dump_account(sender)
        e.dump_account(recipient)
        e.dump_account(beneficiary)
        e.dump()
        break

    if b.header.number % 1000 == 0:
        e.save_snapshot(SNAPSHOT_PATHNAME)

