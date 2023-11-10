from hashlib import sha256
import json


def hash_string_256(string):
    """ function that takes a string encoded in UTF8 string format and generate a byte hash which is
    then converted to normal characters hash by using hexdigest.
    """
    return sha256(string).hexdigest()


def hash_block(block):
    """ Use sha256 algo from standard library to create a 64 characters deterministic hash. 
    sha256 takes a string as arg: binary string json encoded in UTF8 string format. Then
    sha256 generates a byte hash and hexdigest converts it to normal hash characters.

        Here, as a dictionary doesn't guaranty any order, we sort it by keys before stringify it.
    Also, we could have use OrderedDict. Order should be guarateed in transactions & reward_transaction
    as a hash is depending on them a well. Otherwise the hash can generate a different value if the order
    of the keys change in one of those dictionaries. This is call a hash order fault.    
    """
    # json can't take an object
    hashable_block = block.__dict__.copy() # make sure not to modify the object block to be manipulated by hash_string_256
    hashable_block['transactions'] = [tx.to_ordered_dict() for tx in hashable_block['transactions']]
    return hash_string_256(json.dumps(hashable_block, sort_keys=True).encode()) # sor_keys=True is still needed?
