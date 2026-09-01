import argparse
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(BASE_DIR)
    )


def parse_arguments():
    """
    Procesa los argumentos de la CLI de ingestión.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Carga un PDF, detecta duplicados, extrae "
            "su contenido, genera embeddings BGE y lo "
            "registra en SQLite y ChromaDB."
        )
    )

    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Ruta del documento PDF."
    )

    parser.add_argument(
        "--document-type",
        default="pdf",
        help=(
            "Tipo documental, por ejemplo: manual, "
            "report, regulation, procedure o pdf."
        )
    )

    parser.add_argument(
        "--analysis-role",
        choices=[
            "reference",
            "target",
            "supporting"
        ],
        default="target",
        help=(
            "Función del documento en los análisis."
        )
    )

    parser.add_argument(
        "--source-name",
        default="",
        help=(
            "Nombre de la organización o fuente."
        )
    )

    parser.add_argument(
        "--source-url",
        default="",
        help="URL oficial del documento."
    )

    parser.add_argument(
        "--jurisdiction",
        default="",
        help=(
            "Jurisdicción aplicable, si se conoce."
        )
    )

    parser.add_argument(
        "--version",
        default="",
        help="Versión del documento."
    )

    parser.add_argument(
        "--publication-date",
        default="",
        help=(
            "Fecha de publicación, preferiblemente "
            "en formato AAAA-MM-DD."
        )
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Valida, extrae y detecta duplicados sin "
            "copiar, registrar ni indexar el PDF."
        )
    )

    return parser.parse_args()


def print_header(title):
    """
    Muestra una cabecera uniforme.
    """

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def print_duplicate_result(result):
    """
    Muestra información sobre un duplicado detectado.
    """

    print_header(
        "DOCUMENTO DUPLICADO"
    )

    duplicate_type = result.get(
        "duplicate_type",
        result.get(
            "status",
            "desconocido"
        )
    )

    duplicate_description = {
        "duplicate_file": (
            "El archivo PDF es binariamente idéntico "
            "a un documento existente."
        ),
        "duplicate_text": (
            "El archivo es diferente, pero su texto "
            "normalizado coincide con otro documento."
        )
    }.get(
        duplicate_type,
        "Se detectó un documento duplicado."
    )

    print(
        "Resultado:",
        duplicate_description
    )

    print(
        "Ámbito:",
        result.get(
            "duplicate_scope",
            "desconocido"
        )
    )

    print(
        "Documento existente:",
        result.get(
            "document_id",
            ""
        )
    )

    print(
        "Archivo existente:",
        result.get(
            "file_name",
            ""
        )
    )

    print(
        "No se modificaron SQLite ni ChromaDB."
    )


def print_ingestion_result(result):
    """
    Muestra el resultado de una ingestión nueva.
    """

    print_header(
        "RESULTADO DE LA INGESTIÓN"
    )

    print(
        "Estado:",
        result.get(
            "status",
            "desconocido"
        )
    )

    print(
        "ID documental:",
        result.get(
            "document_id",
            ""
        )
    )

    print(
        "Archivo:",
        result.get(
            "file_name",
            ""
        )
    )

    print(
        "Páginas:",
        result.get(
            "page_count",
            0
        )
    )

    print(
        "Chunks:",
        result.get(
            "chunk_count",
            0
        )
    )

    print(
        "Ruta almacenada:",
        result.get(
            "stored_path",
            ""
        )
    )

    if result.get("dry_run"):

        print()
        print(
            "Simulación completada: no se copiaron "
            "archivos y no se modificaron SQLite "
            "ni ChromaDB."
        )

    elif result.get("status") == "needs_ocr":

        print()
        print(
            "El PDF se registró, pero no contiene "
            "texto extraíble. Requiere OCR antes "
            "de poder utilizarse en el RAG."
        )

    elif result.get("status") == "indexed":

        print()
        print(
            "El documento quedó disponible para "
            "preguntas, comparaciones y análisis "
            "de cobertura documental."
        )


def main():
    arguments = parse_arguments()

    # Importación tardía para que --help no inicialice
    # ChromaDB ni cargue el modelo BGE.
    from src.ingestion.document_service import (
        ingest_pdf
    )

    try:

        result = ingest_pdf(
            file_path=arguments.pdf_path,
            document_type=(
                arguments.document_type
            ),
            analysis_role=(
                arguments.analysis_role
            ),
            source_name=(
                arguments.source_name
            ),
            source_url=(
                arguments.source_url
            ),
            jurisdiction=(
                arguments.jurisdiction
            ),
            version=arguments.version,
            publication_date=(
                arguments.publication_date
            ),
            dry_run=arguments.dry_run
        )

    except (
        FileNotFoundError,
        ValueError,
        RuntimeError
    ) as error:

        print_header(
            "ERROR DE INGESTIÓN"
        )

        print(
            f"Error: {error}"
        )

        raise SystemExit(1)

    if result.get("duplicate"):
        print_duplicate_result(
            result
        )

    else:
        print_ingestion_result(
            result
        )


if __name__ == "__main__":
    main()