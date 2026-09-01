import re

import numpy as np

from src.embeddings.text_model import (
    generate_document_embeddings
)
from src.llm.llm import generate_response
from src.retrieval.rag import retrieve_context


DEFAULT_FOCUS = (
    "purpose, scope, hazards, preventive measures, "
    "responsibilities, recommendations and requirements"
)


# ============================================================
# VALIDACION
# ============================================================

def _normalize_document_id(
    document_id,
    argument_name
):
    """
    Valida y normaliza un ID canonico.
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


# ============================================================
# PREPARAR FUENTES
# ============================================================

def _prepare_sources(
    sources,
    document_role,
    offset
):
    """
    Anade el rol A/B y una etiqueta determinista.
    """

    prepared_sources = []

    for position, source in enumerate(
        sources,
        start=1
    ):
        prepared_source = dict(source)

        prepared_source[
            "comparison_document"
        ] = document_role

        prepared_source[
            "source_label"
        ] = f"S{offset + position}"

        prepared_sources.append(
            prepared_source
        )

    return prepared_sources


# ============================================================
# LIMPIAR RESPUESTAS DEL LLM
# ============================================================

def _clean_generated_response(response):
    """
    Elimina encabezados y listas de fuentes generadas
    libremente por el modelo.
    """

    cleaned_response = response.strip()

    cleaned_response = re.sub(
        r"^\s*\*{0,2}"
        r"(ANSWER|RESPUESTA)"
        r":\*{0,2}\s*",
        "",
        cleaned_response,
        count=1,
        flags=re.IGNORECASE
    )

    source_markers = (
        "SOURCES USED:",
        "FUENTES UTILIZADAS:",
        "Evidencias documentales recuperadas:"
    )

    for marker in source_markers:
        marker_position = cleaned_response.find(
            marker
        )

        if marker_position != -1:
            cleaned_response = cleaned_response[
                :marker_position
            ].rstrip()

    return cleaned_response


def _remove_source_labels(text):
    """
    Elimina las etiquetas locales de los resumenes
    intermedios.
    """

    return re.sub(
        r"\[S\d+\]",
        "",
        text
    ).strip()


# ============================================================
# RESUMIR UN DOCUMENTO
# ============================================================

def _summarize_document(
    document_name,
    sources,
    comparison_focus
):
    """
    Resume un unico documento sin mezclarlo
    con el otro documento.
    """

    summary_question = f"""
Analiza exclusivamente las evidencias recuperadas del documento
{document_name}.

Enfoque:
{comparison_focus}

Crea un resumen factual y breve con:

1. Proposito y alcance.
2. Riesgos o problemas descritos.
3. Medidas preventivas o recomendaciones.
4. Responsabilidades o requisitos.
5. Informacion que no puede determinarse con las evidencias.

No compares este documento con ningun otro.
No utilices conocimiento externo.
No declares cumplimiento legal.
Responde completamente en espanol.
""".strip()

    summary = generate_response(
        summary_question,
        sources
    )

    summary = _clean_generated_response(
        summary
    )

    summary = _remove_source_labels(
        summary
    )

    return summary


# ============================================================
# EXTRACTOS
# ============================================================

def _create_excerpt(
    text,
    max_chars=260
):
    """
    Crea un extracto breve y legible.
    """

    normalized_text = " ".join(
        str(text).split()
    )

    if len(normalized_text) <= max_chars:
        return normalized_text

    return (
        normalized_text[
            :max_chars
        ].rstrip()
        + "..."
    )

# ============================================================
# COMPARACION SEMANTICA
# ============================================================

def _calculate_semantic_comparison(
    sources_a,
    sources_b,
    similarity_threshold
):
    """
    Calcula similitudes coseno entre los fragmentos
    recuperados de ambos documentos.
    """

    texts_a = [
        str(source.get("text", ""))
        for source in sources_a
    ]

    texts_b = [
        str(source.get("text", ""))
        for source in sources_b
    ]

    all_texts = (
        texts_a
        + texts_b
    )

    embeddings = np.asarray(
        generate_document_embeddings(
            all_texts,
            batch_size=min(
                16,
                len(all_texts)
            )
        ),
        dtype=np.float32
    )

    embeddings_a = embeddings[
        :len(texts_a)
    ]

    embeddings_b = embeddings[
        len(texts_a):
    ]

    similarity_matrix = (
        embeddings_a
        @ embeddings_b.T
    )

    centroid_a = embeddings_a.mean(
        axis=0
    )

    centroid_b = embeddings_b.mean(
        axis=0
    )

    norm_a = np.linalg.norm(
        centroid_a
    )

    norm_b = np.linalg.norm(
        centroid_b
    )

    if norm_a == 0 or norm_b == 0:
        overall_similarity = 0.0
    else:
        centroid_a = (
            centroid_a
            / norm_a
        )

        centroid_b = (
            centroid_b
            / norm_b
        )

        overall_similarity = float(
            centroid_a
            @ centroid_b
        )

    overall_similarity = max(
        -1.0,
        min(
            1.0,
            overall_similarity
        )
    )

    related_pairs = []

    for index_a, source_a in enumerate(
        sources_a
    ):
        for index_b, source_b in enumerate(
            sources_b
        ):
            similarity = float(
                similarity_matrix[
                    index_a,
                    index_b
                ]
            )

            if (
                similarity
                >= similarity_threshold
            ):
                related_pairs.append(
                    {
                        "source_a": source_a[
                            "source_label"
                        ],
                        "page_a": source_a.get(
                            "page_number"
                        ),
                        "source_b": source_b[
                            "source_label"
                        ],
                        "page_b": source_b.get(
                            "page_number"
                        ),
                        "similarity": round(
                            similarity,
                            4
                        )
                    }
                )

    related_pairs.sort(
        key=lambda pair: pair[
            "similarity"
        ],
        reverse=True
    )

    distinct_a = []

    for index_a, source_a in enumerate(
        sources_a
    ):
        maximum_similarity = float(
            similarity_matrix[
                index_a
            ].max()
        )

        if (
            maximum_similarity
            < similarity_threshold
        ):
            distinct_a.append(
                {
                    "source_label": source_a[
                        "source_label"
                    ],
                    "page_number": source_a.get(
                        "page_number"
                    ),
                    "maximum_similarity": round(
                        maximum_similarity,
                        4
                    ),
                    "excerpt": _create_excerpt(
                        source_a.get(
                            "text",
                            ""
                        )
                    )
                }
            )

    distinct_b = []

    for index_b, source_b in enumerate(
        sources_b
    ):
        maximum_similarity = float(
            similarity_matrix[
                :,
                index_b
            ].max()
        )

        if (
            maximum_similarity
            < similarity_threshold
        ):
            distinct_b.append(
                {
                    "source_label": source_b[
                        "source_label"
                    ],
                    "page_number": source_b.get(
                        "page_number"
                    ),
                    "maximum_similarity": round(
                        maximum_similarity,
                        4
                    ),
                    "excerpt": _create_excerpt(
                        source_b.get(
                            "text",
                            ""
                        )
                    )
                }
            )

    return {
        "overall_similarity": round(
            overall_similarity,
            4
        ),
        "similarity_threshold": (
            similarity_threshold
        ),
        "related_pairs": (
            related_pairs
        ),
        "distinct_a": distinct_a,
        "distinct_b": distinct_b
    }


# ============================================================
# CONSTRUIR INFORME
# ============================================================

def _build_comparison_report(
    document_a_name,
    document_b_name,
    summary_a,
    summary_b,
    sources_a,
    sources_b,
    semantic_comparison,
    comparison_focus
):
    """
    Construye el informe final sin una tercera
    generacion del LLM.
    """

    labels_a = ", ".join(
        f"[{source['source_label']}]"
        for source in sources_a
    )

    labels_b = ", ".join(
        f"[{source['source_label']}]"
        for source in sources_b
    )

    related_pairs = semantic_comparison[
        "related_pairs"
    ]

    if related_pairs:
        related_lines = []

        for pair in related_pairs[:5]:
            related_lines.append(
                "- "
                f"[{pair['source_a']}] "
                f"pagina {pair['page_a']} "
                "y "
                f"[{pair['source_b']}] "
                f"pagina {pair['page_b']}: "
                "similitud "
                f"{pair['similarity']:.4f}"
            )

        related_text = "\n".join(
            related_lines
        )

    else:
        related_text = (
            "- No se detectaron coincidencias "
            "semanticas especificas por encima "
            "del umbral."
        )

    distinct_a = semantic_comparison[
        "distinct_a"
    ]

    if distinct_a:
        distinct_a_text = "\n".join(
            (
                f"- [{item['source_label']}] "
                f"pagina {item['page_number']} "
                "(similitud maxima "
                f"{item['maximum_similarity']:.4f}): "
                f"{item['excerpt']}"
            )
            for item in distinct_a
        )

    else:
        distinct_a_text = (
            "- No se detecto evidencia diferencial "
            "con el umbral utilizado."
        )

    distinct_b = semantic_comparison[
        "distinct_b"
    ]

    if distinct_b:
        distinct_b_text = "\n".join(
            (
                f"- [{item['source_label']}] "
                f"pagina {item['page_number']} "
                "(similitud maxima "
                f"{item['maximum_similarity']:.4f}): "
                f"{item['excerpt']}"
            )
            for item in distinct_b
        )

    else:
        distinct_b_text = (
            "- No se detecto evidencia diferencial "
            "con el umbral utilizado."
        )

    return f"""
COMPARACION DOCUMENTAL BASADA EN EVIDENCIAS

ENFOQUE

{comparison_focus}

1. ANALISIS DEL DOCUMENTO A: {document_a_name}

{summary_a}

Evidencias utilizadas: {labels_a}

2. ANALISIS DEL DOCUMENTO B: {document_b_name}

{summary_b}

Evidencias utilizadas: {labels_b}

3. SIMILITUD SEMANTICA GLOBAL

- Similitud coseno: {semantic_comparison['overall_similarity']:.4f}
- Umbral aplicado: {semantic_comparison['similarity_threshold']:.2f}

4. COINCIDENCIAS SEMANTICAS POTENCIALES

{related_text}

5. EVIDENCIA DIFERENCIAL DEL DOCUMENTO A

{distinct_a_text}

6. EVIDENCIA DIFERENCIAL DEL DOCUMENTO B

{distinct_b_text}

7. LIMITACIONES

- La comparacion se limita a los fragmentos recuperados.
- La similitud semantica indica proximidad textual,
  no equivalencia factual.
- La ausencia de una coincidencia no demuestra que
  el contenido no exista en el documento completo.
- Este informe no determina cumplimiento legal
  o normativo.
""".strip()


# ============================================================
# COMPARAR DOS DOCUMENTOS
# ============================================================

def compare_documents(
    document_a_id,
    document_b_id,
    focus=None,
    chunks_per_document=4,
    similarity_threshold=0.65
):
    """
    Compara dos documentos mediante:

    1. Recuperacion independiente de cada PDF.
    2. Resumen independiente con el LLM.
    3. Comparacion semantica determinista con BGE.
    4. Informe trazable construido con Python.

    No realiza una evaluacion legal de cumplimiento.
    """

    document_a_id = _normalize_document_id(
        document_a_id,
        "document_a_id"
    )

    document_b_id = _normalize_document_id(
        document_b_id,
        "document_b_id"
    )

    if (
        document_a_id
        == document_b_id
    ):
        raise ValueError(
            "Debes seleccionar dos documentos diferentes."
        )

    if (
        isinstance(
            chunks_per_document,
            bool
        )
        or not isinstance(
            chunks_per_document,
            int
        )
        or chunks_per_document <= 0
    ):
        raise ValueError(
            "chunks_per_document debe ser "
            "mayor que cero."
        )

    if (
        isinstance(
            similarity_threshold,
            bool
        )
        or not isinstance(
            similarity_threshold,
            (int, float)
        )
        or not 0 <= similarity_threshold <= 1
    ):
        raise ValueError(
            "similarity_threshold debe estar "
            "entre 0 y 1."
        )

    comparison_focus = (
        str(focus).strip()
        if (
            focus
            and str(focus).strip()
        )
        else DEFAULT_FOCUS
    )

    retrieval_query = (
        "Identify documentary evidence about "
        f"{comparison_focus}."
    )

    sources_a = retrieve_context(
        query=retrieval_query,
        n_results=chunks_per_document,
        max_chunks_per_document=(
            chunks_per_document
        ),
        document_ids=[
            document_a_id
        ]
    )

    sources_b = retrieve_context(
        query=retrieval_query,
        n_results=chunks_per_document,
        max_chunks_per_document=(
            chunks_per_document
        ),
        document_ids=[
            document_b_id
        ]
    )

    missing_documents = []

    if not sources_a:
        missing_documents.append(
            "A"
        )

    if not sources_b:
        missing_documents.append(
            "B"
        )

    if missing_documents:
        raise ValueError(
            "No se recuperaron evidencias para: "
            + ", ".join(
                missing_documents
            )
        )

    prepared_sources_a = _prepare_sources(
        sources_a,
        document_role="A",
        offset=0
    )

    prepared_sources_b = _prepare_sources(
        sources_b,
        document_role="B",
        offset=len(
            prepared_sources_a
        )
    )

    combined_sources = (
        prepared_sources_a
        + prepared_sources_b
    )

    document_a_name = (
        prepared_sources_a[0].get(
            "file_name",
            document_a_id
        )
    )

    document_b_name = (
        prepared_sources_b[0].get(
            "file_name",
            document_b_id
        )
    )

    summary_a = _summarize_document(
        document_a_name,
        prepared_sources_a,
        comparison_focus
    )

    summary_b = _summarize_document(
        document_b_name,
        prepared_sources_b,
        comparison_focus
    )

    semantic_comparison = (
        _calculate_semantic_comparison(
            prepared_sources_a,
            prepared_sources_b,
            similarity_threshold
        )
    )

    response = _build_comparison_report(
        document_a_name,
        document_b_name,
        summary_a,
        summary_b,
        prepared_sources_a,
        prepared_sources_b,
        semantic_comparison,
        comparison_focus
    )

    return {
        "document_a": {
            "document_id": (
                document_a_id
            ),
            "file_name": (
                document_a_name
            ),
            "summary": summary_a,
            "sources": (
                prepared_sources_a
            )
        },
        "document_b": {
            "document_id": (
                document_b_id
            ),
            "file_name": (
                document_b_name
            ),
            "summary": summary_b,
            "sources": (
                prepared_sources_b
            )
        },
        "focus": comparison_focus,
        "response": response,
        "sources": combined_sources,
        "semantic_comparison": (
            semantic_comparison
        )
    }