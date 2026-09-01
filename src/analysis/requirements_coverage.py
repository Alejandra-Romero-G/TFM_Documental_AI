import numpy as np

from src.embeddings.text_model import (
    generate_document_embeddings
)
from src.retrieval.rag import retrieve_context


DEFAULT_FOCUS = (
    "requirements, obligations, responsibilities, "
    "controls, preventive measures and recommendations"
)


def _normalize_document_id(
    document_id,
    argument_name
):
    """
    Valida un ID documental.
    """

    if document_id is None:
        raise ValueError(
            f"{argument_name} no puede ser None."
        )

    normalized_id = str(
        document_id
    ).strip()

    if not normalized_id:
        raise ValueError(
            f"{argument_name} no puede estar vacio."
        )

    return normalized_id


def _validate_thresholds(
    match_threshold,
    review_threshold
):
    """
    Valida los umbrales de clasificacion.
    """

    for name, value in (
        ("match_threshold", match_threshold),
        ("review_threshold", review_threshold)
    ):
        if (
            isinstance(value, bool)
            or not isinstance(
                value,
                (int, float)
            )
            or not 0 <= value <= 1
        ):
            raise ValueError(
                f"{name} debe estar entre 0 y 1."
            )

    if review_threshold > match_threshold:
        raise ValueError(
            "review_threshold no puede superar "
            "match_threshold."
        )


def _create_excerpt(
    text,
    max_chars=320
):
    """
    Crea un extracto breve de una evidencia.
    """

    normalized_text = " ".join(
        str(text).split()
    )

    if len(normalized_text) <= max_chars:
        return normalized_text

    return (
        normalized_text[:max_chars].rstrip()
        + "..."
    )


def _prepare_sources(
    sources,
    prefix
):
    """
    Asigna etiquetas R1, R2 o E1, E2.
    """

    prepared_sources = []

    for position, source in enumerate(
        sources,
        start=1
    ):
        prepared_source = dict(
            source
        )

        prepared_source[
            "source_label"
        ] = f"{prefix}{position}"

        prepared_sources.append(
            prepared_source
        )

    return prepared_sources


def _calculate_overall_similarity(
    reference_embeddings,
    evaluated_embeddings
):
    """
    Calcula la similitud entre centroides.
    """

    reference_centroid = (
        reference_embeddings.mean(
            axis=0
        )
    )

    evaluated_centroid = (
        evaluated_embeddings.mean(
            axis=0
        )
    )

    reference_norm = np.linalg.norm(
        reference_centroid
    )

    evaluated_norm = np.linalg.norm(
        evaluated_centroid
    )

    if (
        reference_norm == 0
        or evaluated_norm == 0
    ):
        return 0.0

    reference_centroid = (
        reference_centroid
        / reference_norm
    )

    evaluated_centroid = (
        evaluated_centroid
        / evaluated_norm
    )

    similarity = float(
        reference_centroid
        @ evaluated_centroid
    )

    return round(
        max(
            -1.0,
            min(1.0, similarity)
        ),
        4
    )


def _classify_score(
    score,
    match_threshold,
    review_threshold
):
    """
    Clasifica una coincidencia documental.
    """

    if score >= match_threshold:
        return "coincidencia_semantica"

    if score >= review_threshold:
        return "revision_manual"

    return "sin_evidencia_recuperada"


def _build_report(
    reference_name,
    evaluated_name,
    focus,
    mappings,
    metrics
):
    """
    Construye un informe determinista.
    """

    result_lines = []

    for mapping in mappings:
        result_lines.extend(
            [
                (
                    f"### [{mapping['reference_label']}] "
                    f"{mapping['status']}"
                ),
                "",
                (
                    "- Similitud máxima: "
                    f"{mapping['similarity']:.4f}"
                ),
                (
                    "- Referencia: página "
                    f"{mapping['reference_page']}, "
                    f"chunk {mapping['reference_chunk']}"
                ),
                (
                    "- Mejor evidencia evaluada: "
                    f"[{mapping['evaluated_label']}], "
                    f"página {mapping['evaluated_page']}, "
                    f"chunk {mapping['evaluated_chunk']}"
                ),
                "",
                "Evidencia de referencia:",
                "",
                f"> {mapping['reference_excerpt']}",
                "",
                "Evidencia evaluada más próxima:",
                "",
                f"> {mapping['evaluated_excerpt']}",
                ""
            ]
        )

    results_text = "\n".join(
        result_lines
    )

    return f"""
# Pre-evaluacion de cobertura documental

## Documentos

- Documento de referencia: {reference_name}
- Documento evaluado: {evaluated_name}
- Enfoque: {focus}

## Metricas

- Similitud global: {metrics['overall_similarity']:.4f}
- Evidencias de referencia evaluadas: {metrics['total_reference_items']}
- Coincidencias semanticas: {metrics['semantic_matches']}
- Revision manual necesaria: {metrics['manual_reviews']}
- Sin evidencia recuperada: {metrics['not_evidenced']}
- Cobertura semantica: {metrics['coverage_rate']:.2%}

## Resultados por evidencia de referencia

{results_text}

## Limitaciones

- La evaluacion se limita a los fragmentos recuperados.
- Una similitud alta no demuestra cumplimiento legal.
- Una similitud baja no demuestra incumplimiento.
- Cada resultado debe revisarse por una persona competente.
- El sistema no sustituye una auditoria normativa o juridica.
""".strip()


def analyze_requirements_coverage(
    reference_document_id,
    evaluated_document_id,
    focus=None,
    n_results=6,
    match_threshold=0.65,
    review_threshold=0.60
):
    """
    Compara evidencias de un documento evaluado frente
    a un documento utilizado como referencia.

    No determina cumplimiento legal.
    """

    reference_document_id = (
        _normalize_document_id(
            reference_document_id,
            "reference_document_id"
        )
    )

    evaluated_document_id = (
        _normalize_document_id(
            evaluated_document_id,
            "evaluated_document_id"
        )
    )

    if (
        reference_document_id
        == evaluated_document_id
    ):
        raise ValueError(
            "La referencia y el documento evaluado "
            "deben ser diferentes."
        )

    if (
        isinstance(n_results, bool)
        or not isinstance(n_results, int)
        or n_results <= 0
    ):
        raise ValueError(
            "n_results debe ser mayor que cero."
        )

    _validate_thresholds(
        match_threshold,
        review_threshold
    )

    coverage_focus = (
        str(focus).strip()
        if focus and str(focus).strip()
        else DEFAULT_FOCUS
    )

    retrieval_query = (
        "Identify explicit documentary evidence about "
        f"{coverage_focus}."
    )

    reference_sources = retrieve_context(
        query=retrieval_query,
        n_results=n_results,
        max_chunks_per_document=n_results,
        document_ids=[
            reference_document_id
        ]
    )

    evaluated_sources = retrieve_context(
        query=retrieval_query,
        n_results=n_results,
        max_chunks_per_document=n_results,
        document_ids=[
            evaluated_document_id
        ]
    )

    if not reference_sources:
        raise ValueError(
            "No se recuperaron evidencias "
            "del documento de referencia."
        )

    if not evaluated_sources:
        raise ValueError(
            "No se recuperaron evidencias "
            "del documento evaluado."
        )

    reference_sources = _prepare_sources(
        reference_sources,
        prefix="R"
    )

    evaluated_sources = _prepare_sources(
        evaluated_sources,
        prefix="E"
    )

    all_sources = (
        reference_sources
        + evaluated_sources
    )

    embeddings = np.asarray(
        generate_document_embeddings(
            [
                source["text"]
                for source in all_sources
            ],
            batch_size=min(
                16,
                len(all_sources)
            )
        ),
        dtype=np.float32
    )

    reference_embeddings = embeddings[
        :len(reference_sources)
    ]

    evaluated_embeddings = embeddings[
        len(reference_sources):
    ]

    similarity_matrix = (
        reference_embeddings
        @ evaluated_embeddings.T
    )

    mappings = []

    for reference_index, reference_source in enumerate(
        reference_sources
    ):
        evaluated_index = int(
            np.argmax(
                similarity_matrix[
                    reference_index
                ]
            )
        )

        score = float(
            similarity_matrix[
                reference_index,
                evaluated_index
            ]
        )

        evaluated_source = (
            evaluated_sources[
                evaluated_index
            ]
        )

        mappings.append(
            {
                "reference_label": (
                    reference_source[
                        "source_label"
                    ]
                ),
                "reference_page": (
                    reference_source.get(
                        "page_number"
                    )
                ),
                "reference_chunk": (
                    reference_source.get(
                        "chunk_index"
                    )
                ),
                "reference_excerpt": (
                    _create_excerpt(
                        reference_source[
                            "text"
                        ]
                    )
                ),
                "evaluated_label": (
                    evaluated_source[
                        "source_label"
                    ]
                ),
                "evaluated_page": (
                    evaluated_source.get(
                        "page_number"
                    )
                ),
                "evaluated_chunk": (
                    evaluated_source.get(
                        "chunk_index"
                    )
                ),
                "evaluated_excerpt": (
                    _create_excerpt(
                        evaluated_source[
                            "text"
                        ]
                    )
                ),
                "similarity": round(
                    score,
                    4
                ),
                "status": _classify_score(
                    score,
                    match_threshold,
                    review_threshold
                )
            }
        )

    semantic_matches = sum(
        mapping["status"]
        == "coincidencia_semantica"
        for mapping in mappings
    )

    manual_reviews = sum(
        mapping["status"]
        == "revision_manual"
        for mapping in mappings
    )

    not_evidenced = sum(
        mapping["status"]
        == "sin_evidencia_recuperada"
        for mapping in mappings
    )

    total_reference_items = len(
        mappings
    )

    metrics = {
        "overall_similarity": (
            _calculate_overall_similarity(
                reference_embeddings,
                evaluated_embeddings
            )
        ),
        "total_reference_items": (
            total_reference_items
        ),
        "semantic_matches": (
            semantic_matches
        ),
        "manual_reviews": manual_reviews,
        "not_evidenced": not_evidenced,
        "coverage_rate": (
            semantic_matches
            / total_reference_items
        ),
        "match_threshold": (
            match_threshold
        ),
        "review_threshold": (
            review_threshold
        )
    }

    reference_name = (
        reference_sources[0].get(
            "file_name",
            reference_document_id
        )
    )

    evaluated_name = (
        evaluated_sources[0].get(
            "file_name",
            evaluated_document_id
        )
    )

    report = _build_report(
        reference_name,
        evaluated_name,
        coverage_focus,
        mappings,
        metrics
    )

    return {
        "reference_document": {
            "document_id": (
                reference_document_id
            ),
            "file_name": reference_name,
            "sources": reference_sources
        },
        "evaluated_document": {
            "document_id": (
                evaluated_document_id
            ),
            "file_name": evaluated_name,
            "sources": evaluated_sources
        },
        "focus": coverage_focus,
        "metrics": metrics,
        "mappings": mappings,
        "report": report
    }