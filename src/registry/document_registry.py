import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

DEFAULT_REGISTRY_PATH = (
    BASE_DIR
    / "data"
    / "registry"
    / "documents.db"
)


DOCUMENT_FIELDS = (
    "document_id",
    "file_name",
    "file_path",
    "file_hash",
    "text_hash",
    "document_type",
    "analysis_role",
    "source_name",
    "source_url",
    "jurisdiction",
    "version",
    "publication_date",
    "page_count",
    "chunk_count",
    "status",
    "uploaded_at"
)


REQUIRED_FIELDS = (
    "document_id",
    "file_name",
    "file_path",
    "file_hash",
    "document_type",
    "status"
)


def _utc_now():
    """
    Devuelve la fecha actual en UTC.
    """

    return datetime.now(
        timezone.utc
    ).isoformat(
        timespec="seconds"
    )


def _connect(
    db_path=DEFAULT_REGISTRY_PATH
):
    """
    Abre una conexion SQLite.
    """

    database_path = Path(
        db_path
    )

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        database_path,
        timeout=30
    )

    connection.row_factory = (
        sqlite3.Row
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection

@contextmanager
def _connection(
    db_path=DEFAULT_REGISTRY_PATH
):
    """
    Abre, confirma o revierte y cierra
    siempre la conexion SQLite.
    """

    connection = _connect(
        db_path
    )

    try:
        with connection:
            yield connection

    finally:
        connection.close()

def initialize_registry(
    db_path=DEFAULT_REGISTRY_PATH
):
    """
    Crea la tabla e indices del registro.
    """
    with _connection(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL,
                text_hash TEXT,
                document_type TEXT NOT NULL,
                analysis_role TEXT,
                source_name TEXT,
                source_url TEXT,
                jurisdiction TEXT,
                version TEXT,
                publication_date TEXT,
                page_count INTEGER,
                chunk_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                uploaded_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_documents_text_hash
            ON documents(text_hash)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_documents_status
            ON documents(status)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_documents_type
            ON documents(document_type)
            """
        )


def _row_to_dict(row):
    """
    Convierte una fila SQLite en diccionario.
    """

    if row is None:
        return None

    return dict(row)


def _validate_record(record):
    """
    Valida los campos obligatorios.
    """

    if not isinstance(record, dict):
        raise TypeError(
            "record debe ser un diccionario."
        )

    missing_fields = [
        field
        for field in REQUIRED_FIELDS
        if (
            record.get(field) is None
            or str(
                record.get(field)
            ).strip() == ""
        )
    ]

    if missing_fields:
        raise ValueError(
            "Faltan campos obligatorios: "
            + ", ".join(
                missing_fields
            )
        )

    page_count = record.get(
        "page_count"
    )

    chunk_count = record.get(
        "chunk_count",
        0
    )

    if (
        page_count is not None
        and (
            isinstance(page_count, bool)
            or not isinstance(
                page_count,
                int
            )
            or page_count < 0
        )
    ):
        raise ValueError(
            "page_count debe ser un entero "
            "mayor o igual que cero."
        )

    if (
        isinstance(chunk_count, bool)
        or not isinstance(
            chunk_count,
            int
        )
        or chunk_count < 0
    ):
        raise ValueError(
            "chunk_count debe ser un entero "
            "mayor o igual que cero."
        )


def register_document(
    record,
    db_path=DEFAULT_REGISTRY_PATH
):
    """
    Registra un documento nuevo.
    """

    initialize_registry(
        db_path
    )

    record = dict(record)

    if record.get(
        "chunk_count"
    ) is None:
        record["chunk_count"] = 0

    if not record.get(
        "uploaded_at"
    ):
        record["uploaded_at"] = (
            _utc_now()
        )

    _validate_record(
        record
    )

    values = [
        record.get(field)
        for field in DOCUMENT_FIELDS
    ]

    placeholders = ", ".join(
        "?"
        for _ in DOCUMENT_FIELDS
    )

    fields_sql = ", ".join(
        DOCUMENT_FIELDS
    )

    try:
        with _connection(db_path) as connection:
            connection.execute(
                f"""
                INSERT INTO documents (
                    {fields_sql}
                )
                VALUES (
                    {placeholders}
                )
                """,
                values
            )

    except sqlite3.IntegrityError as error:
        raise ValueError(
            "No se pudo registrar el documento. "
            "El ID o el hash binario ya existe."
        ) from error

    return get_document(
        record["document_id"],
        db_path=db_path
    )


def get_document(
    document_id,
    db_path=DEFAULT_REGISTRY_PATH
):
    """
    Busca un documento por ID.
    """

    initialize_registry(
        db_path
    )

    with _connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM documents
            WHERE document_id = ?
            """,
            (
                str(document_id),
            )
        ).fetchone()

    return _row_to_dict(
        row
    )


def find_by_file_hash(
    file_hash,
    db_path=DEFAULT_REGISTRY_PATH
):
    """
    Busca una copia binaria exacta.
    """

    initialize_registry(
        db_path
    )

    with _connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM documents
            WHERE file_hash = ?
            """,
            (
                str(file_hash),
            )
        ).fetchone()

    return _row_to_dict(
        row
    )


def find_by_text_hash(
    text_hash,
    db_path=DEFAULT_REGISTRY_PATH
):
    """
    Busca documentos con el mismo texto normalizado.
    """

    if not text_hash:
        return []

    initialize_registry(
        db_path
    )

    with _connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM documents
            WHERE text_hash = ?
            ORDER BY uploaded_at ASC
            """,
            (
                str(text_hash),
            )
        ).fetchall()

    return [
        _row_to_dict(row)
        for row in rows
    ]


def list_documents(
    status=None,
    db_path=DEFAULT_REGISTRY_PATH
):
    """
    Lista documentos, opcionalmente por estado.
    """

    initialize_registry(
        db_path
    )

    with _connection(db_path) as connection:
        if status is None:
            rows = connection.execute(
                """
                SELECT *
                FROM documents
                ORDER BY uploaded_at DESC
                """
            ).fetchall()

        else:
            rows = connection.execute(
                """
                SELECT *
                FROM documents
                WHERE status = ?
                ORDER BY uploaded_at DESC
                """,
                (
                    str(status),
                )
            ).fetchall()

    return [
        _row_to_dict(row)
        for row in rows
    ]


def update_document_status(
    document_id,
    status,
    chunk_count=None,
    db_path=DEFAULT_REGISTRY_PATH
):
    """
    Actualiza el estado y, opcionalmente,
    el numero de chunks.
    """

    if not str(status).strip():
        raise ValueError(
            "status no puede estar vacio."
        )

    initialize_registry(
        db_path
    )

    with _connection(db_path) as connection:
        if chunk_count is None:
            cursor = connection.execute(
                """
                UPDATE documents
                SET status = ?
                WHERE document_id = ?
                """,
                (
                    str(status),
                    str(document_id)
                )
            )

        else:
            if (
                isinstance(chunk_count, bool)
                or not isinstance(
                    chunk_count,
                    int
                )
                or chunk_count < 0
            ):
                raise ValueError(
                    "chunk_count debe ser un entero "
                    "mayor o igual que cero."
                )

            cursor = connection.execute(
                """
                UPDATE documents
                SET status = ?,
                    chunk_count = ?
                WHERE document_id = ?
                """,
                (
                    str(status),
                    chunk_count,
                    str(document_id)
                )
            )

        if cursor.rowcount == 0:
            raise ValueError(
                "No existe el documento: "
                f"{document_id}"
            )

    return get_document(
        document_id,
        db_path=db_path
    )


def count_documents(
    db_path=DEFAULT_REGISTRY_PATH
):
    """
    Cuenta los documentos registrados.
    """

    initialize_registry(
        db_path
    )

    with _connection(db_path) as connection:
        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM documents
            """
        ).fetchone()[0]

    return int(count)


def delete_document(
    document_id,
    db_path=DEFAULT_REGISTRY_PATH
):
    """
    Elimina un registro.

    Se utilizara solo para revertir una carga fallida.
    """

    initialize_registry(
        db_path
    )

    with _connection(db_path) as connection:
        cursor = connection.execute(
            """
            DELETE FROM documents
            WHERE document_id = ?
            """,
            (
                str(document_id),
            )
        )

    return cursor.rowcount > 0