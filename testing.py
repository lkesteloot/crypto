
# Utilities for testing.

import random

# Return a random bytes object between min and max length inclusive.
def random_bytes(min_length, max_length):
    length = random.randint(min_length, max_length)
    return random.randbytes(length)

