import sys
import tempfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(BASE_DIR)
    )


from pypdf import PdfWriter
from pypdf.generic import (
    DecodedStreamObject,
    DictionaryObject,
    NameObject
)

from src.ingestion.document_service import ingest_pdf
from src.registry.document_registry import (
    delete_document,
    get_document
)
from src.retrieval.rag import retrieve_context
from src.vector_db.chroma_db import (
    delete_document_chunks
)


def create_test_pdf(output_path):
    """
    Crea un PDF pequeño con texto extraíble y único.
    """

    writer = PdfWriter()

    page = writer.add_blank_page(
        width=612,
        height=792
    )

    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject(
                "/Helvetica"
            )
        }
    )

    font_reference = writer._add_object(
        font
    )

    resources = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {
                    NameObject("/F1"): font_reference
                }
            )
        }
    )

    page[
        NameObject("/Resources")
    ] = resources

    content = DecodedStreamObject()

    content.set_data(
        (
            "BT "
            "/F1 12 Tf "
            "72 720 Td "
            "(Unique dynamic ingestion test document. "
            "Employers should provide drinking water, "
            "shade, rest breaks and heat stress training "
            "to protect workers from excessive heat.) "
            "Tj "
            "ET"
        ).encode("ascii")
    )

    page[
        NameObject("/Contents")
    ] = writer._add_object(
        content
    )

    with Path(output_path).open(
        "wb"
    ) as pdf_file:
        writer.write(
            pdf_file
        )


def main():
    """
    Ejecuta una prueba integral y elimina sus datos al terminar.
    """

    document_id = None
    registry_database = None

    with tempfile.TemporaryDirectory() as temporary_name:

        temporary_directory = Path(
            temporary_name
        )

        test_pdf = (
            temporary_directory
            / "dynamic_ingestion_test.pdf"
        )

        upload_directory = (
            temporary_directory
            / "uploads"
        )

        registry_database = (
            temporary_directory
            / "documents_test.db"
        )

        create_test_pdf(
            test_pdf
        )

        try:

            result = ingest_pdf(
                file_path=test_pdf,
                document_type="test_document",
                analysis_role="target",
                source_name="integration_test",
                upload_dir=upload_directory,
                registry_db_path=registry_database
            )

            document_id = result[
                "document_id"
            ]

            if result["status"] != "indexed":
                raise AssertionError(
                    "El documento no quedó indexado."
                )

            if result["chunk_count"] <= 0:
                raise AssertionError(
                    "El documento no generó chunks."
                )

            registry_record = get_document(
                document_id,
                db_path=registry_database
            )

            if registry_record is None:
                raise AssertionError(
                    "El documento no aparece en SQLite."
                )

            context = retrieve_context(
                query=(
                    "What should employers provide "
                    "to protect workers from heat?"
                ),
                n_results=3,
                max_chunks_per_document=3,
                document_ids=[
                    document_id
                ]
            )

            if not context:
                raise AssertionError(
                    "El RAG no recuperó el documento."
                )

            unauthorized_ids = {
                item["document_id"]
                for item in context
            } - {
                document_id
            }

            if unauthorized_ids:
                raise AssertionError(
                    "El RAG recuperó documentos "
                    "no autorizados."
                )

            print(
                "Estado:",
                result["status"]
            )

            print(
                "Documento:",
                document_id
            )

            print(
                "Páginas:",
                result["page_count"]
            )

            print(
                "Chunks:",
                result["chunk_count"]
            )

            print(
                "Registro SQLite:",
                registry_record["status"]
            )

            print(
                "Fuentes recuperadas:",
                len(context)
            )

            print(
                "IDs no autorizados:",
                unauthorized_ids
            )

            for position, source in enumerate(
                context,
                start=1
            ):
                print(
                    f"[S{position}] "
                    f"{source['file_name']} "
                    f"| página "
                    f"{source['page_number']} "
                    f"| chunk "
                    f"{source['chunk_index']} "
                    f"| distancia "
                    f"{source['distance']:.4f}"
                )

        finally:

            removed_chunks = 0
            removed_registry = False

            if document_id is not None:

                removed_chunks = (
                    delete_document_chunks(
                        document_id
                    )
                )

                removed_registry = (
                    delete_document(
                        document_id,
                        db_path=registry_database
                    )
                )

            print(
                "Chunks de prueba eliminados:",
                removed_chunks
            )

            print(
                "Registro de prueba eliminado:",
                removed_registry
            )


if __name__ == "__main__":
    main()