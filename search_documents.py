from src.embeddings.text_model import generate_embedding
from src.vector_db.chroma_db import search_documents


query = input("Escribe tu pregunta: ")

query_embedding = generate_embedding(query)

results = search_documents(
    query_embedding,
    n_results=5
)

print()
print("=" * 70)
print("RESULTADOS")
print("=" * 70)

documents = results["documents"][0]
metadatas = results["metadatas"][0]
distances = results["distances"][0]

for i, (document, metadata, distance) in enumerate(
    zip(documents, metadatas, distances)
):

    print()
    print("=" * 70)
    print(f"RESULTADO {i + 1}")
    print("=" * 70)

    print("Documento:", metadata["file_name"])
    print("Chunk:", metadata["chunk"])
    print("Distancia:", distance)

    print()
    print(document[:1000])