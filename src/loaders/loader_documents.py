from pathlib import Path

from .pdf_loader import read_pdf
from .docx_loader import read_docx
from .txt_loader import read_txt

SUPPORTED_EXTENSIONS = {
    ".pdf": read_pdf,
    ".docx": read_docx,
    ".txt": read_txt,
}


def load_documents(folder_path):

    documents = []

    folder = Path(folder_path)

    print(f"Buscando en: {folder.resolve()}")
    print(f"¿Existe la carpeta? {folder.exists()}")

    for file in folder.rglob("*"):
        print("Encontrado:", file)

        if file.suffix.lower() in SUPPORTED_EXTENSIONS:

            reader = SUPPORTED_EXTENSIONS[file.suffix.lower()]

            text = reader(file)

            documents.append(
                {
                    "file_name": file.name,
                    "path": str(file),
                    "type": file.suffix.lower(),
                    "text": text,
                }
            )

    return documents



