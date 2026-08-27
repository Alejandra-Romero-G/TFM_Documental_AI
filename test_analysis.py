from src.analysis.analyzer import analyze_documents


question = """
Analyze the main recommendations related to
hurricane preparedness contained in the documents.

Provide:
1. A brief summary.
2. The main topics.
3. The most important recommendations.
4. A short conclusion.
"""


result = analyze_documents(
    question,
    n_results=10
)


print("=" * 70)
print("ANÁLISIS DOCUMENTAL")
print("=" * 70)

print(result["response"])


print()
print("=" * 70)
print("FUENTES UTILIZADAS")
print("=" * 70)

for source in result["sources"]:

    print(
        f"- {source['file_name']} "
        f"(chunk {source['chunk']})"
    )