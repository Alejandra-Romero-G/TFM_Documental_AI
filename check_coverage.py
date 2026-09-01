import argparse
import csv
import sys
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
    Resuelve un nombre o ID canonico.
    """

    normalized_selector = str(
        selector
    ).strip()

    if not normalized_selector:
        raise ValueError(
            "El selector no puede estar vacio."
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
            "Pre-evalua la cobertura documental "
            "frente a una referencia. "
            "No determina cumplimiento legal."
        )
    )

    parser.add_argument(
        "reference_document",
        help=(
            "Nombre o ID canonico del documento "
            "utilizado como referencia."
        )
    )

    parser.add_argument(
        "evaluated_document",
        help=(
            "Nombre o ID canonico del documento "
            "que se desea evaluar."
        )
    )

    parser.add_argument(
        "--focus",
        default=None,
        help=(
            "Enfoque opcional de la evaluacion."
        )
    )

    parser.add_argument(
        "--n-results",
        type=int,
        default=6,
        help=(
            "Numero de evidencias recuperadas "
            "por documento."
        )
    )

    parser.add_argument(
        "--match-threshold",
        type=float,
        default=0.65,
        help=(
            "Umbral minimo para coincidencia "
            "semantica."
        )
    )

    parser.add_argument(
        "--review-threshold",
        type=float,
        default=0.60,
        help=(
            "Umbral minimo para revision manual."
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

    if arguments.n_results <= 0:
        parser.error(
            "--n-results debe ser mayor que cero."
        )

    if not 0 <= arguments.match_threshold <= 1:
        parser.error(
            "--match-threshold debe estar "
            "entre 0 y 1."
        )

    if not 0 <= arguments.review_threshold <= 1:
        parser.error(
            "--review-threshold debe estar "
            "entre 0 y 1."
        )

    if (
        arguments.review_threshold
        > arguments.match_threshold
    ):
        parser.error(
            "--review-threshold no puede superar "
            "--match-threshold."
        )

    return arguments


def markdown_cell(value):
    """
    Escapa un valor para tablas Markdown.
    """

    return (
        str(value)
        .replace("|", "\\|")
        .replace("\n", " ")
        .rstrip()
    )


def build_export_report(result):
    """
    Anade trazabilidad tecnica al informe.
    """

    generated_at = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    clean_report = "\n".join(
        line.rstrip()
        for line in result[
            "report"
        ].splitlines()
    )

    lines = [
        clean_report,
        "",
        "## Informacion de ejecucion",
        "",
        f"- Fecha de generacion: {generated_at}",
        (
            "- Umbral de coincidencia: "
            f"{result['metrics']['match_threshold']:.2f}"
        ),
        (
            "- Umbral de revision: "
            f"{result['metrics']['review_threshold']:.2f}"
        ),
        "",
        "## Fuentes recuperadas",
        "",
        (
            "| Etiqueta | Tipo | Archivo | "
            "Pagina | Chunk | Distancia |"
        ),
        "|---|---|---|---:|---:|---:|"
    ]

    source_groups = (
        (
            "referencia",
            result[
                "reference_document"
            ][
                "sources"
            ]
        ),
        (
            "evaluado",
            result[
                "evaluated_document"
            ][
                "sources"
            ]
        )
    )

    for source_type, sources in source_groups:
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
                else ""
            )

            lines.append(
                "| "
                f"{markdown_cell(source['source_label'])} | "
                f"{source_type} | "
                f"{markdown_cell(source.get('file_name', ''))} | "
                f"{markdown_cell(source.get('page_number', ''))} | "
                f"{markdown_cell(source.get('chunk_index', ''))} | "
                f"{distance_text} |"
            )

    lines.extend(
        [
            "",
            "## Advertencia",
            "",
            (
                "Este resultado es una pre-evaluacion "
                "automatizada de cobertura documental. "
                "No demuestra cumplimiento o incumplimiento "
                "legal y requiere revision humana."
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
    Guarda el informe Markdown en UTF-8.
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


def print_mapping_summary(result):
    """
    Muestra el mapeo resumido.
    """

    print()
    print("=" * 70)
    print("MAPEO DE EVIDENCIAS")
    print("=" * 70)

    for mapping in result["mappings"]:
        print(
            f"[{mapping['reference_label']}] "
            f"-> [{mapping['evaluated_label']}] "
            f"| similitud "
            f"{mapping['similarity']:.4f} "
            f"| {mapping['status']}"
        )


def main():
    if hasattr(
        sys.stdout,
        "reconfigure"
    ):
        sys.stdout.reconfigure(
            errors="replace"
        )

    arguments = parse_arguments()
    arguments = parse_arguments()

    try:
        manifest = load_manifest()

        reference_row = resolve_document(
            arguments.reference_document,
            manifest
        )

        evaluated_row = resolve_document(
            arguments.evaluated_document,
            manifest
        )

        reference_id = reference_row[
            "canonical_document_id"
        ]

        evaluated_id = evaluated_row[
            "canonical_document_id"
        ]

        if reference_id == evaluated_id:
            raise ValueError(
                "La referencia y el documento "
                "evaluado deben ser diferentes."
            )

    except (
        FileNotFoundError,
        ValueError
    ) as error:
        print(f"Error: {error}")
        raise SystemExit(1)

    print(
        "Referencia: "
        f"{reference_row['file_name']}"
    )

    print(
        "Evaluado: "
        f"{evaluated_row['file_name']}"
    )

    # Importacion tardia para que --help
    # no cargue el modelo BGE.
    from src.analysis.requirements_coverage import (
        analyze_requirements_coverage
    )

    try:
        result = analyze_requirements_coverage(
            reference_document_id=reference_id,
            evaluated_document_id=evaluated_id,
            focus=arguments.focus,
            n_results=arguments.n_results,
            match_threshold=(
                arguments.match_threshold
            ),
            review_threshold=(
                arguments.review_threshold
            )
        )

    except ValueError as error:
        print(f"Error: {error}")
        raise SystemExit(1)

    print()
    print("=" * 70)
    print("INFORME DE COBERTURA")
    print("=" * 70)
    print(result["report"])

    print_mapping_summary(
        result
    )

    if arguments.output is not None:
        export_report = build_export_report(
            result
        )

        saved_path = save_report(
            export_report,
            arguments.output
        )

        print()
        print(
            "Informe guardado en: "
            f"{saved_path}"
        )


if __name__ == "__main__":
    main()