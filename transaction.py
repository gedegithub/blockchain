from collections import OrderedDict

from utility.printable import Printable

class Transaction(Printable):
    """ A transaction which can be added to a block in the blockchain 
      Attributes"
        :sender: The sender of the coins
        :recipient: The recipient of the coins
        :signature: The signature of the transactions
        :amount: The amount of coins sent
    """
    def __init__(self, sender, recipient, signature, amount):
        self.sender = sender
        self.recipient = recipient # recipient is a public_key, like a uuid
        self.amount = amount
        self.signature = signature

    # To guarantee in the dictionary the keys keep the same order
    def to_ordered_dict(self):
        return OrderedDict([('sender', self.sender), ('recipient', self.recipient), ('amount', self.amount)])