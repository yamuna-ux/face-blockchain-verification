import json
import hashlib
import os
from datetime import datetime

BLOCKCHAIN_FILE = "output/blockchain.json"


def calculate_hash(block):
    block_copy = block.copy()
    block_copy.pop("hash", None)

    encoded = json.dumps(
        block_copy,
        sort_keys=True,
        separators=(",", ":")
    ).encode()

    return hashlib.sha256(encoded).hexdigest()


def create_genesis_block():

    block = {
        "index": 0,
        "timestamp": datetime.now().isoformat(),
        "type": "GENESIS",
        "data": "Face ID Blockchain",
        "previous_hash": "0"
    }

    block["hash"] = calculate_hash(block)

    return block


def load_blockchain():

    os.makedirs("output", exist_ok=True)

    if not os.path.exists(BLOCKCHAIN_FILE):

        chain = [create_genesis_block()]

        save_blockchain(chain)

        return chain

    try:

        with open(BLOCKCHAIN_FILE, "r") as f:
            chain = json.load(f)

        if not chain:
            chain = [create_genesis_block()]
            save_blockchain(chain)

        return chain

    except Exception:

        chain = [create_genesis_block()]
        save_blockchain(chain)

        return chain


def save_blockchain(chain):

    with open(BLOCKCHAIN_FILE, "w") as f:
        json.dump(chain, f, indent=4)


def register_face(identity_id, image_hash, embedding_hash):

    chain = load_blockchain()

    previous_block = chain[-1]

    block = {
        "index": len(chain),
        "timestamp": datetime.now().isoformat(),
        "type": "FACE_REGISTRATION",

        "data": {
            "identity_id": identity_id,
            "image_sha256": image_hash,
            "embedding_sha256": embedding_hash
        },

        "previous_hash": previous_block["hash"]
    }

    block["hash"] = calculate_hash(block)

    chain.append(block)

    save_blockchain(chain)

    return block


def verify_blockchain():

    chain = load_blockchain()

    if not chain:
        return False

    for i, block in enumerate(chain):

        calculated_hash = calculate_hash(block)

        if block["hash"] != calculated_hash:
            return False

        if i == 0:

            if block["previous_hash"] != "0":
                return False

        else:

            previous_block = chain[i - 1]

            if block["previous_hash"] != previous_block["hash"]:
                return False

    return True


def get_registration_blocks():

    chain = load_blockchain()

    return [
        block
        for block in chain
        if block.get("type") == "FACE_REGISTRATION"
    ]