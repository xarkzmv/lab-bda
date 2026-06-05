import os
import hashlib
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

FOLDER = "DiscursosOriginales"
client = MongoClient(
   "mongodb://mongo1:30001,mongo2:30002,mongo3:30003/?"
   "replicaSet=my-replica-set"
   "&readPreference=primaryPreferred"
   "&ssl=false"
   "&serverSelectionTimeoutMS=5000"   
   "&connectTimeoutMS=2000"           
   "&socketTimeoutMS=2000"            
   "&retryWrites=true"                
   "&retryReads=true"                 
)
db = client.Politica
collection = db['Discursos']

print("Connected to MongoDB replica set")

model = SentenceTransformer("all-MiniLM-L6-v2")

for filename in os.listdir(FOLDER):

    if not filename.endswith(".txt"):
        continue

    path = os.path.join(FOLDER, filename)
    with open(path, "r", encoding="utf-8") as f:
        texto = f.read().strip()

    sha256 = hashlib.sha256(
        texto.encode("utf-8")
    ).hexdigest()

    embedding = model.encode(texto).tolist()

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

print("\nFiniquitados la inserciÃ³n de documentos")