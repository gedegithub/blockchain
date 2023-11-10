from uuid import uuid4

from blockchain import Blockchain
from utility.verification import Verification
from wallet import Wallet

class Node: # ui class where every Node is a host
    def __init__(self):
        self.wallet = Wallet() # self.id = 'MAX' | self.id = str(uuid4())
        ########## These two lines of code is duplicated in if user_input == '5' ##########
        self.wallet.create_keys() 
        self.blockchain = Blockchain(self.wallet.public_key)

    def get_transaction_value(self):
        """Returns the input of the user (a new transaction) as a (sender, recipient, tx_amount)"""
        tx_recipient = input("Enter the recipient of the transaction: ")
        tx_amount = input("Your transaction amount please: ")
        print("-" * 20)
        return (tx_recipient, float(tx_amount))
    
    def get_user_choice(self):
        user_input = input("Your choice: ")
        return user_input

    def print_blockchain_elements(self):
        # Output the blockchain list to the console
        # print(self.blockchain)
        for block in self.blockchain.chain:
            print("Outputting Block")
            print(block)
        print("-" * 20)

    def listen_for_input(self):
        waiting_for_input = True
        # Add transaction input or print the blocks of the blockchain infinitely
        while waiting_for_input:
            print('Please choose!')
            print('-' * 20)
            print('\t1: Add a new transaction value')
            print('\t2: Mine a new block')
            print('\t3: Output the blockchain blocks')
            print('\t4: Check all transactions validity')
            print('\t5: Create Wallet')
            print('\t6: Load Wallet')
            print('\t7: Save keys into file')
            # print("\th: Manipulate the chain")
            print('\tq: Quit')

            user_choice = self.get_user_choice()

            if user_choice == '1':
                tx_data = self.get_transaction_value()
                recipient, amount = tx_data  # unpacking: like destructuring in JS
                signature = self.wallet.sign_transaction(self.wallet.public_key, recipient, amount)
                if self.blockchain.add_transaction(recipient, self.wallet.public_key, signature, amount=amount): # self.wallet.public_key replaces self.id
                    print("Added transaction successfully!")
                    print("-" * 20)
                else:
                    print("Transaction failed!")
                print(self.blockchain.get_open_transactions())
                print('-' * 20)
            elif user_choice == '2':
                if not self.blockchain.mine_block(): # after execution if mine_block did not succeed
                    print('Mining failed!')
            elif user_choice == '3':
                self.print_blockchain_elements()
            elif user_choice == '4':
                if Verification.verify_transactions(self.blockchain.get_open_transactions(), self.blockchain.get_balance):
                    print("All transactions are valid")
                else:
                    print("There are invalid transactions")
                print('-' * 20)
            elif user_choice == '5':
                self.wallet.create_keys() # Creating keys from the object wallet previously created
                self.blockchain = Blockchain(self.wallet.public_key) # Update the blockchain
            elif user_choice == '6':
                self.wallet.load_keys()
                self.blockchain = Blockchain(self.wallet.public_key) # Update the blockchain
            elif user_choice == '7':
                self.wallet.save_keys()
            elif user_choice == 'q':
                waiting_for_input = False
            else:
                print("Invalid input, please pick a value from the list")
            if not Verification.verify_chain(self.blockchain.chain):
                self.print_blockchain_elements()
                print("Invalid blockchain")
                print('-' * 20)
                break
            print("Balance of {}: {:6.2f}".format(self.wallet.public_key, self.blockchain.get_balance()))  # 6 digits with 2 decimals
        print("Done!")

# Module execution Context via __name__: in node.py it prints main, but it's blochain for blockchain.py & the other exported files
if __name__ == '__main__':
    print(__name__)
    node = Node()
    node.listen_for_input()

# Could have just been this without the if statement
# node = Node()
# node.listen_for_input() 