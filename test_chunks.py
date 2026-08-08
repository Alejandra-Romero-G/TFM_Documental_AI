from pathlib import Path

from src.loaders.loader_documents import load_documents
from src.preprocessing.text_splitter import split_text


BASE_DIR = Path(__file__).resolve().parent

documents_path = BASE_DIR / "data" / "documents"

documents = load_documents(documents_path)

print(f"Documentos encontrados: {len(documents)}")

if documents:

    document = documents[0]

    print("=" * 60)
    print("Documento:", document["file_name"])
    print("Caracteres:", len(document["text"]))

    chunks = split_text(document["text"])

    print("Chunks generados:", len(chunks))

    for i, chunk in enumerate(chunks[:5]):

        print("=" * 60)
        print(f"CHUNK {i + 1}")
        print(chunk[:500])