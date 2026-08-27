from src.loaders.loader_documents import load_documents

from src.similarity.document_similarity import (
    generate_document_embeddings,
    find_similar_documents
)


# ============================================================
# CARGAR DOCUMENTOS
# ============================================================

DATASET_PATH = "data/documents/osha"

print("=" * 70)
print("CARGANDO DOCUMENTOS")
print("=" * 70)

documents = load_documents(DATASET_PATH)

print(f"\nDocumentos encontrados: {len(documents)}")


# ============================================================
# GENERAR EMBEDDINGS
# ============================================================

embeddings = generate_document_embeddings(documents)

print("\nEmbeddings generados.")
print("Dimensión:", embeddings.shape)


# ============================================================
# DOCUMENTO DE PRUEBA
# ============================================================

target_index = next(
    i for i, document in enumerate(documents)
    if document["file_name"] == "000000105_active_shooter_booklet.pdf"
)

target_document = documents[target_index]

print("\n" + "=" * 70)
print("DOCUMENTO DE PRUEBA")
print("=" * 70)

print(target_document["file_name"])


# ============================================================
# BUSCAR DOCUMENTOS SIMILARES
# ============================================================

results = find_similar_documents(
    documents,
    embeddings,
    target_index,
    top_k=5
)


# ============================================================
# MOSTRAR RESULTADOS
# ============================================================

print("\n" + "=" * 70)
print("DOCUMENTOS SIMILARES")
print("=" * 70)

for rank, result in enumerate(results, start=1):

    print(
        f"{rank}. "
        f"{result['file_name']} "
        f"| similitud: "
        f"{result['similarity'] * 100:.2f}%"
    )