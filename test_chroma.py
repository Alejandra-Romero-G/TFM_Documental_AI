from pathlib import Path

from src.loaders.loader_documents import load_documents
from src.embeddings.text_model import generate_embedding
from src.vector_db.chroma_db import add_document


BASE_DIR = Path(__file__).resolve().parent

documents_path = BASE_DIR / "data" / "documents"

documents = load_documents(documents_path)

print(f"Documentos encontrados: {len(documents)}")


# Probamos solamente el primer documento

document = documents[0]

text = document["text"]

embedding = generate_embedding(text)


add_document(
    document_id=document["file_name"],
    text=text,
    embedding=embedding,
    metadata={
        "file_name": document["file_name"],
        "type": document["type"],
        "path": document["path"]
    }
)

print()
print("Documento almacenado correctamente:")
print(document["file_name"])