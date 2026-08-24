from src.retrieval.rag import retrieve_context
from src.llm.llm import generate_response


question = input("Pregunta: ")


results = retrieve_context(
    question,
    n_results=5
)


context_parts = []

for result in results:

    context_parts.append(
        f"""
Document: {result['file_name']}
Chunk: {result['chunk']}

{result['text']}
"""
    )


context = "\n\n".join(context_parts)


answer = generate_response(
    question,
    context
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

for result in results:

    print(
        f"- {result['file_name']} "
        f"(chunk {result['chunk']})"
    )