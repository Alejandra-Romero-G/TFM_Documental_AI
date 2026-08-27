import numpy as np

from src.embeddings.bge_embeddings import model


def calculate_similarity(embedding_a, embedding_b):
    """
    Calcula la similitud coseno entre dos embeddings normalizados.
    """

    return float(np.dot(embedding_a, embedding_b))


def generate_document_embeddings(documents):
    """
    Genera los embeddings de todos los documentos.
    """

    texts = [
        document["text"]
        for document in documents
    ]

    print("\nGenerando embeddings de documentos...")

    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    return embeddings


def find_similar_documents(
    documents,
    embeddings,
    target_index,
    top_k=5
):
    """
    Busca los documentos más similares a un documento.
    """

    target_document = documents[target_index]

    target_embedding = embeddings[target_index]

    similarities = []

    for index, document in enumerate(documents):

        # No comparar el documento consigo mismo
        if index == target_index:
            continue

        similarity = calculate_similarity(
            target_embedding,
            embeddings[index]
        )

        similarities.append(
            {
                "file_name": document["file_name"],
                "path": document["path"],
                "similarity": similarity
            }
        )

    similarities.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return similarities[:top_k]