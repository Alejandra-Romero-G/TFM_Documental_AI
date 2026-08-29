from src.embeddings.text_model import (
    generate_query_embedding
)
from src.vector_db.chroma_db import search_documents


def _normalize_document_ids(document_ids):
    """
    Limpia y elimina IDs documentales repetidos.
    """

    if document_ids is None:
        return []

    if isinstance(document_ids, str):
        document_ids = [document_ids]

    normalized_ids = []

    for document_id in document_ids:

        document_id = str(document_id).strip()

        if (
            document_id
            and document_id not in normalized_ids
        ):
            normalized_ids.append(document_id)

    return normalized_ids


def _build_document_filter(document_ids):
    """
    Construye el filtro de metadatos utilizado por ChromaDB.
    """

    document_ids = _normalize_document_ids(
        document_ids
    )

    if not document_ids:
        return None

    if len(document_ids) == 1:
        return {
            "document_id": document_ids[0]
        }

    return {
        "document_id": {
            "$in": document_ids
        }
    }


def retrieve_context(
    query,
    n_results=10,
    max_chunks_per_document=2,
    document_ids=None
):
    """
    Recupera los chunks más relevantes para una consulta.

    Parameters
    ----------
    query:
        Consulta del usuario.
    n_results:
        Número máximo de chunks devueltos.
    max_chunks_per_document:
        Número máximo de chunks procedentes del mismo PDF.
    document_ids:
        Lista opcional de documentos en los que buscar.
        Si es None o está vacía, se consulta todo el corpus.
    """

    if not query or not query.strip():
        return []

    if n_results <= 0:
        raise ValueError(
            "n_results debe ser mayor que cero."
        )

    if max_chunks_per_document <= 0:
        raise ValueError(
            "max_chunks_per_document debe ser mayor que cero."
        )

    normalized_document_ids = (
        _normalize_document_ids(document_ids)
    )

    where_filter = _build_document_filter(
        normalized_document_ids
    )

    query_embedding = generate_query_embedding(
        query.strip()
    )

    # Se recuperan más candidatos para poder limitar
    # posteriormente los chunks por documento.
    candidate_count = max(
        n_results * 5,
        n_results
    )

    results = search_documents(
        query_embedding=query_embedding,
        n_results=candidate_count,
        where=where_filter
    )

    result_ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        return []

    context = []
    document_counts = {}
    used_chunk_ids = set()

    for result_id, document, metadata, distance in zip(
        result_ids,
        documents,
        metadatas,
        distances
    ):
        metadata = metadata or {}

        document_id = metadata.get(
            "document_id",
            ""
        )

        file_name = metadata.get(
            "file_name",
            "documento_desconocido"
        )

        document_key = (
            document_id
            or metadata.get(
                "canonical_document_id",
                file_name
            )
        )

        chunk_id = metadata.get(
            "chunk_id",
            result_id
        )

        if chunk_id in used_chunk_ids:
            continue

        current_count = document_counts.get(
            document_key,
            0
        )

        if (
            current_count
            >= max_chunks_per_document
        ):
            continue

        used_chunk_ids.add(chunk_id)

        document_counts[document_key] = (
            current_count + 1
        )

        numeric_distance = (
            float(distance)
            if distance is not None
            else None
        )

        context.append(
            {
                "text": document,
                "file_name": file_name,
                "document_id": document_id,
                "canonical_document_id": (
                    metadata.get(
                        "canonical_document_id",
                        document_id
                    )
                ),
                "chunk": metadata.get(
                    "chunk_index",
                    ""
                ),
                "chunk_index": metadata.get(
                    "chunk_index",
                    ""
                ),
                "chunk_id": chunk_id,
                "page_number": metadata.get(
                    "page_number",
                    ""
                ),
                "relative_path": metadata.get(
                    "relative_path",
                    ""
                ),
                "source_collection": metadata.get(
                    "source_collection",
                    ""
                ),
                "document_type": metadata.get(
                    "document_type",
                    "pdf"
                ),
                # Se mantiene source por compatibilidad.
                "source": metadata.get(
                    "relative_path",
                    file_name
                ),
                "distance": numeric_distance,
                "similarity": (
                    1.0 - numeric_distance
                    if numeric_distance is not None
                    else None
                )
            }
        )

        if len(context) >= n_results:
            break

    return context