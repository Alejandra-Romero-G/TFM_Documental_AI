from src.embeddings.text_model import generate_embedding
from src.vector_db.chroma_db import search_documents


def retrieve_context(query, n_results=5):

    # Convertir la pregunta en embedding
    query_embedding = generate_embedding(query)

    # Buscar información relacionada
    results = search_documents(
        query_embedding,
        n_results=n_results
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    context = []

    for document, metadata in zip(documents, metadatas):

        context.append(
            {
                "text": document,
                "file_name": metadata["file_name"],
                "chunk": metadata["chunk"]
            }
        )

    return context