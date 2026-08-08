from pathlib import Path

from src.loaders.loader_documents import load_documents
from src.embeddings.text_model import generate_embedding


BASE_DIR = Path(__file__).resolve().parent

documents_path = BASE_DIR / "data" / "documents"

documents = load_documents(documents_path)

print(f"Documentos encontrados: {len(documents)}")


if documents:

    document = documents[0]

    print("=" * 60)
    print("Documento:", document["file_name"])

    text = document["text"]

    print("Caracteres:", len(text))

    embedding = generate_embedding(text)

    print("Tipo:", type(embedding))
    print("Dimensión:", len(embedding))
    print("Primeros valores:", embedding[:5])