from pathlib import Path
from docx import Document


def read_docx(file_path: Path) -> str:

    document = Document(file_path)

    text = ""

    for paragraph in document.paragraphs:

        text += paragraph.text + "\n"

    return text