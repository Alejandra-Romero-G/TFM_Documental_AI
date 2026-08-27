from src.loaders.loader_documents import load_documents
from src.loaders.chunker import split_text
from src.embeddings.bge_embeddings import model
from src.vector_db.chroma_db import (
    add_document,
    count_documents
)


DATASET_PATH = "data/documents/osha"


print("=" * 70)
print("INDEXANDO DOCUMENTOS CON CHUNKING")
print("=" * 70)


# ============================================================
# CARGAR DOCUMENTOS
# ============================================================

documents = load_documents(DATASET_PATH)

print(f"\nDocumentos encontrados: {len(documents)}")


# ============================================================
# CREAR CHUNKS
# ============================================================

print("\nDividiendo documentos en chunks...")


chunks = []

for document in documents:

    document_chunks = split_text(
        document["text"],
        chunk_size=800,
        chunk_overlap=150
    )

    for chunk_number, chunk_text in enumerate(document_chunks):

        chunks.append(
            {
                "text": chunk_text,
                "file_name": document["file_name"],
                "path": document["path"],
                "type": document["type"],
                "chunk": chunk_number
            }
        )


print(f"Chunks generados: {len(chunks)}")


# ============================================================
# EXTRAER TEXTOS
# ============================================================

texts = [
    chunk["text"]
    for chunk in chunks
]


# ============================================================
# GENERAR EMBEDDINGS
# ============================================================

print("\nGenerando embeddings con BGE-base-en-v1.5...")

embeddings = model.encode(
    texts,
    show_progress_bar=True,
    normalize_embeddings=True
)


print(
    f"\nEmbeddings generados: {embeddings.shape}"
)


# ============================================================
# GUARDAR EN CHROMADB
# ============================================================

print("\nGuardando chunks en ChromaDB...")


for i, chunk in enumerate(chunks):

    document_id = f"chunk_{i}"

    metadata = {
        "file_name": chunk["file_name"],
        "path": chunk["path"],
        "type": chunk["type"],
        "chunk": chunk["chunk"]
    }

    add_document(
        document_id=document_id,
        text=chunk["text"],
        embedding=embeddings[i],
        metadata=metadata
    )


print("\n" + "=" * 70)
print("INDEXACIÓN FINALIZADA")
print("=" * 70)

print(
    f"Chunks almacenados en ChromaDB: "
    f"{count_documents()}"
)