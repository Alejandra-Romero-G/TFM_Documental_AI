from pathlib import Path

from src.loaders.loader_documents import load_documents
from src.preprocessing.text_splitter import split_text
from src.embeddings.text_model import generate_embedding
from src.vector_db.chroma_db import add_document


BASE_DIR = Path(__file__).resolve().parent

documents_path = BASE_DIR / "data" / "documents"

documents = load_documents(documents_path)

print(f"Documentos encontrados: {len(documents)}")

total_chunks = 0
processed_documents = 0


for document in documents:

    print("=" * 60)
    print("Procesando:", document["file_name"])

    text = document["text"]

    if not text or not text.strip():
        print("⚠️ Documento sin texto. Se omite.")
        continue

    chunks = split_text(text)

    print("Chunks:", len(chunks))

    for i, chunk in enumerate(chunks):

        embedding = generate_embedding(chunk)

        chunk_id = f"{document['file_name']}_chunk_{i}"

        add_document(
            document_id=chunk_id,
            text=chunk,
            embedding=embedding,
            metadata={
                "file_name": document["file_name"],
                "chunk": i,
                "type": document["type"],
                "path": document["path"]
            }
        )

        total_chunks += 1

    processed_documents += 1


print()
print("=" * 60)
print("INDEXACIÓN COMPLETADA")
print("=" * 60)

print("Documentos procesados:", processed_documents)
print("Chunks almacenados:", total_chunks)