from flask import Flask, jsonify, request, send_from_directory # request allows to extract data from incoming request, send_from_directory allows to send back a file
from flask_cors import CORS # allow only clients on a server can send http request to it 

from wallet import Wallet
from blockchain import Blockchain

# Python server: RESTFUL Api using Flask
app = Flask(__name__)
CORS(app)

#### Root route: returns a node.html file inside a folder. 
   ## This is how we connect a client (node.html | desktop app | mobile app) to a server, an alternative to postman app
@app.route('/', methods=['GET'])
def get_node_ui():
    return send_from_directory('ui', 'node.html') # 'This domain works!'

# Connect network.html to server via /network
@app.route('/network', methods=['GET'])
def get_network_ui():
    return send_from_directory('ui', 'network.html') 

## Helper routes

# Create keys in a wallet
@app.route('/wallet', methods=['POST'])
def create_keys():
    wallet.create_keys()
    if wallet.save_keys():  # save keys into a file    
        global blockchain
        blockchain = Blockchain(wallet.public_key, port) # update the global blockchain with the newly created key
        response = {'public_key': wallet.public_key, 'private_key': wallet.private_key,  'funds': blockchain.get_balance()}
        return jsonify(response), 201
    else:
        response = {'message': 'Saving the keys failed'}
        return jsonify(response), 500

# Load the keys
@app.route('/wallet', methods=['GET'])    
def load_keys():
    if wallet.load_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port) # update the global blockchain with the newly created key
        response = {'public_key': wallet.public_key, 'private_key': wallet.private_key, 'funds': blockchain.get_balance()}
        return jsonify(response), 201
    else:
        response = {'message': 'Loading the keys failed'}
        return jsonify(response), 500
    
# Get Balance
@app.route('/balance', methods=['GET'])
def get_balance():
    balance = blockchain.get_balance()
    if balance != None:
        response = {'message': 'Fetched balance successfully', 'funds': balance}
        return jsonify(response), 200
    else:
        response = {'message': 'Loading balance failed', 'wallet_set_up': wallet.public_key != None}
        return jsonify(response), 500

#################################

# Add Broadcast route to the receiver peer_node
@app.route('/broadcast-transaction', methods=['POST'])
def broadcast_transaction():
    data = request.get_json() # Extract transaction as dict_data in json format from this incoming request
    if not data:
        response = {'message': 'No transaction data found in this incoming request.'}
        return jsonify(response), 400
    required = ['sender', 'recipient', 'amount', 'signature']
    if not all(key in data for key in required):
        response = {'message': 'Some data is missing.'}
        return jsonify(response), 400 
    # Calling add_transaction without contacting the peer_node of the peer_node of the peer_node ...
    success = blockchain.add_transaction(data['recipient'], data['sender'], data['signature'], data['amount'], is_receiving=True)
    if success:
        response = {
            'message': 'Successfully added transaction', 
            'transaction': {
                'sender': data['sender'], 
                'recipient': data['recipient'],
                'signature': data['signature'], 
                'amount': data['amount']    
            } 
        }
        return jsonify(response), 201
    else:
        response = {'message': 'Adding a transaction failed.'}
        return jsonify(response), 500
    
# Broadcasting a new block to receiver peer_node
@app.route('/broadcast-block', methods=['POST'])
def broadcast_block():
    data = request.get_json() # Extract block as dict_data in json format from this incoming request
    if not data:
        response = {'message': 'No block data found in this incoming request.'}
        return jsonify(response), 400
    if 'block' not in data: # only one block is expected
        response = {'message': 'Some block data is missing.'}
        return jsonify(response), 400
    block = data['block']
    if block['index'] == blockchain.chain[-1].index + 1: # if incoming block is accepted, i.e. index is equals to local blockchain index
        if blockchain.add_block(block):
            response = {'message': 'Block added when broadcasting.'}
            return jsonify(response), 201
        else:
            response = {'message': 'Block seems invalid when broadcasting.'}
            return jsonify(response), 409 # conflict but we don't to deal with it rn
    elif block['index'] > blockchain.chain[-1].index: # if True then it's a problem on the peer node -> (conflict)
        response = {'message': 'Blockchain seems to differ from local blockchain.'}
        blockchain.resolve_conflicts = True
        return jsonify(response), 200 # we will have to deal with that
    else:
        response = {'message': 'Blockchain seems to be shorter than peer\'s, block not added'}
        return jsonify(response, 409) # Invalid incoming data

# Add a transaction
@app.route('/transaction', methods=['POST'])
def add_transaction():
    if wallet.public_key == None:
        response = {'message': 'No wallet set up.'}
        return jsonify(response), 400
    data = request.get_json()  # data in json format from this incoming request
    if not data:
        response = {'message': 'No transaction data found in this incoming request.'}
        return jsonify(response), 400
    required_fields = ['recipient', 'amount']
    if not all(field in data for field in required_fields):
        response = {'message': 'Required data is missing.'}
        return jsonify(response), 400
    recipient = data['recipient']
    amount = data['amount']
    signature = wallet.sign_transaction(wallet.public_key, recipient, amount)
    success = blockchain.add_transaction(recipient, wallet.public_key, signature, amount)
    if success:
        response = {
            'message': 'Successfully added transaction', 
            'transaction': {
                'sender': wallet.public_key, 
                'recipient': recipient, 
                'amount': amount, 
                'signature': signature
            },
            'funds': blockchain.get_balance() 
        }
        return jsonify(response), 201
    else:
        response = {'message': 'Adding a transaction failed.'}
        return jsonify(response), 500

@app.route('/mine', methods=['POST'])
def mine():
    if blockchain.resolve_conflicts: # Conflict check
        response = {'message': 'Resolve conflicts first, block not added!'}
        return jsonify(response), 409
    
    block = blockchain.mine_block()
    
    if block != None:
        dict_block = block.__dict__.copy() # convert object block to a dict_block
        dict_block['transactions'] = [tx.__dict__ for tx in dict_block['transactions']]
        response = {'message': 'Block added successfully', 'block': dict_block, 'funds': blockchain.get_balance()}
        return jsonify(response), 201
    else: 
        response = {'message': 'Adding a block failed', 'wallet_set_up': wallet.public_key != None}
        return jsonify(response), 500

# Resolve Conflict route
@app.route('/resolve-conflicts', methods=['POST'])
def resolve_conflicts():
    replaced = blockchain.resolve()
    if replaced:
        response = {'message': 'Chain was replaced!'}
    else:
        response = {'message': 'Local chain kept!'}
    return jsonify(response), 200

# Getting the list of open_transactions
@app.route('/transactions', methods=['GET'])
def get_open_transactions():
    transactions = blockchain.get_open_transactions()
    dict_transactions = [tx.__dict__ for tx in transactions]
    return jsonify(dict_transactions), 200

@app.route('/chain', methods=['GET'])
def get_chain():
    chain_snapshot = blockchain.chain
    dict_chain = [block.__dict__.copy() for block in chain_snapshot]
    for dict_block in dict_chain:
        dict_block['transactions'] = [tx.__dict__ for tx in dict_block['transactions']] # update the tx as __dict__
    return jsonify(dict_chain), 200

# Add node route without a wallet
@app.route('/node', methods=['POST'])
def add_node():
    data = request.get_json() # receive the node passed as args in the request in json format
    if not data:
        response = {'message': 'No node data attached to the incoming request.'}
        return jsonify(response), 400
    if 'node' not in data:
        response = {'message': 'No node found in data.'}
        return jsonify(response), 400
    node = data['node']
    blockchain.add_peer_node(node)
    response = {'message': 'Node added successfully.', 'all_nodes': blockchain.get_peer_nodes()}
    return jsonify(response), 201

# Remove node route where the node URL is passed in the path
@app.route('/node/<node_url>', methods=['DELETE']) # Flask notation to pass a <node_url>
def remove_node(node_url):
    if node_url ==  '' or node_url == None or node_url not in blockchain.get_peer_nodes(): 
        response = {'message': 'Node not found.'}
        return jsonify(response), 400
    else:
        blockchain.remove_peer_node(node_url)
        response = {'message': 'Node removed', 'all_nodes': blockchain.get_peer_nodes()}
        return jsonify(response), 200
    
@app.route('/nodes', methods=['GET'])
def get_nodes():
    nodes = blockchain.get_peer_nodes()
    response = {'all_nodes': nodes}
    return jsonify(response), 200


###### Setting the domain for a Network of Nodes: python node.py -p 5000 | node.py -p 5005 | etc.  

if __name__ == '__main__':
    from argparse import ArgumentParser 
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=5000)
    args = parser.parse_args() # to extract the above args
    port = args.port # to access the port arg (print(args))
    wallet = Wallet(port)
    blockchain = Blockchain(wallet.public_key, port)

    app.run(host='0.0.0.0', port=port) # localhost/5000/ +path, where path is defined in each route