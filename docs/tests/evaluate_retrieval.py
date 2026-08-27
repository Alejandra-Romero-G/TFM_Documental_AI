from sentence_transformers import SentenceTransformer
from src.vector_db.chroma_db import search_documents
from evaluation_questions import QUESTIONS


MODEL_NAME = "BAAI/bge-base-en-v1.5"

model = SentenceTransformer(MODEL_NAME)


print("=" * 80)
print("EVALUACIÓN DEL RETRIEVAL")
print("=" * 80)


for question in QUESTIONS:

    print("\n" + "-" * 80)
    print("PREGUNTA:")
    print(question)

    # Generar embedding de la pregunta
    query_embedding = model.encode(
        question,
        normalize_embeddings=True
    )

    # Buscar documentos
    results = search_documents(
        query_embedding,
        n_results=5
    )

    print("\nDOCUMENTOS RECUPERADOS:")

    for i in range(5):

        metadata = results["metadatas"][0][i]
        distance = results["distances"][0][i]

        print(
            f"{i + 1}. "
            f"{metadata['file_name']} "
            f"| distancia: {distance:.4f}"
        )