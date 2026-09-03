import time
import numpy as np
from sentence_transformers import SentenceTransformer

from src.loaders.loader_documents import load_documents


# ============================================================
# CONFIGURACIÓN
# ============================================================

DATASET_PATH = "data/documents/osha"

MODELS = {
    "all-MiniLM-L6-v2": "sentence-transformers/all-MiniLM-L6-v2",
    "BGE-base-en-v1.5": "BAAI/bge-base-en-v1.5",
}

QUERIES = [
    "What should an employer do to protect workers from heat stress?",
    "What should employers do during a hurricane?",
    "How can employers protect temporary workers?",
    "What measures can prevent workplace injuries?",
    "What are the responsibilities of employers regarding workplace safety?",
]


# ============================================================
# CARGAR DOCUMENTOS
# ============================================================

print("=" * 70)
print("CARGANDO DOCUMENTOS")
print("=" * 70)

documents = load_documents(DATASET_PATH)

print(f"\nDocumentos encontrados: {len(documents)}")


# ============================================================
# PREPARAR TEXTOS
# ============================================================

texts = [doc["text"] for doc in documents]
file_names = [doc["file_name"] for doc in documents]


# ============================================================
# COMPARACIÓN
# ============================================================

all_results = {}


for model_name, model_id in MODELS.items():

    print("\n" + "=" * 70)
    print(f"MODELO: {model_name}")
    print(f"ID: {model_id}")
    print("=" * 70)

    start_load = time.time()

    model = SentenceTransformer(model_id)

    load_time = time.time() - start_load

    print(f"\nTiempo de carga: {load_time:.2f} segundos")

    # --------------------------------------------------------
    # Generación de embeddings
    # --------------------------------------------------------

    start_embedding = time.time()

    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    embedding_time = time.time() - start_embedding

    dimension = embeddings.shape[1]

    print(f"\nDimensión de embedding: {dimension}")
    print(f"Tiempo generación embeddings: {embedding_time:.2f} segundos")

    # --------------------------------------------------------
    # Consultas
    # --------------------------------------------------------

    model_results = []

    for query in QUERIES:

        print("\n" + "-" * 70)
        print("CONSULTA:")
        print(query)

        query_embedding = model.encode(
            query,
            normalize_embeddings=True
        )

        # Similitud coseno porque los embeddings están normalizados
        similarities = np.dot(
            embeddings,
            query_embedding
        )

        # Obtener los 5 documentos más similares
        top_indices = np.argsort(similarities)[::-1][:5]

        results = []

        print("\nTop 5 resultados:")

        for rank, index in enumerate(top_indices, start=1):

            similarity = float(similarities[index])

            result = {
                "rank": rank,
                "file_name": file_names[index],
                "similarity": similarity
            }

            results.append(result)

            print(
                f"{rank}. "
                f"{file_names[index]} "
                f"| similitud: {similarity:.4f}"
            )

        model_results.append({
            "query": query,
            "results": results
        })

    all_results[model_name] = {
        "dimension": dimension,
        "load_time": load_time,
        "embedding_time": embedding_time,
        "queries": model_results
    }


# ============================================================
# RESUMEN FINAL
# ============================================================

print("\n\n")
print("=" * 70)
print("RESUMEN DE LA COMPARACIÓN")
print("=" * 70)

for model_name, data in all_results.items():

    print(f"\nModelo: {model_name}")
    print(f"Dimensión: {data['dimension']}")
    print(f"Tiempo carga: {data['load_time']:.2f} s")
    print(f"Tiempo embeddings: {data['embedding_time']:.2f} s")

print("\n" + "=" * 70)
print("COMPARACIÓN FINALIZADA")
print("=" * 70)