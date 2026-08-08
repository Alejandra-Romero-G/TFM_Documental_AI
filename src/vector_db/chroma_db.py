import chromadb


# Base de datos persistente
client = chromadb.PersistentClient(
    path="data/chroma"
)


# Colección donde guardaremos los chunks
collection = client.get_or_create_collection(
    name="documents"
)


def add_document(document_id, text, embedding, metadata):
    """
    Guarda un chunk y su embedding en ChromaDB.
    """

    collection.add(
        ids=[document_id],
        documents=[text],
        embeddings=[embedding.tolist()],
        metadatas=[metadata]
    )


def search_documents(query_embedding, n_results=5):
    """
    Busca los chunks más similares a una consulta.
    """

    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=n_results
    )

    return results