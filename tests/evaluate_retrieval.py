import sys
from pathlib import Path

# Añadir la raíz del proyecto al PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sentence_transformers import SentenceTransformer
from src.vector_db.chroma_db import search_documents
from tests.evaluation_questions import QUESTIONS


MODEL_NAME = "BAAI/bge-base-en-v1.5"

print("=" * 80)
print("EVALUACIÓN DEL RETRIEVAL - PRECISION@5")
print("=" * 80)

print("\nCargando modelo BGE...")

model = SentenceTransformer(MODEL_NAME)

print("Modelo cargado.\n")


for question in QUESTIONS:

    query = question["question"]
    expected_keywords = question["expected_keywords"]

    print("-" * 80)
    print("PREGUNTA:")
    print(query)

    # Generar embedding de la pregunta
    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    # Recuperar 5 documentos
    results = search_documents(
        query_embedding,
        n_results=5
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    relevant = 0

    print("\nDOCUMENTOS RECUPERADOS:")

    for i in range(5):

        file_name = metadatas[i]["file_name"]
        text = documents[i].lower()

        # Comprobar si el documento contiene alguna palabra clave
        is_relevant = any(
            keyword.lower() in text
            for keyword in expected_keywords
        )

        if is_relevant:
            relevant += 1
            mark = "OK"
        else:
            mark = "NO"

        print(
            f"{i + 1}. [{mark}] "
            f"{file_name} | "
            f"distancia: {distances[i]:.4f}"
        )

    precision = relevant / 5

    print("\nRESULTADO:")
    print(f"Documentos relevantes: {relevant}/5")
    print(f"Precision@5: {precision:.2f}")


print("\n" + "=" * 80)
print("EVALUACIÓN FINALIZADA")
print("=" * 80)