from src.analysis.analyzer import analyze_documents


questions = [
    "What should an employer do to protect workers from heat stress?",
    "What should employers do during a hurricane?",
    "How can employers protect temporary workers?",
    "What are the responsibilities of employers regarding workplace safety?"
]


for question in questions:

    print("\n" + "=" * 80)
    print("PREGUNTA")
    print("=" * 80)

    print(question)

    result = analyze_documents(
        question,
        n_results=5
    )

    print("\n" + "-" * 80)
    print("RESPUESTA")
    print("-" * 80)

    print(result["response"])

    print("\n" + "-" * 80)
    print("FUENTES")
    print("-" * 80)

    for i, source in enumerate(result["sources"], start=1):
        print(
            f"{i}. {source['file_name']}"
        )