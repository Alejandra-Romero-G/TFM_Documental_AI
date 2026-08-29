import csv
import hashlib
import re
from collections import Counter
from pathlib import Path

from pypdf import PdfReader


# ============================================================
# CONFIGURACIÓN
# ============================================================

PDF_DIRECTORY = Path("data/documents")
REPORTS_DIRECTORY = Path("reports")

REPORTS_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def calculate_file_hash(file_path):
    """
    Calcula el SHA-256 binario de un archivo.
    """

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)

    return sha256.hexdigest()


def normalize_text(text):
    """
    Normaliza el texto antes de calcular su hash.
    """

    text = text.lower()

    # Eliminar números de página aislados.
    text = re.sub(
        r"(?m)^\s*(page\s+)?\d+(\s+of\s+\d+)?\s*$",
        " ",
        text
    )

    # Unificar espacios y saltos de línea.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def calculate_text_hash(text):
    """
    Calcula el SHA-256 del texto normalizado.
    """

    normalized_text = normalize_text(text)

    if not normalized_text:
        return ""

    return hashlib.sha256(
        normalized_text.encode("utf-8")
    ).hexdigest()


def extract_pdf_information(pdf_path):
    """
    Extrae texto e información básica de un PDF.
    """

    result = {
        "file_name": pdf_path.name,
        "relative_path": str(pdf_path),
        "size_bytes": pdf_path.stat().st_size,
        "file_sha256": "",
        "text_sha256": "",
        "pages": 0,
        "characters": 0,
        "average_characters_per_page": 0,
        "likely_scanned": False,
        "extraction_status": "ok",
        "error": ""
    }

    try:
        result["file_sha256"] = calculate_file_hash(
            pdf_path
        )

        reader = PdfReader(str(pdf_path))

        result["pages"] = len(reader.pages)

        extracted_pages = []

        for page in reader.pages:
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""

            extracted_pages.append(page_text)

        full_text = "\n".join(extracted_pages)

        result["characters"] = len(full_text.strip())

        if result["pages"] > 0:
            result["average_characters_per_page"] = round(
                result["characters"] / result["pages"],
                2
            )

        result["likely_scanned"] = (
            result["pages"] > 0
            and result["average_characters_per_page"] < 100
        )

        result["text_sha256"] = calculate_text_hash(
            full_text
        )

        if not full_text.strip():
            result["extraction_status"] = "no_text"

    except Exception as error:
        result["extraction_status"] = "error"
        result["error"] = str(error)

    return result


def write_csv(file_path, rows, fieldnames):
    """
    Escribe una colección de filas en CSV.
    """

    with open(
        file_path,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# AUDITORÍA
# ============================================================

def audit_corpus():
    pdf_files = sorted(
        PDF_DIRECTORY.rglob("*.pdf")
    )

    print("=" * 70)
    print("AUDITORÍA DEL CORPUS OSHA")
    print("=" * 70)
    print(f"PDF encontrados: {len(pdf_files)}")
    print()

    rows = []

    for index, pdf_path in enumerate(
        pdf_files,
        start=1
    ):
        print(
            f"[{index}/{len(pdf_files)}] "
            f"{pdf_path.name}"
        )

        rows.append(
            extract_pdf_information(pdf_path)
        )

    # ========================================================
    # IDENTIFICAR DUPLICADOS
    # ========================================================

    file_hash_counts = Counter(
        row["file_sha256"]
        for row in rows
        if row["file_sha256"]
    )

    text_hash_counts = Counter(
        row["text_sha256"]
        for row in rows
        if row["text_sha256"]
    )

    canonical_by_file_hash = {}
    canonical_by_text_hash = {}

    for row in rows:
        file_hash = row["file_sha256"]
        text_hash = row["text_sha256"]

        row["duplicate_type"] = ""
        row["duplicate_of"] = ""

        if (
            file_hash
            and file_hash in canonical_by_file_hash
        ):
            row["duplicate_type"] = "exact"
            row["duplicate_of"] = (
                canonical_by_file_hash[file_hash]
            )

        elif (
            text_hash
            and text_hash in canonical_by_text_hash
        ):
            row["duplicate_type"] = "content"
            row["duplicate_of"] = (
                canonical_by_text_hash[text_hash]
            )

        else:
            if file_hash:
                canonical_by_file_hash[file_hash] = (
                    row["file_name"]
                )

            if text_hash:
                canonical_by_text_hash[text_hash] = (
                    row["file_name"]
                )

        canonical_name = (
            row["duplicate_of"]
            if row["duplicate_of"]
            else row["file_name"]
        )

        row["canonical_document_id"] = hashlib.sha256(
            canonical_name.encode("utf-8")
        ).hexdigest()[:16]

        row["file_hash_repetitions"] = (
            file_hash_counts.get(file_hash, 0)
        )

        row["text_hash_repetitions"] = (
            text_hash_counts.get(text_hash, 0)
        )

    fieldnames = list(rows[0].keys()) if rows else []

    # ========================================================
    # CREAR INFORMES
    # ========================================================

    write_csv(
        REPORTS_DIRECTORY / "corpus_audit.csv",
        rows,
        fieldnames
    )

    exact_duplicates = [
        row for row in rows
        if row["duplicate_type"] == "exact"
    ]

    content_duplicates = [
        row for row in rows
        if row["duplicate_type"] == "content"
    ]

    extraction_problems = [
        row for row in rows
        if row["extraction_status"] != "ok"
        or row["likely_scanned"]
    ]

    canonical_documents = [
        row for row in rows
        if not row["duplicate_of"]
        and row["extraction_status"] == "ok"
        and not row["likely_scanned"]
    ]

    write_csv(
        REPORTS_DIRECTORY / "exact_duplicates.csv",
        exact_duplicates,
        fieldnames
    )

    write_csv(
        REPORTS_DIRECTORY / "content_duplicates.csv",
        content_duplicates,
        fieldnames
    )

    write_csv(
        REPORTS_DIRECTORY / "extraction_problems.csv",
        extraction_problems,
        fieldnames
    )

    write_csv(
        REPORTS_DIRECTORY / "canonical_documents.csv",
        canonical_documents,
        fieldnames
    )

    # ========================================================
    # RESUMEN
    # ========================================================

    print()
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"Archivos totales: {len(rows)}")
    print(
        f"Duplicados exactos: "
        f"{len(exact_duplicates)}"
    )
    print(
        f"Duplicados por contenido: "
        f"{len(content_duplicates)}"
    )
    print(
        f"Problemas de extracción o escaneados: "
        f"{len(extraction_problems)}"
    )
    print(
        f"Documentos canónicos utilizables: "
        f"{len(canonical_documents)}"
    )
    print()
    print("Informes guardados en reports/")


if __name__ == "__main__":
    audit_corpus()