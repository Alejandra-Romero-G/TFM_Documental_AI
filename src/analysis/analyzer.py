from math import ceil

from src.retrieval.rag import retrieve_context
from src.llm.llm import generate_response


def analyze_documents(
    question,
    n_results=10,
    max_chunks_per_document=None,
    document_ids=None
):
    """
    Analiza el corpus completo o una seleccion de documentos.
    """

    if not question or not question.strip():
        raise ValueError("La pregunta no puede estar vacia.")

    question = question.strip()

    if document_ids is not None:
        document_ids = [
            str(document_id).strip()
            for document_id in document_ids
            if str(document_id).strip()
        ]

        if not document_ids:
            document_ids = None

    if max_chunks_per_document is None:
        if document_ids:
            max_chunks_per_document = max(
                1,
                ceil(n_results / len(document_ids))
            )
        else:
            max_chunks_per_document = 2

    context = retrieve_context(
        query=question,
        n_results=n_results,
        max_chunks_per_document=max_chunks_per_document,
        document_ids=document_ids
    )

    if not context:
        return {
            "question": question,
            "response": (
                "No se encontro informacion relevante "
                "en los documentos seleccionados."
            ),
            "sources": [],
            "document_ids": document_ids or []
        }

    response = generate_response(
        question,
        context
    )

    return {
        "question": question,
        "response": response,
        "sources": context,
        "document_ids": document_ids or []
    }