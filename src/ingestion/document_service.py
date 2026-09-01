import csv
import hashlib
import re
import shutil
from pathlib import Path


from src.loaders.chunker import split_text
from src.loaders.pdf_loader import read_pdf_pages
from src.registry.document_registry import (
    delete_document,
    find_by_file_hash,
    find_by_text_hash,
    get_document,
    register_document
)
from src.vector_db.chroma_db import (
    add_documents,
    delete_document_chunks
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

CANONICAL_CSV = (
    BASE_DIR
    / "reports"
    / "canonical_documents.csv"
)

DEFAULT_UPLOAD_DIR = (
    BASE_DIR
    / "data"
    / "uploads"
)

CHUNK_SIZE = 300
CHUNK_OVERLAP = 50
EMBEDDING_BATCH_SIZE = 32
CHROMA_BATCH_SIZE = 64


# ============================================================
# UTILIDADES DEL REGISTRO
# ============================================================

def _registry_call(
    function,
    *args,
    db_path=None,
    **kwargs
):
    """
    Ejecuta una operación del registro utilizando la base
    predeterminada o una base indicada expresamente.
    """

    if db_path is not None:
        kwargs["db_path"] = db_path

    return function(
        *args,
        **kwargs
    )


# ============================================================
# VALIDACIÓN Y HASHES
# ============================================================

def validate_pdf(file_path):
    """
    Comprueba que la ruta corresponda a un PDF existente.
    """

    file_path = Path(file_path).resolve()

    if not file_path.exists():
        raise FileNotFoundError(
            f"No existe el archivo: {file_path}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"La ruta no corresponde a un archivo: {file_path}"
        )

    if file_path.suffix.lower() != ".pdf":
        raise ValueError(
            "Solo se admiten documentos PDF."
        )

    if file_path.stat().st_size == 0:
        raise ValueError(
            "El archivo PDF está vacío."
        )

    with file_path.open("rb") as pdf_file:
        header = pdf_file.read(1024)

    if b"%PDF-" not in header:
        raise ValueError(
            "El archivo no contiene una cabecera PDF válida."
        )

    return file_path


def calculate_file_hash(file_path):
    """
    Calcula el SHA-256 binario de un archivo.
    """

    sha256 = hashlib.sha256()

    with Path(file_path).open("rb") as pdf_file:

        while True:
            block = pdf_file.read(
                1024 * 1024
            )

            if not block:
                break

            sha256.update(block)

    return sha256.hexdigest()


def normalize_text(text):
    """
    Normaliza el texto con las mismas reglas utilizadas
    por scripts/audit_corpus.py.
    """

    text = str(text).lower()

    text = re.sub(
        r"(?m)^\s*(page\s+)?\d+(\s+of\s+\d+)?\s*$",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def calculate_text_hash(text):
    """
    Calcula el SHA-256 del texto normalizado.
    """

    normalized_text = normalize_text(
        text
    )

    if not normalized_text:
        return ""

    return hashlib.sha256(
        normalized_text.encode("utf-8")
    ).hexdigest()


# ============================================================
# MANIFIESTO CANÓNICO
# ============================================================

def load_canonical_manifest():
    """
    Carga el manifiesto canónico para detectar duplicados
    frente al corpus original.
    """

    if not CANONICAL_CSV.exists():
        return []

    with CANONICAL_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:

        return list(
            csv.DictReader(csv_file)
        )


def find_canonical_by_value(
    manifest,
    field_name,
    value
):
    """
    Busca una coincidencia exacta dentro del manifiesto.
    """

    if not value:
        return None

    for row in manifest:

        if (
            str(
                row.get(
                    field_name,
                    ""
                )
            ).strip()
            == str(value).strip()
        ):
            return row

    return None


def build_document_id(
    file_hash,
    manifest,
    registry_db_path=None
):
    """
    Construye un ID estable y evita una posible colisión
    con otro documento.
    """

    for length in (
        16,
        24,
        32,
        64
    ):
        candidate = file_hash[:length]

        canonical_record = (
            find_canonical_by_value(
                manifest,
                "canonical_document_id",
                candidate
            )
        )

        registry_record = _registry_call(
            get_document,
            candidate,
            db_path=registry_db_path
        )

        if (
            canonical_record is None
            and registry_record is None
        ):
            return candidate

    raise ValueError(
        "No se pudo generar un ID documental único."
    )


# ============================================================
# RESULTADOS DE DUPLICADOS
# ============================================================

def build_duplicate_result(
    duplicate_type,
    duplicate_scope,
    file_hash,
    text_hash,
    existing_record
):
    """
    Construye una respuesta homogénea para duplicados.
    """

    existing_document_id = (
        existing_record.get(
            "document_id"
        )
        or existing_record.get(
            "canonical_document_id"
        )
        or ""
    )

    return {
        "status": duplicate_type,
        "duplicate": True,
        "duplicate_type": duplicate_type,
        "duplicate_scope": duplicate_scope,
        "document_id": existing_document_id,
        "file_name": existing_record.get(
            "file_name",
            ""
        ),
        "file_hash": file_hash,
        "text_hash": text_hash,
        "page_count": int(
            existing_record.get(
                "page_count",
                existing_record.get(
                    "pages",
                    0
                )
            )
            or 0
        ),
        "chunk_count": int(
            existing_record.get(
                "chunk_count",
                0
            )
            or 0
        ),
        "dry_run": False,
        "existing_document": existing_record
    }


# ============================================================
# RUTAS
# ============================================================

def sanitize_file_name(file_name):
    """
    Elimina caracteres no válidos para nombres de archivo.
    """

    sanitized_name = re.sub(
        r'[<>:"/\\|?*\x00-\x1F]',
        "_",
        Path(file_name).name
    ).strip()

    if not sanitized_name:
        sanitized_name = "document.pdf"

    return sanitized_name


def resolve_upload_directory(upload_dir):
    """
    Resuelve la carpeta donde se conservará el PDF.
    """

    if upload_dir is None:
        return DEFAULT_UPLOAD_DIR

    upload_dir = Path(upload_dir)

    if not upload_dir.is_absolute():
        upload_dir = (
            BASE_DIR
            / upload_dir
        )

    return upload_dir.resolve()


def path_for_metadata(file_path):
    """
    Devuelve una ruta relativa al proyecto cuando sea posible.
    """

    file_path = Path(file_path).resolve()

    try:
        return file_path.relative_to(
            BASE_DIR
        ).as_posix()

    except ValueError:
        return file_path.as_posix()


def copy_uploaded_pdf(
    source_path,
    destination_path
):
    """
    Copia el PDF sin sobrescribir un archivo diferente.
    Devuelve True si se creó un archivo nuevo.
    """

    source_path = Path(
        source_path
    ).resolve()

    destination_path = Path(
        destination_path
    ).resolve()

    if source_path == destination_path:
        return False

    if destination_path.exists():

        destination_hash = calculate_file_hash(
            destination_path
        )

        source_hash = calculate_file_hash(
            source_path
        )

        if destination_hash != source_hash:
            raise FileExistsError(
                "Ya existe un archivo diferente en "
                f"la ruta de destino: {destination_path}"
            )

        return False

    destination_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    shutil.copy2(
        source_path,
        destination_path
    )

    return True


# ============================================================
# CREACIÓN DE CHUNKS
# ============================================================

def create_document_chunks(
    pages,
    document_id,
    file_name,
    stored_path,
    file_hash,
    text_hash,
    document_type,
    analysis_role,
    source_name="",
    source_url="",
    jurisdiction="",
    version="",
    publication_date=""
):
    """
    Genera chunks y metadatos compatibles con el indexador
    canónico y con retrieve_context().
    """

    chunks = []

    optional_metadata = {
        "analysis_role": analysis_role,
        "source_name": source_name,
        "source_url": source_url,
        "jurisdiction": jurisdiction,
        "version": version,
        "publication_date": publication_date
    }

    optional_metadata = {
        key: value
        for key, value in optional_metadata.items()
        if value not in (
            None,
            ""
        )
    }

    for page in pages:

        page_number = int(
            page["page_number"]
        )

        page_text = str(
            page.get(
                "text",
                ""
            )
        ).strip()

        if not page_text:
            continue

        page_chunks = split_text(
            page_text,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )

        for chunk_index, chunk_text in enumerate(
            page_chunks
        ):
            chunk_id = (
                f"{document_id}"
                f"_p{page_number:04d}"
                f"_c{chunk_index:04d}"
            )

            metadata = {
                "document_id": document_id,
                "canonical_document_id": document_id,
                "chunk_id": chunk_id,
                "file_name": file_name,
                "relative_path": stored_path,
                "source_collection": "uploads",
                "document_type": document_type,
                "page_number": page_number,
                "chunk_index": chunk_index,
                "chunk_word_count": len(
                    chunk_text.split()
                ),
                "chunk_size_words": CHUNK_SIZE,
                "chunk_overlap_words": CHUNK_OVERLAP,
                "page_count": len(pages),
                "file_sha256": file_hash,
                "text_sha256": text_hash,
                **optional_metadata
            }

            chunks.append(
                {
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": metadata
                }
            )

    return chunks


# ============================================================
# REGISTRO DOCUMENTAL
# ============================================================

def build_registry_record(
    document_id,
    file_name,
    stored_path,
    file_hash,
    text_hash,
    document_type,
    analysis_role,
    page_count,
    chunk_count,
    status,
    source_name="",
    source_url="",
    jurisdiction="",
    version="",
    publication_date=""
):
    """
    Construye el registro persistente del documento.
    """

    return {
        "document_id": document_id,
        "file_name": file_name,
        "file_path": stored_path,
        "file_hash": file_hash,
        "text_hash": text_hash,
        "document_type": document_type,
        "analysis_role": analysis_role,
        "source_name": source_name,
        "source_url": source_url,
        "jurisdiction": jurisdiction,
        "version": version,
        "publication_date": publication_date,
        "page_count": page_count,
        "chunk_count": chunk_count,
        "status": status
    }


# ============================================================
# INGESTIÓN PRINCIPAL
# ============================================================

def ingest_pdf(
    file_path,
    document_type="pdf",
    analysis_role="target",
    source_name="",
    source_url="",
    jurisdiction="",
    version="",
    publication_date="",
    upload_dir=None,
    registry_db_path=None,
    dry_run=False
):
    """
    Valida, analiza, registra e indexa dinámicamente un PDF.

    La operación detecta duplicados contra el manifiesto
    canónico y contra el registro SQLite.

    Si dry_run es True, realiza las comprobaciones sin copiar,
    registrar ni indexar el documento.
    """

    source_path = validate_pdf(
        file_path
    )

    document_type = str(
        document_type
    ).strip() or "pdf"

    analysis_role = str(
        analysis_role
    ).strip() or "target"

    file_hash = calculate_file_hash(
        source_path
    )

    canonical_manifest = (
        load_canonical_manifest()
    )

    # --------------------------------------------------------
    # DUPLICADO BINARIO EN EL REGISTRO DINÁMICO
    # --------------------------------------------------------

    registry_file_duplicate = _registry_call(
        find_by_file_hash,
        file_hash,
        db_path=registry_db_path
    )

    if registry_file_duplicate is not None:
        return build_duplicate_result(
            duplicate_type="duplicate_file",
            duplicate_scope="registry",
            file_hash=file_hash,
            text_hash=registry_file_duplicate.get(
                "text_hash",
                ""
            ),
            existing_record=registry_file_duplicate
        )

    # --------------------------------------------------------
    # DUPLICADO BINARIO EN EL CORPUS CANÓNICO
    # --------------------------------------------------------

    canonical_file_duplicate = (
        find_canonical_by_value(
            canonical_manifest,
            "file_sha256",
            file_hash
        )
    )

    if canonical_file_duplicate is not None:
        return build_duplicate_result(
            duplicate_type="duplicate_file",
            duplicate_scope="canonical_manifest",
            file_hash=file_hash,
            text_hash=canonical_file_duplicate.get(
                "text_sha256",
                ""
            ),
            existing_record=canonical_file_duplicate
        )

    # --------------------------------------------------------
    # EXTRACCIÓN
    # --------------------------------------------------------

    try:
        pages = read_pdf_pages(
            source_path
        )

    except Exception as error:
        raise ValueError(
            "No se pudo leer el PDF: "
            f"{error}"
        ) from error

    if not pages:
        raise ValueError(
            "El PDF no contiene páginas."
        )

    full_text = "\n".join(
        str(
            page.get(
                "text",
                ""
            )
        )
        for page in pages
    )

    text_hash = calculate_text_hash(
        full_text
    )

    # --------------------------------------------------------
    # DUPLICADO TEXTUAL
    # --------------------------------------------------------

    if text_hash:

        registry_text_duplicates = (
            _registry_call(
                find_by_text_hash,
                text_hash,
                db_path=registry_db_path
            )
            or []
        )

        if registry_text_duplicates:
            return build_duplicate_result(
                duplicate_type="duplicate_text",
                duplicate_scope="registry",
                file_hash=file_hash,
                text_hash=text_hash,
                existing_record=(
                    registry_text_duplicates[0]
                )
            )

        canonical_text_duplicate = (
            find_canonical_by_value(
                canonical_manifest,
                "text_sha256",
                text_hash
            )
        )

        if canonical_text_duplicate is not None:
            return build_duplicate_result(
                duplicate_type="duplicate_text",
                duplicate_scope="canonical_manifest",
                file_hash=file_hash,
                text_hash=text_hash,
                existing_record=canonical_text_duplicate
            )

    # --------------------------------------------------------
    # IDENTIFICADOR Y RUTA
    # --------------------------------------------------------

    document_id = build_document_id(
        file_hash=file_hash,
        manifest=canonical_manifest,
        registry_db_path=registry_db_path
    )

    safe_file_name = sanitize_file_name(
        source_path.name
    )

    destination_directory = (
        resolve_upload_directory(
            upload_dir
        )
    )

    destination_path = (
        destination_directory
        / f"{document_id}_{safe_file_name}"
    )

    stored_path = path_for_metadata(
        destination_path
    )

    chunks = create_document_chunks(
        pages=pages,
        document_id=document_id,
        file_name=source_path.name,
        stored_path=stored_path,
        file_hash=file_hash,
        text_hash=text_hash,
        document_type=document_type,
        analysis_role=analysis_role,
        source_name=source_name,
        source_url=source_url,
        jurisdiction=jurisdiction,
        version=version,
        publication_date=publication_date
    )

    # --------------------------------------------------------
    # SIMULACIÓN SEGURA
    # --------------------------------------------------------

    if dry_run:

        return {
            "status": (
                "ready_for_indexing"
                if chunks
                else "needs_ocr"
            ),
            "duplicate": False,
            "document_id": document_id,
            "file_name": source_path.name,
            "file_hash": file_hash,
            "text_hash": text_hash,
            "page_count": len(pages),
            "chunk_count": len(chunks),
            "stored_path": stored_path,
            "dry_run": True
        }

    destination_created = False
    chunks_indexed = False
    registry_created = False

    try:

        destination_created = copy_uploaded_pdf(
            source_path,
            destination_path
        )

        # ----------------------------------------------------
        # PDF SIN TEXTO EXTRAÍBLE
        # ----------------------------------------------------

        if not chunks:

            registry_record = (
                build_registry_record(
                    document_id=document_id,
                    file_name=source_path.name,
                    stored_path=stored_path,
                    file_hash=file_hash,
                    text_hash="",
                    document_type=document_type,
                    analysis_role=analysis_role,
                    page_count=len(pages),
                    chunk_count=0,
                    status="needs_ocr",
                    source_name=source_name,
                    source_url=source_url,
                    jurisdiction=jurisdiction,
                    version=version,
                    publication_date=publication_date
                )
            )

            registered_document = (
                _registry_call(
                    register_document,
                    registry_record,
                    db_path=registry_db_path
                )
            )

            registry_created = True

            return {
                "status": "needs_ocr",
                "duplicate": False,
                "document_id": document_id,
                "file_name": source_path.name,
                "file_hash": file_hash,
                "text_hash": "",
                "page_count": len(pages),
                "chunk_count": 0,
                "stored_path": stored_path,
                "dry_run": False,
                "registry_record": registered_document
            }

        # ----------------------------------------------------
        # EMBEDDINGS E INDEXACIÓN
        # ----------------------------------------------------

        from src.embeddings.text_model import (
            generate_document_embeddings
        )

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = generate_document_embeddings(
            texts,
            batch_size=EMBEDDING_BATCH_SIZE
        )

        for batch_start in range(
            0,
            len(chunks),
            CHROMA_BATCH_SIZE
        ):
            batch_end = (
                batch_start
                + CHROMA_BATCH_SIZE
            )

            batch_chunks = chunks[
                batch_start:batch_end
            ]

            batch_embeddings = embeddings[
                batch_start:batch_end
            ]

            add_documents(
                document_ids=[
                    chunk["id"]
                    for chunk in batch_chunks
                ],
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

            chunks_indexed = True

        registry_record = build_registry_record(
            document_id=document_id,
            file_name=source_path.name,
            stored_path=stored_path,
            file_hash=file_hash,
            text_hash=text_hash,
            document_type=document_type,
            analysis_role=analysis_role,
            page_count=len(pages),
            chunk_count=len(chunks),
            status="indexed",
            source_name=source_name,
            source_url=source_url,
            jurisdiction=jurisdiction,
            version=version,
            publication_date=publication_date
        )

        registered_document = _registry_call(
            register_document,
            registry_record,
            db_path=registry_db_path
        )

        registry_created = True

        return {
            "status": "indexed",
            "duplicate": False,
            "document_id": document_id,
            "file_name": source_path.name,
            "file_hash": file_hash,
            "text_hash": text_hash,
            "page_count": len(pages),
            "chunk_count": len(chunks),
            "stored_path": stored_path,
            "dry_run": False,
            "registry_record": registered_document
        }

    except Exception as error:

        # Revierte Chroma si la indexación quedó incompleta.
        if chunks_indexed:

            try:
                delete_document_chunks(
                    document_id
                )

            except Exception:
                pass

        # Revierte SQLite si llegó a crearse el registro.
        if registry_created:

            try:
                _registry_call(
                    delete_document,
                    document_id,
                    db_path=registry_db_path
                )

            except Exception:
                pass

        # Solo elimina el archivo si esta operación lo copió.
        if (
            destination_created
            and destination_path.exists()
        ):

            try:
                destination_path.unlink()

            except OSError:
                pass

        raise RuntimeError(
            "La ingestión del PDF no pudo completarse: "
            f"{error}"
        ) from error