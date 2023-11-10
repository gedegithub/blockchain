from time import time

from utility.printable import Printable

class Block(Printable):
    def __init__(self, index, previous_hash, transactions, proof, timestamp=None): # constructor with a default time attribute
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.proof = proof
        self.timestamp = time() if timestamp is None else timestamp