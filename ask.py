from src.retrieval.rag import retrieve_context
from src.llm.llm import generate_response


question = input("Pregunta: ").strip()

if not question:
    print("Debes introducir una pregunta.")
    raise SystemExit


results = retrieve_context(
    question,
    n_results=5
)

if not results:
    print("No se encontraron documentos relevantes.")
    raise SystemExit


answer = generate_response(
    question,
    results
)


print()
print("=" * 70)
print("RESPUESTA")
print("=" * 70)
print(answer)


print()
print("=" * 70)
print("FUENTES")
print("=" * 70)

for position, result in enumerate(results, start=1):
    print(
        f"{position}. {result.get('file_name', 'desconocido')} "
        f"(chunk {result.get('chunk', 'desconocido')})"
    )