import argparse
import csv
from math import ceil
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

CANONICAL_CSV = (
    BASE_DIR
    / "reports"
    / "canonical_documents.csv"
)


def load_manifest():
    """
    Carga los documentos canónicos disponibles.
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


def resolve_documents(selectors, manifest):
    """
    Convierte nombres de archivo o IDs en IDs canónicos.
    """

    if not selectors:
        return [], []

    documents_by_id = {
        row["canonical_document_id"]: row
        for row in manifest
    }

    documents_by_name = {
        row["file_name"].lower(): row
        for row in manifest
    }

    selected_rows = []
    unknown_selectors = []

    for selector in selectors:

        selector = selector.strip()

        selected_document = (
            documents_by_id.get(selector)
            or documents_by_name.get(
                selector.lower()
            )
        )

        if selected_document is None:
            unknown_selectors.append(selector)
            continue

        document_id = selected_document[
            "canonical_document_id"
        ]

        if all(
            row["canonical_document_id"]
            != document_id
            for row in selected_rows
        ):
            selected_rows.append(
                selected_document
            )

    document_ids = [
        row["canonical_document_id"]
        for row in selected_rows
    ]

    return document_ids, unknown_selectors


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Realiza preguntas sobre el corpus documental."
        )
    )

    parser.add_argument(
        "question",
        nargs="*",
        help=(
            "Pregunta opcional. Si se omite, se solicita "
            "interactivamente."
        )
    )

    parser.add_argument(
        "--document",
        action="append",
        default=[],
        help=(
            "Nombre o ID canónico de un documento. "
            "Puede repetirse para seleccionar varios."
        )
    )

    parser.add_argument(
        "--n-results",
        type=int,
        default=5,
        help="Número máximo de fuentes recuperadas."
    )

    parser.add_argument(
        "--max-chunks-per-document",
        type=int,
        default=None,
        help=(
            "Máximo de chunks por PDF. "
            "Si se omite, se calcula automáticamente."
        )
    )

    arguments = parser.parse_args()

    if arguments.n_results <= 0:
        parser.error(
            "--n-results debe ser mayor que cero."
        )

    if (
        arguments.max_chunks_per_document
        is not None
        and arguments.max_chunks_per_document <= 0
    ):
        parser.error(
            "--max-chunks-per-document debe ser "
            "mayor que cero."
        )

    return arguments


def main():
    arguments = parse_arguments()

    question = " ".join(
        arguments.question
    ).strip()

    if not question:
        question = input(
            "Pregunta: "
        ).strip()

    if not question:
        print(
            "Debes introducir una pregunta."
        )
        raise SystemExit(1)

    manifest = load_manifest()

    document_ids, unknown_selectors = (
        resolve_documents(
            arguments.document,
            manifest
        )
    )

    if unknown_selectors:
        print(
            "No se encontraron estos documentos:"
        )

        for selector in unknown_selectors:
            print(f"- {selector}")

        raise SystemExit(1)

    if document_ids:

        selected_names = [
            row["file_name"]
            for row in manifest
            if row["canonical_document_id"]
            in document_ids
        ]

        print(
            "Documentos seleccionados: "
            + ", ".join(selected_names)
        )

    else:
        print(
            "Consultando todo el corpus "
            f"({len(manifest)} documentos)."
        )

    if (
        arguments.max_chunks_per_document
        is not None
    ):
        max_chunks_per_document = (
            arguments.max_chunks_per_document
        )

    elif len(document_ids) == 1:
        max_chunks_per_document = (
            arguments.n_results
        )

    elif document_ids:
        max_chunks_per_document = max(
            2,
            ceil(
                arguments.n_results
                / len(document_ids)
            )
        )

    else:
        max_chunks_per_document = 2

    # Las importaciones se realizan después de validar
    # la pregunta y los documentos para no cargar los
    # modelos innecesariamente.
    from src.retrieval.rag import (
        retrieve_context
    )

    results = retrieve_context(
        query=question,
        n_results=arguments.n_results,
        max_chunks_per_document=(
            max_chunks_per_document
        ),
        document_ids=(
            document_ids or None
        )
    )

    if not results:
        print(
            "No se encontró evidencia documental "
            "para responder la pregunta."
        )
        raise SystemExit(1)

    from src.llm.llm import generate_response

    answer = generate_response(
        question,
        results
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

    for position, result in enumerate(
        results,
        start=1
    ):
        distance = result.get("distance")

        distance_text = (
            f"{distance:.4f}"
            if distance is not None
            else "desconocida"
        )

        print(
            f"[S{position}] "
            f"{result.get('file_name', 'desconocido')} "
            f"| página "
            f"{result.get('page_number', 'desconocida')} "
            f"| chunk "
            f"{result.get('chunk_index', 'desconocido')} "
            f"| distancia {distance_text}"
        )


if __name__ == "__main__":
    main()