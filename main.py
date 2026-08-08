from src.loaders.loader_documents import load_documents

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

documents_path = BASE_DIR / "data" / "documents"

print("Ruta de documentos:", documents_path)

documents = load_documents(documents_path)

print(f"Documentos encontrados: {len(documents)}")

for document in documents:
    print("=" * 50)
    print(document["file_name"])
    print(document["text"][:300])
