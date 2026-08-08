from src.retrieval.rag import retrieve_context


query = input("Pregunta: ")

results = retrieve_context(
    query,
    n_results=5
)


print()
print("=" * 70)
print("CONTEXTO PARA EL LLM")
print("=" * 70)


for i, result in enumerate(results):

    print()
    print(f"--- RESULTADO {i + 1} ---")

    print("Documento:", result["file_name"])
    print("Chunk:", result["chunk"])

    print()
    print(result["text"])