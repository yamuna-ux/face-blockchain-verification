import cv2
import json
import os
import hashlib
from insightface.app import FaceAnalysis

IMAGE_PATH = "input/test_image.jpg"
OUTPUT_PATH = "output/face_embedding.json"


def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of the input image."""

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while chunk := file.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()


print("=" * 60)
print("          FACE ID - FACE ENCODING")
print("=" * 60)

# ---------------------------------------------------------
# 1. Load model
# ---------------------------------------------------------

print("\n[1] Loading face recognition model...")

app = FaceAnalysis(
    name="buffalo_l",
    providers=["CPUExecutionProvider"]
)

app.prepare(
    ctx_id=0,
    det_size=(640, 640)
)

print("    ✓ Model loaded")

# ---------------------------------------------------------
# 2. Load image
# ---------------------------------------------------------

print("\n[2] Loading input image...")

image = cv2.imread(IMAGE_PATH)

if image is None:
    raise FileNotFoundError(
        f"Could not find image: {IMAGE_PATH}"
    )

print("    ✓ Image loaded")

# ---------------------------------------------------------
# 3. Detect face
# ---------------------------------------------------------

print("\n[3] Detecting face...")

faces = app.get(image)

print(f"    ✓ Faces detected: {len(faces)}")

if len(faces) == 0:
    raise RuntimeError("No face detected in the image.")

if len(faces) > 1:
    print("    ⚠ Multiple faces detected.")
    print("    Using the first detected face.")

# ---------------------------------------------------------
# 4. Generate embedding
# ---------------------------------------------------------

print("\n[4] Generating face encoding...")

face = faces[0]

embedding = face.embedding.tolist()

print(f"    Detection confidence : {face.det_score:.4f}")
print(f"    Embedding dimensions : {len(embedding)}")
print("    ✓ Face encoding generated")

# ---------------------------------------------------------
# 5. Hash original image
# ---------------------------------------------------------

print("\n[5] Hashing input image...")

image_hash = calculate_file_hash(IMAGE_PATH)

print(f"    SHA-256: {image_hash}")

# ---------------------------------------------------------
# 6. Save result
# ---------------------------------------------------------

os.makedirs("output", exist_ok=True)

result = {
    "image": IMAGE_PATH,
    "image_sha256": image_hash,
    "faces_detected": len(faces),
    "detection_confidence": float(face.det_score),
    "embedding_dimensions": len(embedding),
    "embedding": embedding
}

with open(OUTPUT_PATH, "w") as file:
    json.dump(result, file, indent=4)

print("\n[6] Saving face encoding...")
print(f"    ✓ Saved to: {OUTPUT_PATH}")

print("\n" + "=" * 60)
print("       FACE ENCODING SUCCESS")
print("=" * 60)