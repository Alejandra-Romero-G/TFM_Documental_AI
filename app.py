import csv
import tempfile
from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
CANONICAL_CSV = BASE_DIR / "reports" / "canonical_documents.csv"


st.set_page_config(
    page_title="Documentary AI",
    page_icon="📚",
    layout="wide"
)


def load_document_catalog():
    """Combina el manifiesto canónico y el registro dinámico."""

    documents_by_id = {}
    registry_error = None

    if CANONICAL_CSV.exists():
        with CANONICAL_CSV.open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as csv_file:
            for row in csv.DictReader(csv_file):
                document_id = row.get(
                    "canonical_document_id",
                    ""
                ).strip()

                if not document_id:
                    continue

                documents_by_id[document_id] = {
                    "document_id": document_id,
                    "file_name": row.get("file_name", ""),
                    "file_path": row.get("relative_path", ""),
                    "document_type": "pdf",
                    "analysis_role": "corpus",
                    "page_count": int(row.get("pages", 0) or 0),
                    "chunk_count": "",
                    "status": "indexed",
                    "origin": "canonical"
                }

    try:
        from src.registry.document_registry import list_documents

        for row in list_documents():
            document_id = row.get("document_id", "").strip()

            if not document_id:
                continue

            documents_by_id[document_id] = {
                **row,
                "document_id": document_id,
                "origin": "dynamic"
            }

    except Exception as error:
        registry_error = str(error)

    documents = sorted(
        documents_by_id.values(),
        key=lambda item: (
            item.get("file_name", "").lower(),
            item["document_id"]
        )
    )

    return documents, registry_error


def document_label(document_id, documents_by_id):
    """Crea una etiqueta legible para los selectores."""

    document = documents_by_id[document_id]
    origin = (
        "corpus"
        if document.get("origin") == "canonical"
        else "cargado"
    )

    return (
        f"{document.get('file_name', 'documento')} "
        f"[{origin}] · {document_id}"
    )


def sources_table(sources):
    """Convierte fuentes del RAG en filas compactas."""

    rows = []

    for position, source in enumerate(sources, start=1):
        distance = source.get("distance")

        rows.append(
            {
                "Fuente": source.get(
                    "source_label",
                    f"S{position}"
                ),
                "Documento": source.get(
                    "comparison_document",
                    ""
                ),
                "Archivo": source.get("file_name", ""),
                "Página": source.get("page_number", ""),
                "Chunk": source.get("chunk_index", ""),
                "Distancia": (
                    round(float(distance), 4)
                    if distance is not None
                    else None
                )
            }
        )

    return rows


def markdown_report(title, body, sources):
    """Construye una exportación Markdown sencilla."""

    lines = [
        f"# {title}",
        "",
        body.strip(),
        "",
        "## Fuentes",
        "",
        "| Fuente | Documento | Archivo | Página | Chunk |",
        "|---|---|---|---:|---:|"
    ]

    for row in sources_table(sources):
        lines.append(
            "| "
            f"{row['Fuente']} | "
            f"{row['Documento']} | "
            f"{row['Archivo']} | "
            f"{row['Página']} | "
            f"{row['Chunk']} |"
        )

    lines.extend(
        [
            "",
            (
                "Este resultado es un análisis documental "
                "asistido. No constituye una determinación "
                "de cumplimiento legal."
            ),
            ""
        ]
    )

    return "\n".join(lines)


def show_ingestion_result(result):
    """Muestra el último resultado de carga."""

    status = result.get("status")

    if result.get("duplicate"):
        st.warning(
            "El PDF ya está representado en el sistema. "
            "No se creó una copia ni un índice nuevo."
        )
        st.write(
            "Tipo de duplicado:",
            result.get("duplicate_type", "desconocido")
        )
        st.write(
            "Documento existente:",
            result.get("file_name", "")
        )
        st.write(
            "ID existente:",
            result.get("document_id", "")
        )
        return

    if status == "indexed":
        st.success(
            "PDF registrado e indexado correctamente."
        )
    elif status == "needs_ocr":
        st.warning(
            "El PDF fue registrado, pero necesita OCR "
            "antes de utilizarse en los análisis."
        )
    else:
        st.info(
            "Simulación completada sin modificar datos."
        )

    col1, col2, col3 = st.columns(3)
    col1.metric("Páginas", result.get("page_count", 0))
    col2.metric("Chunks", result.get("chunk_count", 0))
    col3.metric("Estado", status or "desconocido")
    st.code(result.get("document_id", ""), language=None)


def render_home(documents, registry_error):
    """Página inicial y resumen del sistema."""

    st.title("Sistema inteligente de análisis documental")
    st.write(
        "Carga, consulta, compara y preevalúa cobertura "
        "documental mediante BGE, ChromaDB y un LLM local."
    )

    canonical_count = sum(
        item.get("origin") == "canonical"
        for item in documents
    )
    dynamic_count = sum(
        item.get("origin") == "dynamic"
        for item in documents
    )
    indexed_count = sum(
        item.get("status") == "indexed"
        for item in documents
    )
    ocr_count = sum(
        item.get("status") == "needs_ocr"
        for item in documents
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Corpus canónico", canonical_count)
    col2.metric("PDF cargados", dynamic_count)
    col3.metric("Disponibles", indexed_count)
    col4.metric("Pendientes de OCR", ocr_count)

    st.subheader("Funciones disponibles")
    st.markdown(
        """
        - Ingestión de PDF con detección binaria y textual de duplicados.
        - Preguntas fundamentadas con archivo, página y fragmento.
        - Comparación semántica entre exactamente dos documentos.
        - Preevaluación de cobertura frente a un documento de referencia.
        - Exportación de resultados y trazabilidad de evidencias.
        """
    )

    st.info(
        "La cobertura calculada es semántica y documental. "
        "El sistema no certifica cumplimiento legal o normativo."
    )

    if registry_error:
        st.warning(
            "No se pudo leer el registro dinámico: "
            f"{registry_error}"
        )


def render_upload():
    """Carga y registra un PDF nuevo."""

    st.header("Cargar PDF")
    st.caption(
        "El sistema comprobará duplicados antes de generar embeddings."
    )

    if "last_ingestion" in st.session_state:
        show_ingestion_result(
            st.session_state["last_ingestion"]
        )
        st.divider()

    with st.form("upload_form"):
        uploaded_file = st.file_uploader(
            "Documento PDF",
            type=["pdf"]
        )

        col1, col2 = st.columns(2)

        with col1:
            document_type = st.selectbox(
                "Tipo documental",
                [
                    "manual",
                    "report",
                    "regulation",
                    "procedure",
                    "guide",
                    "other"
                ]
            )
            analysis_role = st.selectbox(
                "Función de análisis",
                ["target", "reference", "supporting"]
            )
            source_name = st.text_input(
                "Organización o fuente"
            )
            jurisdiction = st.text_input(
                "Jurisdicción"
            )

        with col2:
            source_url = st.text_input("URL oficial")
            version = st.text_input("Versión")
            publication_date = st.text_input(
                "Fecha de publicación",
                placeholder="AAAA-MM-DD"
            )
            dry_run = st.checkbox(
                "Solo simular; no guardar ni indexar"
            )

        submitted = st.form_submit_button(
            "Procesar PDF",
            type="primary"
        )

    if not submitted:
        return

    if uploaded_file is None:
        st.error("Selecciona un archivo PDF.")
        return

    from src.ingestion.document_service import ingest_pdf

    with st.spinner(
        "Comprobando, extrayendo e indexando el documento..."
    ):
        try:
            with tempfile.TemporaryDirectory() as temporary_name:
                temporary_path = (
                    Path(temporary_name)
                    / Path(uploaded_file.name).name
                )
                temporary_path.write_bytes(
                    uploaded_file.getvalue()
                )

                result = ingest_pdf(
                    file_path=temporary_path,
                    document_type=document_type,
                    analysis_role=analysis_role,
                    source_name=source_name,
                    source_url=source_url,
                    jurisdiction=jurisdiction,
                    version=version,
                    publication_date=publication_date,
                    dry_run=dry_run
                )

        except Exception as error:
            st.error(f"No se pudo procesar el PDF: {error}")
            return

    st.session_state["last_ingestion"] = result
    st.rerun()


def render_chat(analysis_ids, documents_by_id):
    """Chat RAG sobre todo el corpus o documentos elegidos."""

    st.header("Preguntas documentales")

    scope = st.radio(
        "Ámbito de la consulta",
        ["Todo el corpus", "Documentos seleccionados"],
        horizontal=True
    )

    selected_ids = []

    if scope == "Documentos seleccionados":
        selected_ids = st.multiselect(
            "Selecciona uno o varios PDF",
            analysis_ids,
            format_func=lambda value: document_label(
                value,
                documents_by_id
            )
        )

    question = st.text_area(
        "Pregunta",
        placeholder=(
            "Ejemplo: What preventive measures are recommended "
            "to protect workers from heat stress?"
        )
    )
    n_results = st.slider(
        "Número máximo de evidencias",
        min_value=1,
        max_value=10,
        value=5
    )

    if st.button("Responder", type="primary"):
        if not question.strip():
            st.error("Introduce una pregunta.")
        elif (
            scope == "Documentos seleccionados"
            and not selected_ids
        ):
            st.error("Selecciona al menos un documento.")
        else:
            with st.spinner("Recuperando evidencias y generando respuesta..."):
                try:
                    from src.analysis.analyzer import analyze_documents

                    result = analyze_documents(
                        question=question,
                        n_results=n_results,
                        document_ids=(
                            selected_ids
                            if selected_ids
                            else None
                        )
                    )
                    st.session_state["qa_result"] = result
                except Exception as error:
                    st.error(f"No se pudo responder: {error}")

    result = st.session_state.get("qa_result")

    if result:
        st.subheader("Respuesta")
        st.markdown(result.get("response", ""))
        st.subheader("Fuentes recuperadas")
        st.dataframe(
            sources_table(result.get("sources", [])),
            use_container_width=True,
            hide_index=True
        )


def render_comparison(analysis_ids, documents_by_id):
    """Compara dos documentos y permite exportar el resultado."""

    st.header("Comparación documental")

    if len(analysis_ids) < 2:
        st.warning("Se necesitan al menos dos documentos indexados.")
        return

    col1, col2 = st.columns(2)

    with col1:
        document_a_id = st.selectbox(
            "Documento A",
            analysis_ids,
            index=0,
            format_func=lambda value: document_label(
                value,
                documents_by_id
            ),
            key="comparison_a"
        )

    with col2:
        document_b_id = st.selectbox(
            "Documento B",
            analysis_ids,
            index=1,
            format_func=lambda value: document_label(
                value,
                documents_by_id
            ),
            key="comparison_b"
        )

    focus = st.text_input(
        "Enfoque",
        value=(
            "purpose, scope, hazards, preventive measures, "
            "responsibilities and recommendations"
        )
    )

    col3, col4 = st.columns(2)
    chunks_per_document = col3.slider(
        "Fragmentos por documento",
        1,
        8,
        4
    )
    threshold = col4.slider(
        "Umbral de similitud",
        0.0,
        1.0,
        0.65,
        0.01
    )

    if st.button("Comparar documentos", type="primary"):
        if document_a_id == document_b_id:
            st.error("Selecciona dos documentos diferentes.")
        else:
            with st.spinner("Comparando las evidencias documentales..."):
                try:
                    from src.analysis.document_comparator import compare_documents

                    result = compare_documents(
                        document_a_id=document_a_id,
                        document_b_id=document_b_id,
                        focus=focus,
                        chunks_per_document=chunks_per_document,
                        similarity_threshold=threshold
                    )
                    st.session_state["comparison_result"] = result
                except Exception as error:
                    st.error(f"No se pudo comparar: {error}")

    result = st.session_state.get("comparison_result")

    if result:
        semantic = result.get("semantic_comparison", {})
        st.metric(
            "Similitud semántica global",
            f"{semantic.get('overall_similarity', 0):.4f}"
        )
        st.subheader("Informe")
        st.markdown(result.get("response", ""))
        st.subheader("Fuentes")
        st.dataframe(
            sources_table(result.get("sources", [])),
            use_container_width=True,
            hide_index=True
        )

        report = markdown_report(
            "Informe de comparación documental",
            result.get("response", ""),
            result.get("sources", [])
        )
        file_a = Path(
            result["document_a"]["file_name"]
        ).stem
        file_b = Path(
            result["document_b"]["file_name"]
        ).stem
        st.download_button(
            "Descargar informe Markdown",
            data=report.encode("utf-8"),
            file_name=f"{file_a}_vs_{file_b}.md",
            mime="text/markdown"
        )


def render_coverage(analysis_ids, documents_by_id):
    """Preevalúa cobertura documental frente a una referencia."""

    st.header("Cobertura frente a una referencia")
    st.warning(
        "Esta función identifica cobertura semántica para revisión. "
        "No certifica cumplimiento legal."
    )

    if len(analysis_ids) < 2:
        st.warning("Se necesitan al menos dos documentos indexados.")
        return

    col1, col2 = st.columns(2)

    with col1:
        reference_id = st.selectbox(
            "Documento de referencia",
            analysis_ids,
            index=0,
            format_func=lambda value: document_label(
                value,
                documents_by_id
            ),
            key="coverage_reference"
        )

    with col2:
        evaluated_id = st.selectbox(
            "Documento evaluado",
            analysis_ids,
            index=1,
            format_func=lambda value: document_label(
                value,
                documents_by_id
            ),
            key="coverage_evaluated"
        )

    focus = st.text_input(
        "Enfoque de cobertura",
        value=(
            "hazards, preventive measures, first aid, "
            "responsibilities and requirements"
        )
    )

    col3, col4, col5 = st.columns(3)
    n_results = col3.slider(
        "Evidencias por documento",
        1,
        8,
        4
    )
    match_threshold = col4.slider(
        "Coincidencia",
        0.0,
        1.0,
        0.65,
        0.01
    )
    review_threshold = col5.slider(
        "Revisión manual",
        0.0,
        1.0,
        0.60,
        0.01
    )

    if st.button("Analizar cobertura", type="primary"):
        if reference_id == evaluated_id:
            st.error("Selecciona dos documentos diferentes.")
        elif review_threshold >= match_threshold:
            st.error(
                "El umbral de revisión debe ser menor "
                "que el de coincidencia."
            )
        else:
            with st.spinner("Calculando el mapeo de evidencias..."):
                try:
                    from src.analysis.requirements_coverage import (
                        analyze_requirements_coverage
                    )

                    result = analyze_requirements_coverage(
                        reference_document_id=reference_id,
                        evaluated_document_id=evaluated_id,
                        focus=focus,
                        n_results=n_results,
                        match_threshold=match_threshold,
                        review_threshold=review_threshold
                    )
                    st.session_state["coverage_result"] = result
                except Exception as error:
                    st.error(f"No se pudo analizar la cobertura: {error}")

    result = st.session_state.get("coverage_result")

    if result:
        metrics = result.get("metrics", {})
        col6, col7, col8, col9 = st.columns(4)
        col6.metric(
            "Similitud global",
            f"{metrics.get('overall_similarity', 0):.4f}"
        )
        col7.metric(
            "Coincidencias",
            metrics.get("semantic_matches", 0)
        )
        col8.metric(
            "Revisión manual",
            metrics.get("manual_reviews", 0)
        )
        col9.metric(
            "Cobertura semántica",
            f"{metrics.get('coverage_rate', 0):.2%}"
        )

        st.subheader("Informe")
        st.markdown(result.get("report", ""))
        st.subheader("Mapeo de evidencias")
        st.dataframe(
            result.get("mappings", []),
            use_container_width=True,
            hide_index=True
        )
        st.download_button(
            "Descargar informe Markdown",
            data=result.get("report", "").encode("utf-8"),
            file_name="coverage_report.md",
            mime="text/markdown"
        )


def render_registry(documents):
    """Lista el corpus y los documentos cargados."""

    st.header("Registro documental")
    st.write(f"Documentos registrados: {len(documents)}")

    rows = []

    for document in documents:
        rows.append(
            {
                "Archivo": document.get("file_name", ""),
                "ID": document.get("document_id", ""),
                "Origen": document.get("origin", ""),
                "Tipo": document.get("document_type", ""),
                "Función": document.get("analysis_role", ""),
                "Páginas": document.get("page_count", ""),
                "Chunks": document.get("chunk_count", ""),
                "Estado": document.get("status", "")
            }
        )

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True
    )


documents, registry_error = load_document_catalog()
documents_by_id = {
    item["document_id"]: item
    for item in documents
}
analysis_ids = [
    item["document_id"]
    for item in documents
    if item.get("status") == "indexed"
]


st.sidebar.title("Documentary AI")
page = st.sidebar.radio(
    "Navegación",
    [
        "Inicio",
        "Cargar PDF",
        "Preguntar",
        "Comparar",
        "Cobertura",
        "Registro"
    ]
)
st.sidebar.caption(
    "BGE + ChromaDB + Qwen local"
)


if page == "Inicio":
    render_home(documents, registry_error)
elif page == "Cargar PDF":
    render_upload()
elif page == "Preguntar":
    render_chat(analysis_ids, documents_by_id)
elif page == "Comparar":
    render_comparison(analysis_ids, documents_by_id)
elif page == "Cobertura":
    render_coverage(analysis_ids, documents_by_id)
elif page == "Registro":
    render_registry(documents)