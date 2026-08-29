from pathlib import Path

from pypdf import PdfReader


def read_pdf_pages(file_path: Path) -> list[dict]:
    """
    Extrae el texto de un PDF página por página.

    Devuelve una lista con el número de página y su texto.
    Las páginas sin texto también se conservan para no perder
    la numeración original.
    """

    reader = PdfReader(file_path)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):

        page_text = page.extract_text() or ""

        pages.append(
            {
                "page_number": page_number,
                "text": page_text.strip()
            }
        )

    return pages


def read_pdf(file_path: Path) -> str:
    """
    Lee un PDF y devuelve todo su texto.

    Se mantiene esta función por compatibilidad con el código anterior.
    """

    pages = read_pdf_pages(file_path)

    return "\n\n".join(
        page["text"]
        for page in pages
        if page["text"]
    )