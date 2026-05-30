import os
import hashlib
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

# Folder containing .txt files
FOLDER = "DiscursosOriginales"

# Mongo replica set connection
MONGO_URI = (
    "mongodb://localhost:27017,"
    "localhost:27018,"
    "localhost:27019/"
    "?replicaSet=rs0"
)

# Connect to MongoDB
client = MongoClient(MONGO_URI)

db = client["Política"]
collection = db["Discursos"]

print("Connected to MongoDB replica set")

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Process each .txt file
for filename in os.listdir(FOLDER):

    if not filename.endswith(".txt"):
        continue

    path = os.path.join(FOLDER, filename)

    with open(path, "r", encoding="utf-8") as f:
        texto = f.read().strip()

    # SHA-256 hash
    sha256 = hashlib.sha256(
        texto.encode("utf-8")
    ).hexdigest()

    # Generate embedding
    embedding = model.encode(texto).tolist()

    # Mongo document
    documento = {
        "_id": sha256,
        "texto": texto,
        "embedding": embedding
    }

    try:
        collection.insert_one(documento)
        print(f"Inserted: {filename}")

    except Exception as e:
        print(f"Skipped {filename}: {e}")

print("\nFinished loading documents")