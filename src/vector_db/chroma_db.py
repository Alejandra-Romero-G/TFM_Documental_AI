import chromadb


# ============================================================
# CONFIGURACIÓN
# ============================================================

CHROMA_PATH = "data/chroma"
COLLECTION_NAME = "documents_bge_base_v1_5"
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
EMBEDDING_DIMENSION = 768


client = chromadb.PersistentClient(
    path=CHROMA_PATH
)


collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={
        "hnsw:space": "cosine",
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dimension": EMBEDDING_DIMENSION
    }
)


# ============================================================
# UTILIDADES
# ============================================================

def _embedding_to_list(embedding):
    """
    Convierte un embedding NumPy o una lista de Python
    al formato esperado por ChromaDB.
    """

    if hasattr(embedding, "tolist"):
        return embedding.tolist()

    return embedding


def _prepare_metadata(metadata):
    """
    Añade la información del modelo y elimina valores None.
    """

    complete_metadata = {
        **metadata,
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dimension": EMBEDDING_DIMENSION
    }

    return {
        key: value
        for key, value in complete_metadata.items()
        if value is not None
    }


# ============================================================
# INSERCIÓN INDIVIDUAL
# ============================================================

def add_document(
    document_id,
    text,
    embedding,
    metadata
):
    """
    Guarda o actualiza un único chunk en ChromaDB.
    """

    add_documents(
        document_ids=[document_id],
        texts=[text],
        embeddings=[embedding],
        metadatas=[metadata]
    )


# ============================================================
# INSERCIÓN POR LOTES
# ============================================================

def add_documents(
    document_ids,
    texts,
    embeddings,
    metadatas
):
    """
    Guarda o actualiza varios chunks en una sola operación.
    """

    lengths = {
        len(document_ids),
        len(texts),
        len(embeddings),
        len(metadatas)
    }

    if len(lengths) != 1:
        raise ValueError(
            "IDs, textos, embeddings y metadatos deben "
            "tener la misma longitud."
        )

    if not document_ids:
        return

    prepared_embeddings = [
        _embedding_to_list(embedding)
        for embedding in embeddings
    ]

    prepared_metadatas = [
        _prepare_metadata(metadata)
        for metadata in metadatas
    ]

    collection.upsert(
        ids=[str(document_id) for document_id in document_ids],
        documents=texts,
        embeddings=prepared_embeddings,
        metadatas=prepared_metadatas
    )


# ============================================================
# BÚSQUEDA SEMÁNTICA
# ============================================================

def search_documents(
    query_embedding,
    n_results=5,
    where=None
):
    """
    Busca los chunks más similares.

    El parámetro where permite limitar la búsqueda a uno
    o varios documentos.
    """

    query_embedding = _embedding_to_list(query_embedding)

    collection_count = collection.count()

    if collection_count == 0:
        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }

    query_parameters = {
        "query_embeddings": [query_embedding],
        "n_results": min(n_results, collection_count),
        "include": [
            "documents",
            "metadatas",
            "distances"
        ]
    }

    if where:
        query_parameters["where"] = where

    return collection.query(**query_parameters)


# ============================================================
# REANUDACIÓN
# ============================================================

def get_existing_ids():
    """
    Devuelve los IDs de los chunks que ya están indexados.

    Permite continuar una indexación interrumpida sin volver
    a generar los chunks almacenados.
    """

    results = collection.get(
        include=["metadatas"]
    )

    return set(results.get("ids") or [])


# ============================================================
# INFORMACIÓN DE LA COLECCIÓN
# ============================================================

def count_documents():
    """
    Devuelve el número de chunks almacenados.
    """

    return collection.count()


def get_collection_info():
    """
    Devuelve la configuración y tamaño de la colección.
    """

    return {
        "name": collection.name,
        "count": collection.count(),
        "metadata": collection.metadata
    }
# ============================================================
# ELIMINACIÓN POR DOCUMENTO
# ============================================================

def delete_document_chunks(document_id):
    """
    Elimina de ChromaDB todos los chunks de un documento.

    Se utiliza para revertir una indexación incompleta.
    Devuelve el número aproximado de chunks eliminados.
    """

    document_id = str(document_id).strip()

    if not document_id:
        raise ValueError(
            "El ID documental no puede estar vacío."
        )

    count_before = collection.count()

    collection.delete(
        where={
            "document_id": document_id
        }
    )

    count_after = collection.count()

    return max(
        0,
        count_before - count_after
    )