""" Provides verification helper methods """ # docstring for the module in the package

from utility.hash_util import hash_string_256, hash_block
from wallet import Wallet

class Verification():
    @staticmethod # for independent method
    def valid_proof(transactions, last_hash, proof):
        """PoW check based on proof & a condition (hash starts with '00') as transactions and last hash are static"""
        # Create a string with all the hash inputs with transactions as OrderedDict
        guess = (str([tx.to_ordered_dict() for tx in transactions]) + str(last_hash) + str(proof)).encode()
        # print(guess) # Debug: shows transactions as OrderedDict
        guess_hash = hash_string_256(guess)  # hash the string guess
        # print(guess_hash)
        return guess_hash[0:2] == "00"
    
    @classmethod # for method that depends on others. cls replaces self
    def verify_chain(cls, blockchain): # cls substitutes self for @classmethod
        """Compare the stored hash in a given block with the re-calculated hash of the previous block"""
        for index, block in enumerate(blockchain):
            if index == 0:
                continue
            if block.previous_hash != hash_block(blockchain[index - 1]):
                print(
                    "Stored hash in current block is not equal to previous hash of previous block"
                )
                return False
            # Call valid_proof excluding the reward transaction in transactions
            if not cls.valid_proof(block.transactions[:-1], block.previous_hash, block.proof):
                print("Proof of Work - PoW is invalid!")
                return False
        return True
    
    @staticmethod
    def verify_transaction(transaction, get_balance, check_funds=True):
        """ Verify a transaction by checking whether the sender has sufficient coins and/or the signature is good
        Arguments:
             :transaction: The transaction that should be verified
        """
        if check_funds:
            sender_balance = get_balance(transaction.sender)
            return sender_balance >= transaction.amount and Wallet.verify_tx_signature(transaction) # only when add_transaction
        return Wallet.verify_tx_signature(transaction) # from user_choice == 4 we already passed the fund check
    
    @classmethod
    def verify_transactions(cls, open_transactions, get_balance):
        """ Verify the validity of all transaction by checking just the signature """
        return all([cls.verify_transaction(tx, get_balance, False) for tx in open_transactions])
    
    