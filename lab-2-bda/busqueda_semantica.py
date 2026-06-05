import numpy as np
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

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

print("Conectado a la BD")
model = SentenceTransformer("all-MiniLM-L6-v2")

def buscar_discursos(consulta_textual, top_n=5):
    documentos = list(collection.find({}, {"_id": 1, "texto": 1, "embedding": 1}))
    if not documentos:
        print("La colección 'Discursos' está vacía. Ejecuta primero el script de inserción.")
        return
    embeddings_bd = np.array([doc["embedding"] for doc in documentos])
    embedding_consulta = model.encode(consulta_textual).reshape(1, -1)
    similitudes = cosine_similarity(embedding_consulta, embeddings_bd)[0]
    
    for idx, doc in enumerate(documentos):
        doc["score"] = float(similitudes[idx])
    
    resultados = sorted(documentos, key=lambda x: x["score"], reverse=True)[:top_n]
    print(f"Resultado de: '{consulta_textual}'")
    for i, doc in enumerate(resultados, 1):
        print(f"\nTop {i} Id: {doc['_id']}")
        print(f"Puntaje de similitud coseno: {doc['score']:.4f}")
        extracto = doc['texto'][:250].replace('\n', ' ')
        print(f"Parte del discurso: {extracto}")

if __name__ == "__main__":
    consulta = "Discursos sobre ex Presidentes Frei, Lagos y Bachelet"
    buscar_discursos(consulta, top_n=5)