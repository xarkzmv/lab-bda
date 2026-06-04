import numpy as np
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# 1. Configuración de conexión 
# Usa la URI con la que lograste insertar los datos en el paso anterior.
# Si modificaste el archivo hosts de Windows, puedes usar la URI del Replica Set original.
# Si usaste la conexión directa, mantén esta:
MONGO_URI = "mongodb://localhost:27017/?directConnection=true"

client = MongoClient(MONGO_URI)
db = client["Política"]
collection = db["Discursos"]

# 2. Cargar el modelo de lenguaje (debe ser el mismo que usaste para poblar)
print("Cargando el modelo de lenguaje (esto puede tomar unos segundos)...")
model = SentenceTransformer("all-MiniLM-L6-v2")

def buscar_discursos_similares(consulta, top_k=5):
    print(f"\nProcesando consulta: '{consulta}'")
    
    # 3. Generar el vector (embedding) de la consulta
    # scikit-learn espera un arreglo 2D, por eso la consulta va entre corchetes
    query_embedding = model.encode([consulta])
    
    # 4. Obtener todos los documentos de la base de datos
    # Extraemos el _id, embedding y el texto completo
    documentos = list(collection.find({}, {
        "_id": 1, 
        "embedding": 1, 
        "texto": 1 
    }))
    
    if not documentos:
        print("No hay documentos en la base de datos. Ejecuta el script de poblamiento primero.")
        return

    # Extraemos solo los vectores de la BD para hacer el cálculo matemático
    embeddings_db = [doc["embedding"] for doc in documentos]
    
    # 5. Calcular la similitud coseno
    # Comparamos el vector de la consulta contra la matriz de todos los vectores de la BD
    # [0] extrae los puntajes de la primera (y única) fila de resultados
    similitudes = cosine_similarity(query_embedding, embeddings_db)[0]
    
    # 6. Asociar cada puntaje de similitud con su documento correspondiente
    resultados = []
    for i, doc in enumerate(documentos):
        resultados.append({
            "id": doc["_id"],
            "similitud": similitudes[i],
            "extracto": doc.get("texto", "")[:150] + "..."
        })
        
    # 7. Ordenar los resultados de mayor a menor similitud y tomar los 'top_k' (5)
    resultados_ordenados = sorted(resultados, key=lambda x: x["similitud"], reverse=True)[:top_k]
    
    # 8. Mostrar los resultados formateados en consola
    print("\n" + "="*50)
    print(" 🏆 TOP 5 DISCURSOS MÁS SIMILARES 🏆")
    print("="*50)
    for i, res in enumerate(resultados_ordenados, 1):
        # Convertimos el puntaje a porcentaje para que sea más fácil de leer
        porcentaje = res['similitud'] * 100
        print(f"\nTop {i} | Similitud: {porcentaje:.2f}%")
        print(f"ID (SHA-256): {res['id']}")
        print(f"Extracto: \"{res['extracto']}\"")
        print("-" * 50)

if __name__ == "__main__":
    print("\n--- Sistema RAG de Búsqueda de Discursos ---")
    while True:
        consulta_usuario = input("\nIngresa tu búsqueda (o escribe 'salir' para terminar): ")
        
        if consulta_usuario.lower() == 'salir':
            print("Saliendo del buscador...")
            break
            
        if consulta_usuario.strip() == "":
            print("Por favor, ingresa texto válido.")
            continue
            
        buscar_discursos_similares(consulta_usuario)