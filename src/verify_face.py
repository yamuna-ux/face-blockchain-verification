import sys
import json
import hashlib
import cv2
import numpy as np
from insightface.app import FaceAnalysis

from blockchain import load_blockchain, verify_blockchain


REGISTERED_DATA = "output/face_embedding.json"
TEST_IMAGE = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "input/test_image_2.jpg"
)


def calculate_embedding_hash(embedding):
    """
    Generate SHA-256 hash of a face embedding.
    """

    embedding_string = json.dumps(
        embedding.tolist(),
        separators=(",", ":")
    )

    return hashlib.sha256(
        embedding_string.encode("utf-8")
    ).hexdigest()


def cosine_similarity(embedding1, embedding2):
    """
    Calculate cosine similarity between two face embeddings.
    """

    embedding1 = np.array(embedding1)
    embedding2 = np.array(embedding2)

    similarity = np.dot(embedding1, embedding2) / (
        np.linalg.norm(embedding1) *
        np.linalg.norm(embedding2)
    )

    return float(similarity)


def load_face_model():

    print("\n[1] Loading face recognition model...")

    app = FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"]
    )

    app.prepare(
        ctx_id=0,
        det_size=(640, 640)
    )

    return app


def main():

    print("=" * 60)
    print("          FACE ID - VERIFICATION")
    print("=" * 60)

    # --------------------------------------------------
    # 1. Load registered face
    # --------------------------------------------------

    print("\n[2] Loading registered face...")

    try:

        with open(
            REGISTERED_DATA,
            "r",
            encoding="utf-8"
        ) as file:

            registered_data = json.load(file)

    except FileNotFoundError:

        print("ERROR: Registered face data not found.")
        print("Run register_face.py first.")
        return

    registered_embedding = np.array(
        registered_data["embedding"],
        dtype=np.float32
    )

    print(
        "      Registered embedding:",
        registered_data["embedding_dimensions"],
        "dimensions"
    )

    # --------------------------------------------------
    # 2. Load model
    # --------------------------------------------------

    app = load_face_model()

    # --------------------------------------------------
    # 3. Load verification image
    # --------------------------------------------------

    print("\n[3] Loading verification image...")

    image = cv2.imread(TEST_IMAGE)

    if image is None:
       print("ERROR: Could not load verification image.")
       print("Check that this file exists:")
       print("     ", TEST_IMAGE)
       return

    print("      Image:", TEST_IMAGE)
    print("      Image loaded successfully.")

    # --------------------------------------------------
    # 4. Detect face
    # --------------------------------------------------

    print("\n[4] Detecting face...")

    faces = app.get(image)

    print("      Faces detected:", len(faces))

    if len(faces) == 0:

        print("\n❌ VERIFICATION FAILED")
        print("      No face detected.")

        return

    if len(faces) > 1:

        print("\n❌ VERIFICATION FAILED")
        print("      Multiple faces detected.")

        return

    face = faces[0]

    print(
        "      Detection confidence:",
        round(float(face.det_score), 4)
    )

    # --------------------------------------------------
    # 5. Generate new embedding
    # --------------------------------------------------

    print("\n[5] Generating face embedding...")

    new_embedding = face.embedding

    print(
        "      Embedding dimensions:",
        len(new_embedding)
    )

    # --------------------------------------------------
    # 6. Calculate similarity
    # --------------------------------------------------

    print("\n[6] Comparing faces...")

    similarity = cosine_similarity(
        registered_embedding,
        new_embedding
    )

    print(
        "      Cosine similarity:",
        round(similarity, 4)
    )

    # --------------------------------------------------
    # 7. Calculate image hash
    # --------------------------------------------------

    print("\n[7] Calculating verification embedding hash...")

    new_embedding_hash = calculate_embedding_hash(
        new_embedding
    )

    print(
        "      Verification embedding hash:"
    )

    print(
        "     ",
        new_embedding_hash
    )

    # --------------------------------------------------
    # 8. Verify blockchain
    # --------------------------------------------------

    print("\n[8] Checking blockchain integrity...")

    blockchain_valid = verify_blockchain()

    if blockchain_valid:

        print("      Blockchain integrity: VALID")

    else:

        print("      Blockchain integrity: INVALID")

        print("\n❌ VERIFICATION FAILED")
        print("      Blockchain has been modified.")

        return

    # --------------------------------------------------
    # 9. Get registered block
    # --------------------------------------------------

    blockchain = load_blockchain()

    registration_block = None

    for block in blockchain:

        if block["type"] == "FACE_REGISTRATION":

            registration_block = block
            break

    if registration_block is None:

        print("\n❌ VERIFICATION FAILED")
        print("      No face registration found.")

        return

    registered_embedding_hash = registration_block[
        "data"
    ]["embedding_sha256"]

    # --------------------------------------------------
    # 10. Compare identity
    # --------------------------------------------------

    # Threshold for this demo.
    # We will tune this after seeing your real result.

    THRESHOLD = 0.40

    face_match = similarity >= THRESHOLD

    # --------------------------------------------------
    # 11. Final result
    # --------------------------------------------------

    print("\n" + "=" * 60)

    if face_match:

        print("             ✅ FACE VERIFIED")
        print("=" * 60)

        print("\nIdentity match: YES")
        print(
            "Similarity:",
            round(similarity, 4)
        )
        print(
            "Threshold:",
            THRESHOLD
        )
        print("Blockchain: VALID")
        print("Registration: FOUND")

    else:

        print("             ❌ FACE VERIFICATION FAILED")
        print("=" * 60)

        print("\nIdentity match: NO")
        print(
            "Similarity:",
            round(similarity, 4)
        )
        print(
            "Threshold:",
            THRESHOLD
        )
        print("Blockchain: VALID")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()