import argparse
import csv
import sys
from pathlib import Path


# Permite ejecutar el script desde la carpeta scripts.
BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from src.loaders.chunker import split_text
from src.loaders.pdf_loader import read_pdf_pages
from src.vector_db.chroma_db import (
    add_documents,
    count_documents,
    get_existing_ids
)


CANONICAL_CSV = BASE_DIR / "reports" / "canonical_documents.csv"

CHUNK_SIZE = 300
CHUNK_OVERLAP = 50
EMBEDDING_BATCH_SIZE = 32
CHROMA_BATCH_SIZE = 64


def load_canonical_documents(limit=None):
    """
    Lee el manifiesto de documentos canónicos.
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

        documents = list(
            csv.DictReader(csv_file)
        )

    total_documents = len(documents)

    if limit is not None:
        documents = documents[:limit]

    return documents, total_documents


def create_document_chunks(document):
    """
    Extrae un PDF por páginas y genera chunks con IDs estables.
    """

    relative_path = Path(document["relative_path"])
    file_path = BASE_DIR / relative_path

    if not file_path.exists():
        raise FileNotFoundError(
            f"No se encontró el PDF: {file_path}"
        )

    canonical_document_id = document["canonical_document_id"]
    file_name = document["file_name"]
    source_collection = relative_path.parent.name

    pages = read_pdf_pages(file_path)

    chunks = []

    for page in pages:

        page_number = page["page_number"]
        page_text = page["text"]

        if not page_text:
            continue

        page_chunks = split_text(
            page_text,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )

        for chunk_index, chunk_text in enumerate(page_chunks):

            chunk_id = (
                f"{canonical_document_id}"
                f"_p{page_number:04d}"
                f"_c{chunk_index:04d}"
            )

            metadata = {
                "document_id": canonical_document_id,
                "canonical_document_id": canonical_document_id,
                "chunk_id": chunk_id,
                "file_name": file_name,
                "relative_path": document["relative_path"].replace(
                    "\\",
                    "/"
                ),
                "source_collection": source_collection,
                "document_type": "pdf",
                "page_number": page_number,
                "chunk_index": chunk_index,
                "chunk_word_count": len(chunk_text.split()),
                "chunk_size_words": CHUNK_SIZE,
                "chunk_overlap_words": CHUNK_OVERLAP,
                "page_count": int(document["pages"]),
                "file_sha256": document["file_sha256"],
                "text_sha256": document["text_sha256"]
            }

            chunks.append(
                {
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": metadata
                }
            )

    return chunks


def index_corpus(limit=None, dry_run=False):
    """
    Indexa los documentos canónicos en la colección BGE.
    """

    documents, total_manifest_documents = (
        load_canonical_documents(limit=limit)
    )

    existing_ids = get_existing_ids()

    print("=" * 70)
    print("INDEXACIÓN CANÓNICA CON BGE")
    print("=" * 70)
    print(
        f"Documentos en el manifiesto: "
        f"{total_manifest_documents}"
    )
    print(
        f"Documentos seleccionados: "
        f"{len(documents)}"
    )
    print(
        f"Chunks existentes en ChromaDB: "
        f"{len(existing_ids)}"
    )
    print(
        f"Modo simulación: "
        f"{'sí' if dry_run else 'no'}"
    )

    generate_document_embeddings = None

    if not dry_run:
        from src.embeddings.text_model import (
            generate_document_embeddings
        )

    processed_documents = 0
    failed_documents = 0
    detected_chunks = 0
    inserted_chunks = 0
    previously_indexed_chunks = 0
    errors = []

    for position, document in enumerate(documents, start=1):

        file_name = document["file_name"]

        print()
        print("-" * 70)
        print(
            f"[{position}/{len(documents)}] "
            f"{file_name}"
        )

        try:
            document_chunks = create_document_chunks(
                document
            )

            if not document_chunks:
                raise ValueError(
                    "El documento no generó ningún chunk."
                )

            detected_chunks += len(document_chunks)

            pending_chunks = [
                chunk
                for chunk in document_chunks
                if chunk["id"] not in existing_ids
            ]

            already_indexed = (
                len(document_chunks) -
                len(pending_chunks)
            )

            previously_indexed_chunks += already_indexed

            print(
                f"Páginas declaradas: "
                f"{document['pages']}"
            )
            print(
                f"Chunks detectados: "
                f"{len(document_chunks)}"
            )
            print(
                f"Chunks ya existentes: "
                f"{already_indexed}"
            )
            print(
                f"Chunks pendientes: "
                f"{len(pending_chunks)}"
            )

            if dry_run:
                processed_documents += 1
                continue

            if not pending_chunks:
                print("Documento ya indexado. Se omite.")
                processed_documents += 1
                continue

            texts = [
                chunk["text"]
                for chunk in pending_chunks
            ]

            embeddings = generate_document_embeddings(
                texts,
                batch_size=EMBEDDING_BATCH_SIZE
            )

            for batch_start in range(
                0,
                len(pending_chunks),
                CHROMA_BATCH_SIZE
            ):

                batch_end = (
                    batch_start +
                    CHROMA_BATCH_SIZE
                )

                batch_chunks = pending_chunks[
                    batch_start:batch_end
                ]

                batch_embeddings = embeddings[
                    batch_start:batch_end
                ]

                batch_ids = [
                    chunk["id"]
                    for chunk in batch_chunks
                ]

                add_documents(
                    document_ids=batch_ids,
                    texts=[
                        chunk["text"]
                        for chunk in batch_chunks
                    ],
                    embeddings=batch_embeddings,
                    metadatas=[
                        chunk["metadata"]
                        for chunk in batch_chunks
                    ]
                )

                existing_ids.update(batch_ids)
                inserted_chunks += len(batch_ids)

            processed_documents += 1

            print(
                f"Documento indexado. "
                f"Total actual: {count_documents()} chunks"
            )

        except Exception as error:

            failed_documents += 1

            errors.append(
                {
                    "file_name": file_name,
                    "error": str(error)
                }
            )

            print(
                f"ERROR: {error}"
            )

    print()
    print("=" * 70)
    print("RESUMEN DE INDEXACIÓN")
    print("=" * 70)
    print(
        f"Documentos procesados correctamente: "
        f"{processed_documents}"
    )
    print(
        f"Documentos con error: "
        f"{failed_documents}"
    )
    print(
        f"Chunks detectados: "
        f"{detected_chunks}"
    )
    print(
        f"Chunks que ya existían: "
        f"{previously_indexed_chunks}"
    )
    print(
        f"Chunks insertados: "
        f"{inserted_chunks}"
    )
    print(
        f"Chunks finales en ChromaDB: "
        f"{count_documents()}"
    )

    if errors:

        print()
        print("ERRORES:")

        for error in errors:
            print(
                f"- {error['file_name']}: "
                f"{error['error']}"
            )

    if dry_run:
        print()
        print(
            "La simulación no ha generado embeddings "
            "ni modificado ChromaDB."
        )


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Indexa los documentos canónicos con BGE."
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Procesa solamente los primeros N documentos."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Comprueba rutas, extracción y chunking "
            "sin modificar ChromaDB."
        )
    )

    arguments = parser.parse_args()

    if (
        arguments.limit is not None
        and arguments.limit <= 0
    ):
        parser.error(
            "--limit debe ser mayor que cero."
        )

    return arguments


if __name__ == "__main__":
    args = parse_arguments()

    index_corpus(
        limit=args.limit,
        dry_run=args.dry_run
    )