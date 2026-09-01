import argparse
import csv
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

CANONICAL_CSV = (
    BASE_DIR
    / "reports"
    / "canonical_documents.csv"
)


def load_manifest():
    """
    Carga el manifiesto de documentos canonicos.
    """

    if not CANONICAL_CSV.exists():
        raise FileNotFoundError(
            f"No existe el manifiesto: {CANONICAL_CSV}"
        )

    with CANONICAL_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:
        return list(
            csv.DictReader(csv_file)
        )


def resolve_document(
    selector,
    manifest
):
    """
    Resuelve un nombre de archivo o ID canonico.
    """

    normalized_selector = str(
        selector
    ).strip()

    if not normalized_selector:
        raise ValueError(
            "El selector documental no puede estar vacio."
        )

    for row in manifest:
        document_id = row.get(
            "canonical_document_id",
            ""
        ).strip()

        file_name = row.get(
            "file_name",
            ""
        ).strip()

        if (
            normalized_selector == document_id
            or normalized_selector.lower()
            == file_name.lower()
        ):
            return row

    raise ValueError(
        "No se encontro el documento: "
        f"{normalized_selector}"
    )


def parse_arguments():
    """
    Procesa los argumentos de la CLI.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Compara semanticamente dos documentos "
            "canonicos y genera un informe trazable."
        )
    )

    parser.add_argument(
        "document_a",
        help=(
            "Nombre de archivo o ID canonico "
            "del documento A."
        )
    )

    parser.add_argument(
        "document_b",
        help=(
            "Nombre de archivo o ID canonico "
            "del documento B."
        )
    )

    parser.add_argument(
        "--focus",
        default=None,
        help=(
            "Enfoque opcional de la comparacion."
        )
    )

    parser.add_argument(
        "--chunks-per-document",
        type=int,
        default=4,
        help=(
            "Numero maximo de fragmentos "
            "recuperados por documento."
        )
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.65,
        help=(
            "Umbral de similitud coseno "
            "entre 0 y 1."
        )
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Ruta opcional para exportar "
            "el informe Markdown."
        )
    )

    arguments = parser.parse_args()

    if arguments.chunks_per_document <= 0:
        parser.error(
            "--chunks-per-document debe ser "
            "mayor que cero."
        )

    if not 0 <= arguments.threshold <= 1:
        parser.error(
            "--threshold debe estar entre 0 y 1."
        )

    return arguments


def markdown_cell(value):
    """
    Escapa un valor para una tabla Markdown.
    """

    return (
        str(value)
        .replace("|", "\\|")
        .replace("\n", " ")
    )


def build_markdown_report(result):
    """
    Construye el informe Markdown exportable
    eliminando espacios finales.
    """

    document_a = result[
        "document_a"
    ]

    document_b = result[
        "document_b"
    ]

    semantic = result[
        "semantic_comparison"
    ]

    generated_at = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    clean_response = "\n".join(
        line.rstrip()
        for line in result[
            "response"
        ].splitlines()
    )

    lines = [
        "# Informe de comparación documental",
        "",
        f"- Fecha de generación: {generated_at}",
        (
            "- Documento A: "
            f"`{document_a['file_name']}` "
            f"(`{document_a['document_id']}`)"
        ),
        (
            "- Documento B: "
            f"`{document_b['file_name']}` "
            f"(`{document_b['document_id']}`)"
        ),
        f"- Enfoque: {result['focus']}",
        (
            "- Similitud semántica global: "
            f"{semantic['overall_similarity']:.4f}"
        ),
        (
            "- Umbral aplicado: "
            f"{semantic['similarity_threshold']:.2f}"
        ),
        "",
        "## Resultado",
        "",
        clean_response,
        "",
        "## Fuentes recuperadas",
        "",
        (
            "| Etiqueta | Documento | Archivo | "
            "Página | Chunk | Distancia |"
        ),
        "|---|---|---|---:|---:|---:|"
    ]

    for source in result["sources"]:
        distance = source.get(
            "distance"
        )

        distance_text = (
            f"{distance:.4f}"
            if isinstance(
                distance,
                (int, float)
            )
            else ""
        )

        lines.append(
            "| "
            f"{markdown_cell(source['source_label'])} | "
            f"{markdown_cell(source['comparison_document'])} | "
            f"{markdown_cell(source.get('file_name', ''))} | "
            f"{markdown_cell(source.get('page_number', ''))} | "
            f"{markdown_cell(source.get('chunk_index', ''))} | "
            f"{distance_text} |"
        )

    lines.extend(
        [
            "",
            "## Nota metodológica",
            "",
            (
                "El informe se basa en fragmentos recuperados "
                "mediante búsqueda semántica. Las coincidencias "
                "indican proximidad entre embeddings y no "
                "equivalencia factual ni cumplimiento legal."
            ),
            ""
        ]
    )

    return "\n".join(
        line.rstrip()
        for line in lines
    )


def save_report(
    report_text,
    output_path
):
    """
    Guarda el informe en UTF-8.
    """

    if output_path.suffix.lower() != ".md":
        output_path = output_path.with_suffix(
            ".md"
        )

    if not output_path.is_absolute():
        output_path = (
            BASE_DIR
            / output_path
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        report_text,
        encoding="utf-8"
    )

    return output_path.resolve()


def print_sources(sources):
    """
    Muestra las fuentes en la terminal.
    """

    print()
    print("=" * 70)
    print("FUENTES")
    print("=" * 70)

    for source in sources:
        distance = source.get(
            "distance"
        )

        distance_text = (
            f"{distance:.4f}"
            if isinstance(
                distance,
                (int, float)
            )
            else "desconocida"
        )

        print(
            f"[{source['source_label']}] "
            f"Documento "
            f"{source['comparison_document']} "
            f"| {source.get('file_name', '')} "
            f"| pagina "
            f"{source.get('page_number', '')} "
            f"| chunk "
            f"{source.get('chunk_index', '')} "
            f"| distancia {distance_text}"
        )


def main():
    arguments = parse_arguments()

    try:
        manifest = load_manifest()

        document_a = resolve_document(
            arguments.document_a,
            manifest
        )

        document_b = resolve_document(
            arguments.document_b,
            manifest
        )

        document_a_id = document_a[
            "canonical_document_id"
        ]

        document_b_id = document_b[
            "canonical_document_id"
        ]

        if document_a_id == document_b_id:
            raise ValueError(
                "Debes seleccionar dos "
                "documentos diferentes."
            )

    except (
        FileNotFoundError,
        ValueError
    ) as error:
        print(f"Error: {error}")
        raise SystemExit(1)

    print(
        "Documento A: "
        f"{document_a['file_name']}"
    )

    print(
        "Documento B: "
        f"{document_b['file_name']}"
    )

    print(
        "Umbral: "
        f"{arguments.threshold:.2f}"
    )

    # Importacion tardia para que --help y las
    # validaciones no carguen BGE ni Qwen.
    from src.analysis.document_comparator import (
        compare_documents
    )

    try:
        result = compare_documents(
            document_a_id=document_a_id,
            document_b_id=document_b_id,
            focus=arguments.focus,
            chunks_per_document=(
                arguments.chunks_per_document
            ),
            similarity_threshold=(
                arguments.threshold
            )
        )

    except ValueError as error:
        print(f"Error: {error}")
        raise SystemExit(1)

    print()
    print("=" * 70)
    print("INFORME COMPARATIVO")
    print("=" * 70)
    print(result["response"])

    print_sources(
        result["sources"]
    )

    if arguments.output is not None:
        report_text = build_markdown_report(
            result
        )

        saved_path = save_report(
            report_text,
            arguments.output
        )

        print()
        print(
            "Informe guardado en: "
            f"{saved_path}"
        )


if __name__ == "__main__":
    main()