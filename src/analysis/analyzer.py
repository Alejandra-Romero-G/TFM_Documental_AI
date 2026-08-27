from src.retrieval.rag import retrieve_context
from src.llm.llm import generate_response


def analyze_documents(question, n_results=10):
    """
    Analiza los documentos recuperando los fragmentos
    más relevantes y utilizando el LLM para generar
    un análisis.
    """

    # Recuperar información relevante
    context = retrieve_context(
        question,
        n_results=n_results
    )

    # Generar análisis con el LLM
    response = generate_response(
        question,
        context
    )

    return {
        "question": question,
        "response": response,
        "sources": context
    }