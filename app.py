from flask import Flask, render_template, request, jsonify
import os
import sys
import json
import hashlib
import uuid

import cv2
import numpy as np

from insightface.app import FaceAnalysis

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "src")
)

from blockchain import (
    register_face,
    verify_blockchain,
    load_blockchain
)


app = Flask(__name__)

UPLOAD_FOLDER = "input"
OUTPUT_FOLDER = "output"

IDENTITIES_FILE = os.path.join(
    OUTPUT_FOLDER,
    "identities.json"
)

BLOCKCHAIN_FILE = os.path.join(
    OUTPUT_FOLDER,
    "blockchain.json"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

FACE_MATCH_THRESHOLD = 0.40

DUPLICATE_THRESHOLD = 0.40


# --------------------------------------------------
# LOAD INSIGHTFACE ONCE
# --------------------------------------------------

print()
print("=" * 60)
print("       FACE ID BLOCKCHAIN WEB SERVER")
print("=" * 60)
print()
print("Loading InsightFace model...")

face_app = FaceAnalysis(
    name="buffalo_l"
)

face_app.prepare(
    ctx_id=0,
    det_size=(640, 640)
)

print("InsightFace model ready.")
print()


# --------------------------------------------------
# IDENTITY STORAGE
# --------------------------------------------------

def load_identities():

    if not os.path.exists(IDENTITIES_FILE):
        return []

    try:

        with open(IDENTITIES_FILE, "r") as f:
            return json.load(f)

    except Exception:

        return []


def save_identities(identities):

    with open(IDENTITIES_FILE, "w") as f:

        json.dump(
            identities,
            f,
            indent=4
        )


# --------------------------------------------------
# HASH FUNCTIONS
# --------------------------------------------------

def calculate_file_hash(filepath):

    sha256 = hashlib.sha256()

    with open(filepath, "rb") as f:

        while True:

            chunk = f.read(8192)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def calculate_embedding_hash(embedding):

    embedding_json = json.dumps(
        embedding.tolist(),
        separators=(",", ":")
    )

    return hashlib.sha256(
        embedding_json.encode()
    ).hexdigest()


# --------------------------------------------------
# COSINE SIMILARITY
# --------------------------------------------------

def cosine_similarity(embedding1, embedding2):

    denominator = (
        np.linalg.norm(embedding1)
        *
        np.linalg.norm(embedding2)
    )

    if denominator == 0:
        return 0.0

    return float(
        np.dot(
            embedding1,
            embedding2
        ) / denominator
    )


# --------------------------------------------------
# IMAGE PROCESSING
# --------------------------------------------------

def process_image(filepath):

    image = cv2.imread(filepath)

    if image is None:

        return None, {
            "success": False,
            "message": "Unable to read image."
        }

    faces = face_app.get(image)

    if len(faces) == 0:

        return None, {
            "success": False,
            "message": "No face detected."
        }

    if len(faces) > 1:

        return None, {
            "success": False,
            "message": (
                "Multiple faces detected. "
                "Please use an image containing exactly one face."
            )
        }

    face = faces[0]

    return face, None


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/")
def home():

    identities = load_identities()

    blockchain = load_blockchain()

    return render_template(
        "index.html",
        identities=identities,
        blockchain_valid=verify_blockchain(),
        blocks=len(blockchain)
    )


# --------------------------------------------------
# REGISTER PAGE
# --------------------------------------------------

@app.route("/register")
def register_page():

    return render_template(
        "register.html"
    )


# --------------------------------------------------
# VERIFY PAGE
# --------------------------------------------------

@app.route("/verify")
def verify_page():

    return render_template(
        "verify.html"
    )


# --------------------------------------------------
# SYSTEM STATUS
# --------------------------------------------------

@app.route("/api/status")
def status():

    identities = load_identities()

    blockchain = load_blockchain()

    return jsonify({

        "success": True,

        "registered": len(identities) > 0,

        "identity_count": len(identities),

        "block_count": len(blockchain),

        "blockchain_valid":
            verify_blockchain(),

        "embedding_dimensions": 512,

        "threshold":
            FACE_MATCH_THRESHOLD

    })


# --------------------------------------------------
# REGISTER FACE
# --------------------------------------------------

@app.route(
    "/api/register",
    methods=["POST"]
)
def api_register():

    if "image" not in request.files:

        return jsonify({
            "success": False,
            "message": "No image uploaded."
        }), 400


    image_file = request.files["image"]


    if image_file.filename == "":

        return jsonify({
            "success": False,
            "message": "Please select an image."
        }), 400


    filepath = os.path.join(
        UPLOAD_FOLDER,
        "registration_capture.jpg"
    )


    image_file.save(filepath)


    # Face detection

    face, error = process_image(
        filepath
    )


    if error:

        return jsonify(error), 400


    embedding = face.embedding


    image_hash = calculate_file_hash(
        filepath
    )


    embedding_hash = calculate_embedding_hash(
        embedding
    )


    # --------------------------------------------------
    # DUPLICATE REGISTRATION CHECK
    # --------------------------------------------------

    identities = load_identities()


    for identity in identities:

        stored_embedding = np.array(
            identity["embedding"],
            dtype=np.float32
        )


        similarity = cosine_similarity(
            embedding,
            stored_embedding
        )


        if similarity >= DUPLICATE_THRESHOLD:

            return jsonify({

                "success": False,

                "duplicate": True,

                "message":
                    "This face is already registered.",

                "identity_id":
                    identity["identity_id"],

                "similarity":
                    round(similarity, 4),

                "threshold":
                    DUPLICATE_THRESHOLD

            }), 409


    # --------------------------------------------------
    # CREATE NEW IDENTITY
    # --------------------------------------------------

    identity_id = (
        "FACE-"
        +
        uuid.uuid4().hex[:10].upper()
    )


    identity = {

        "identity_id":
            identity_id,

        "created_at":
            __import__("datetime")
            .datetime.now()
            .isoformat(),

        "image_sha256":
            image_hash,

        "embedding_sha256":
            embedding_hash,

        "embedding_dimensions":
            len(embedding),

        "detection_confidence":
            float(face.det_score),

        "embedding":
            embedding.tolist()

    }


    identities.append(identity)


    save_identities(
        identities
    )


    # --------------------------------------------------
    # BLOCKCHAIN REGISTRATION
    # --------------------------------------------------

    block = register_face(

        identity_id,

        image_hash,

        embedding_hash

    )


    blockchain_valid = verify_blockchain()


    return jsonify({

        "success": True,

        "message":
            "Face registered successfully.",

        "identity_id":
            identity_id,

        "confidence":
            round(
                float(face.det_score),
                4
            ),

        "dimensions":
            len(embedding),

        "block_index":
            block["index"],

        "block_hash":
            block["hash"],

        "blockchain_valid":
            blockchain_valid

    })


# --------------------------------------------------
# VERIFY FACE
# --------------------------------------------------

@app.route(
    "/api/verify",
    methods=["POST"]
)
def api_verify():

    if "image" not in request.files:

        return jsonify({

            "success": False,

            "message":
                "No image uploaded."

        }), 400


    image_file = request.files["image"]


    if image_file.filename == "":

        return jsonify({

            "success": False,

            "message":
                "Please select an image."

        }), 400


    filepath = os.path.join(
        UPLOAD_FOLDER,
        "verification_capture.jpg"
    )


    image_file.save(filepath)


    # Face detection

    face, error = process_image(
        filepath
    )


    if error:

        return jsonify(error), 400


    test_embedding = face.embedding


    identities = load_identities()


    if not identities:

        return jsonify({

            "success": False,

            "message":
                "No registered identity found."

        }), 404


    # --------------------------------------------------
    # FIND BEST MATCH
    # --------------------------------------------------

    best_identity = None

    best_similarity = -1


    for identity in identities:

        registered_embedding = np.array(

            identity["embedding"],

            dtype=np.float32

        )


        similarity = cosine_similarity(

            test_embedding,

            registered_embedding

        )


        if similarity > best_similarity:

            best_similarity = similarity

            best_identity = identity


    # --------------------------------------------------
    # BLOCKCHAIN CHECK
    # --------------------------------------------------

    blockchain_valid = verify_blockchain()


    face_match = (
        best_similarity >=
        FACE_MATCH_THRESHOLD
    )


    verified = (
        face_match
        and
        blockchain_valid
    )


    verification_hash = calculate_embedding_hash(
        test_embedding
    )


    return jsonify({

        "success": True,

        "verified":
            verified,

        "face_match":
            face_match,

        "similarity":
            round(
                best_similarity,
                4
            ),

        "threshold":
            FACE_MATCH_THRESHOLD,

        "identity_id":
            best_identity["identity_id"]
            if face_match
            else None,

        "detection_confidence":
            round(
                float(face.det_score),
                4
            ),

        "embedding_dimensions":
            len(test_embedding),

        "verification_embedding_hash":
            verification_hash,

        "blockchain_valid":
            blockchain_valid,

        "registered_identities":
            len(identities),

        "message":

            "Face verified successfully."

            if verified

            else

            "Face verification failed."

    })


# --------------------------------------------------
# BLOCKCHAIN API
# --------------------------------------------------

@app.route("/api/blockchain")
def blockchain_api():

    chain = load_blockchain()


    return jsonify({

        "success": True,

        "valid":
            verify_blockchain(),

        "blocks":
            chain

    })


# --------------------------------------------------
# IDENTITIES API
# --------------------------------------------------

@app.route("/api/identities")
def identities_api():

    identities = load_identities()


    safe_identities = []


    for identity in identities:

        safe_identities.append({

            "identity_id":
                identity["identity_id"],

            "created_at":
                identity["created_at"],

            "embedding_dimensions":
                identity["embedding_dimensions"],

            "detection_confidence":
                identity["detection_confidence"]

        })


    return jsonify({

        "success": True,

        "identities":
            safe_identities

    })


# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=False

    )
