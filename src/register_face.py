import json
import hashlib
import uuid
from blockchain import register_face, verify_blockchain


EMBEDDING_FILE = "output/face_embedding.json"


def calculate_embedding_hash(embedding):
    """
    Creates a SHA-256 hash of the 512-dimensional face embedding.
    """

    embedding_string = json.dumps(embedding, separators=(",", ":"))

    return hashlib.sha256(
        embedding_string.encode("utf-8")
    ).hexdigest()


def main():

    print("=" * 55)
    print("       FACE ID - BLOCKCHAIN REGISTRATION")
    print("=" * 55)

    # --------------------------------------------------
    # 1. Load face embedding
    # --------------------------------------------------

    print("\n[1] Loading face embedding...")

    try:
        with open(EMBEDDING_FILE, "r", encoding="utf-8") as file:
            face_data = json.load(file)

    except FileNotFoundError:
        print("ERROR: face_embedding.json not found.")
        print("Run face_detection.py first.")
        return

    print("      Image:", face_data["image"])
    print("      Faces detected:", face_data["faces_detected"])
    print("      Embedding dimensions:", face_data["embedding_dimensions"])

    # --------------------------------------------------
    # 2. Get image hash
    # --------------------------------------------------

    image_hash = face_data["image_sha256"]

    print("\n[2] Image SHA-256:")
    print("     ", image_hash)

    # --------------------------------------------------
    # 3. Generate embedding hash
    # --------------------------------------------------

    embedding = face_data["embedding"]

    embedding_hash = calculate_embedding_hash(embedding)

    print("\n[3] Face embedding SHA-256:")
    print("     ", embedding_hash)

    # --------------------------------------------------
    # 4. Register on blockchain
    # --------------------------------------------------

    print("\n[4] Registering face on blockchain...")

    identity_id = (
    "FACE-"
    +
    uuid.uuid4().hex[:10].upper()
    )

    block = register_face(
       identity_id,
       image_hash,
       embedding_hash
    )

    print("      Registration successful!")

    # --------------------------------------------------
    # 5. Display block information
    # --------------------------------------------------

    print("\n[5] Blockchain Block Created")
    print("-" * 55)

    print("Block index:")
    print("     ", block["index"])

    print("\nBlock type:")
    print("     ", block["type"])

    print("\nTimestamp:")
    print("     ", block["timestamp"])

    print("\nPrevious hash:")
    print("     ", block["previous_hash"])

    print("\nBlock hash:")
    print("     ", block["hash"])

    # --------------------------------------------------
    # 6. Verify blockchain integrity
    # --------------------------------------------------

    print("\n[6] Checking blockchain integrity...")

    if verify_blockchain():
        print("      Blockchain integrity: VALID")
    else:
        print("      Blockchain integrity: INVALID")

    print("\n" + "=" * 55)
    print("       FACE REGISTRATION COMPLETED")
    print("=" * 55)


if __name__ == "__main__":
    main()