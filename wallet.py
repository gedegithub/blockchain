from Crypto.PublicKey import RSA # Third party package 'pycryptodome' installed in pycoin env in anaconda navigator where Crypto != pycryptodome
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import Crypto.Random
import binascii

# Wallet holds a key, value pair which is private_key, public_key
class Wallet:
    def __init__(self, node_id):
        self.private_key = None 
        self.public_key = None
        self.node_id = node_id

    # Create the keys and set their values in Wallet class
    def create_keys(self):
        private_key, public_key = self.generate_keys() # Unpacking private_key & public_key
        self.private_key = private_key 
        self.public_key = public_key 

    # write keys to a file iff private & public keys exist
    def save_keys(self):
        if self.public_key != None and self.private_key != None:
            try:
                with open('wallet-{}.txt'.format(self.node_id), mode='w') as f:
                    f.write(self.public_key)
                    f.write('\n')
                    f.write(self.private_key)
                return True
            except(IOError, IndexError):
                print('Saving wallet.txt failed!')
                return False

    # Loading keys is like loading and uuid. We keep working with the history of those keys
    def load_keys(self):
        try:
            with open('wallet-{}.txt'.format(self.node_id), mode='r') as f:
                keys = f.readlines()
                public_key = keys[0][:-1] # to exclude the last character which is '\n'
                private_key = keys[1]
                self.public_key = public_key
                self.private_key = private_key
            return True
        except(IOError, IndexError):
            print('Loading wallet.txt failed!')
            return False

    # Generating keys with RSA
    def generate_keys(self):
        private_key = RSA.generate(1024, Crypto.Random.new().read) # The higher the bits ex. 1024 the longer it takes but the safer it is
        public_key = private_key.public_key()
        # return private_key & public_key from binary format to string format as tuple (prK, puK)
        return (binascii.hexlify(private_key.export_key(format='DER')).decode('ascii'), binascii.hexlify(public_key.export_key(format='DER')).decode('ascii'))
    
    # Sign a transaction with the private_key
    def sign_transaction(self, sender, recipient, amount):
        signer= PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(self.private_key)))
        hash_payload = SHA256.new((str(sender) + str(recipient) + str(amount)).encode('utf8'))
        signature = signer.sign(hash_payload)
        return binascii.hexlify(signature).decode('ascii')
    
    # Verify the signature of transaction
    @staticmethod
    def verify_tx_signature(transaction):
        """ Verify the signature of a transaction 
        Arguments:
           :transaction: The transaction that should be verified
        """
        public_key = RSA.import_key(binascii.unhexlify(transaction.sender))
        verifier = PKCS1_v1_5.new(public_key)
        hash_pl = SHA256.new((str(transaction.sender) + str(transaction.recipient) + str(transaction.amount)).encode('utf8')) 

        return verifier.verify(hash_pl, binascii.unhexlify(transaction.signature))