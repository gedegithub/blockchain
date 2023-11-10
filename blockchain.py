from functools import reduce
from collections import OrderedDict
import json

from utility.hash_util import hash_block
from block import Block
from transaction import Transaction
from utility.verification import Verification
from wallet import Wallet
import requests # From Python package. Different from request from Flask package

MINING_REWARD = 10

class Blockchain:
    """The Blockchain class manages the chain of blocks as well as open transactions and the node on which it's running.

    Attributes:
        :chain: The list of blocks
        :open_transactions (private): The list of open transactions
        :hosting_node: The connected node (which runs the blockchain).
    """
    def __init__(self, public_key, node_id): # node_id to id the node on the Network of Nodes
        """The constructor of the Blockchain class."""
        genesis_block = Block(0, '', [], 100, 0) # Our starting block - which has a dummy proof of work for the blockchain
        self.chain = [genesis_block] # Initializing our empty blocchain initially using chain property
        self.__open_transactions = [] # Unhandled transactions, i.e. list of transactions to be added to the blochchain.
        self.public_key = public_key # where a public_key is stored
        self.node_id = node_id
        self.__peer_nodes = set() # set of peer nodes initialized to empty set before loading data from blockchain.txt
        self.resolve_conflicts = False
        self.load_data()

     # This turns the chain attribute into a property with a getter (the method below) and a setter (@chain.setter)
    @property
    def chain(self):
        return self.__chain[:] # retun a copy

    # The setter for the chain property
    @chain.setter
    def chain(self, val):
        self.__chain = val # pass # to avoid changing that property
    
    def get_open_transactions(self):
        return self.__open_transactions[:]

    # pickle is better than json: Override blockchain & open_transactions wouldn't have been necessary with picke
    def load_data(self):
        """ Initialize blockchain + open transactions data as OrderedDict from blockchain.txt then deserialize them 
            to Python object and load them to memory """
        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='r') as f:
                file_content = f.readlines()
                blockchain = json.loads(file_content[0][:-1])  # take the first line without \n
                # Transaction from Blockchain we loaded from blockchain.txt as a OrderDict
                updated_blockchain = []
                for block in blockchain:
                    converted_tx = [Transaction(tx["sender"], tx["recipient"], tx['signature'], tx["amount"]) for tx in block['transactions']]
                    updated_block = Block(block['index'], block['previous_hash'], converted_tx, block['proof'], block['timestamp'])
                
                    updated_blockchain.append(updated_block)
                self.__chain = updated_blockchain
                open_transactions = json.loads(file_content[1][:-1])  # Take 2nd line without \n
                # Open_transaction should be as OrderDict as well
                updated_transactions = []
                for tx in open_transactions:
                    updated_transaction = Transaction(tx["sender"], tx["recipient"], tx['signature'], tx["amount"])
                    updated_transactions.append(updated_transaction)
                self.__open_transactions = updated_transactions
                peer_nodes = json.loads(file_content[2])
                self.__peer_nodes = set(peer_nodes)
        except (IOError, IndexError):  # to handle file not found & empty file errors
            print('Handled exceptions: FNF & File empty ...')
        finally:
            print("Cleanup!")

    def save_data(self):
        """Write to dynamic file and let python close the file by using 'with' statetemnt"""
        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='w') as f:
                saveable_chain = [block.__dict__ for block in [Block(block_el.index, block_el.previous_hash, [tx.__dict__ for tx in block_el.transactions], block_el.proof, block_el.timestamp) for block_el in self.__chain]]
                f.write(json.dumps(saveable_chain))
                f.write('\n')
                saveable_tx = [tx.__dict__ for tx in self.__open_transactions]
                f.write(json.dumps(saveable_tx))
                f.write('\n')
                f.write(json.dumps(list(self.__peer_nodes)))
        except IOError:
            print('Saving to file failed!')

    def proof_of_work(self):
        """Generate PoW number as the check of stored hash == previous hash is not enough"""
        proof = 0
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)

        # Try different PoW numbers and return the first valid one
        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof

    def get_balance(self, sender=None):
        """ Calculate and return the balance for a particiapant """
        if sender == None:
            if self.public_key == None:
                return None
            participant = self.public_key # The node, i.e. the host will always sends the money
        else:
            participant = sender
        tx_sender = [[tx.amount for tx in block.transactions if tx.sender == participant] for block in self.__chain]
        open_tx_sender = [tx.amount for tx in self.__open_transactions if tx.sender == participant]
        tx_sender.append(open_tx_sender)  # add open transaction to tx_sender as well to prevent a sender from sending globally more than he has
        print(tx_sender)  # to debug *************************
        amount_sent = reduce(
            lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0,
            tx_sender,
            0,
        )  
        # This fetches received coin amounts of transactions that were already included in blocks of the blockchain
        # We ignore open transactions here because you shouldn't be able to spend coins before the transaction was confirmed + included in a block
        tx_recipient = [[tx.amount for tx in block.transactions if tx.recipient == participant] for block in self.__chain]
        amount_received = reduce(
            lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0,
            tx_recipient,
            0,
        )
        return amount_received - amount_sent

    def get_last_blockchain_value(self):
        """Returns the last value of the current blockchain."""
        if len(self.__chain) < 1:
            return None
        return self.__chain[-1]

    def add_transaction(self, recipient, sender, signature, amount=1.0, is_receiving=False):
        """Append a new value and the last blockchain value to the blockchain.

        Arguments:
        :sender: The sender of the coins.
        :recipient: The recipient of the coins.
        :amount: The amount of coins sent with the transaction (default = 1.0)
        """
        # without a public_key we can't add transaction
        # if self.public_key == None:
        #     return False
        # Creating a transaction object
        transaction = Transaction(sender, recipient, signature, amount)
       
        if Verification.verify_transaction(transaction, self.get_balance): # a ref to func get_balance
            self.__open_transactions.append(transaction)
            self.save_data()  # write to blockchain.txt
            # Broadcasting to the network by sending an http request iff we are on the node where that tx has been originally created
            if not is_receiving:
                for node in self.__peer_nodes:
                    url = 'http://{}/broadcast-transaction'.format(node)
                    try:
                        response = requests.post(url, json={'sender': sender, 'recipient': recipient, 'signature': signature, 'amount': amount})
                        if response.status_code == 400 or response.status_code == 500:
                            print('Transaction declined, needs resolving.')
                            return False
                    except requests.exceptions.ConnectionError:
                        continue # skip a node if it's down
            return True
        return False

    def mine_block(self):
        """Create a new block and add a copy of open transactions to it."""
        # Fetch the currently last block of the blockchain
        # Without a public_key we can't mine
        if self.public_key == None:
            return None #return False
        
        last_block = self.__chain[-1]
        hashed_block = hash_block(last_block)  # hash the last block to compare it to the stored hash value
        proof = self.proof_of_work()  # gen a proof of work number

        reward_transaction = Transaction("MINING", self.public_key, '', MINING_REWARD) # An unsigned mining transaction

        # Copy transaction instead of manipulating the original open_transactions list
        # This ensures that if for some reason the mining should fail, we don't have the reward transaction stored in the open transactions
        copied_transactions = self.__open_transactions[:]
        # Signatrue check for every single transaction in the block before appending the reward transaction
        for tx in copied_transactions:
            if not Wallet.verify_tx_signature(tx):
                return None # return False # As bonus, if false we should also remove that tx
        copied_transactions.append(reward_transaction)
        block = Block(len(self.__chain), hashed_block, copied_transactions, proof)

        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data()
        for node in self.__peer_nodes:
            url = 'http://{}/broadcast-block'.format(node)
            converted_block = block.__dict__.copy()
            converted_block['transactions'] = [tx.__dict__ for tx in converted_block['transactions']]
            try:
                response = requests.post(url, json={'block': converted_block})
                if response.status_code == 400 or response.status_code == 500:
                    print('Block declined, needs resolving.')
                if response.status_code == 409:
                    self.resolve_conflicts = True # Conflict
            except requests.exceptions.ConnectionError:
                continue # if any connection issue
        return block # return the block either True of False
   
   # Add a Block instead of mine_block
    def add_block(self, block):
        """Add a block which was received via broadcasting to the local blockchain."""
        # From list of dict_block to list of object_block
        transactions = [Transaction(tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']]
        # Validate the proof of work of the block and store the result (True or False) in a variable
        proof_is_valid = Verification.valid_proof(transactions[:-1], block['previous_hash'], block['proof']) # transaction[:-1] to exclude mining_tx
        # Check if previous_hash stored in the block is equal to the local blockchain's last block's hash and store the result in a block
        hashes_match = hash_block(self.chain[-1]) == block['previous_hash']
        if not proof_is_valid or not hashes_match:
            return False
        # Create a Block object
        converted_block = Block(block['index'], block['previous_hash'], transactions, block['proof'], block['timestamp'])
        self.__chain.append(converted_block)
        stored_transactions = self.__open_transactions[:]

        # Check which open transactions were included in the received block and remove them
        # This could be improved by giving each transaction an ID that would uniquely identify it
        for itx in block['transactions']:
            for opentx in stored_transactions:
                if opentx.sender == itx['sender'] and opentx.recipient == itx['recipient'] and opentx.amount == itx['amount'] and opentx.signature == itx['signature']:
                    try:
                        self.__open_transactions.remove(opentx)
                    except ValueError:
                        print('Item was already removed.')
        self.save_data()
        return True
    
    # Resolve conflicts return True or False
    def resolve(self):
        """Checks all peer nodes' blockchains and replaces the local one with longer valid ones."""
        winner_chain = self.chain
        replace = False
        for node in self.__peer_nodes:
            url = 'http://{}/chain'.format(node)
            try:
                response= requests.get(url) # Send a request and store the response
                node_chain = response.json() # Retrieve the JSON data as a dictionary
                # Convert the dictionary list to a list of block AND transaction objects
                node_chain = [Block(block['index'], block['previous_hash'], [Transaction(tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']], block['proof'], block['timestamp']) for block in node_chain]
                node_chain_length = len(node_chain)
                local_chain_length = len(winner_chain)
                # Store the received chain as the current winner chain if it's longer AND valid
                if node_chain_length > local_chain_length and Verification.verify_chain(node_chain):
                    winner_chain = node_chain
                    replace = True
            except requests.exceptions.ConnectionError:
                continue
        self.resolve_conflicts = False # Conflict solved at this point
        # Replace the local chain with the winner chain
        self.chain = winner_chain
        if replace:
            self.__open_transactions = []
        self.save_data()
        return replace

   # Peer Nodes 
    def add_peer_node(self, node):
        """ Add a new node to the peer node set 
        
        Arguments:
           :node: The node URL which should be added.
        """
        self.__peer_nodes.add(node)
        self.save_data()

    def remove_peer_node(self, node):
        """ Remove a node from the peer node set if it's there
        
        Arguments:
           :node: The node URL which should be removed.
        """
        self.__peer_nodes.discard(node) # remove if it exists
        self.save_data()

    def get_peer_nodes(self):
        """ Return a list of all connected peer nodes """
        return list(self.__peer_nodes)