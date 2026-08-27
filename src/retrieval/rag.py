from src.embeddings.text_model import generate_embedding
from src.vector_db.chroma_db import search_documents


def retrieve_context(
    query,
    n_results=10,
    max_chunks_per_document=2
):
    """
    Recupera los chunks más relevantes para una consulta.

    Se limita el número de chunks procedentes del mismo documento
    para evitar que un único PDF domine el contexto.
    """

    # ============================================================
    # GENERAR EMBEDDING DE LA CONSULTA
    # ============================================================

    query_embedding = generate_embedding(query)

    # ============================================================
    # BUSCAR EN CHROMADB
    # ============================================================

    results = search_documents(
        query_embedding,
        n_results=n_results * 3
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    # ============================================================
    # FILTRAR RESULTADOS
    # ============================================================

    context = []

    document_counts = {}

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):

        file_name = metadata["file_name"]

        # Número de chunks utilizados de este documento
        count = document_counts.get(file_name, 0)

        if count >= max_chunks_per_document:
            continue

        document_counts[file_name] = count + 1

        context.append(
            {
                "text": document,
                "file_name": file_name,
                "chunk": metadata.get("chunk", ""),
                "distance": float(distance)
            }
        )

        if len(context) >= n_results:
            break

    return context