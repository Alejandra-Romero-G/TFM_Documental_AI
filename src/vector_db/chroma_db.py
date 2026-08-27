import chromadb


# ============================================================
# CONFIGURACIÓN
# ============================================================

client = chromadb.PersistentClient(
    path="data/chroma"
)


collection = client.get_or_create_collection(
    name="documents_bge_chunks"
)
# ============================================================
# AÑADIR DOCUMENTO
# ============================================================

def add_document(
    document_id,
    text,
    embedding,
    metadata
):
    """
    Guarda un documento y su embedding en ChromaDB.
    """

    collection.upsert(
        ids=[document_id],
        documents=[text],
        embeddings=[embedding.tolist()],
        metadatas=[metadata]
    )


# ============================================================
# BUSCAR DOCUMENTOS SIMILARES
# ============================================================

def search_documents(
    query_embedding,
    n_results=5
):
    """
    Busca los documentos más similares.
    """

    results = collection.query(
        query_embeddings=[
            query_embedding.tolist()
        ],
        n_results=n_results
    )

    return results


# ============================================================
# INFORMACIÓN DE LA COLECCIÓN
# ============================================================

def count_documents():
    """
    Devuelve el número de documentos almacenados.
    """

    return collection.count()