def split_text(
    text: str,
    chunk_size: int = 300,
    chunk_overlap: int = 50
) -> list[str]:
    """
    Divide un texto en fragmentos de palabras solapados.

    Parameters
    ----------
    text:
        Texto que se dividirá.
    chunk_size:
        Número máximo aproximado de palabras por fragmento.
    chunk_overlap:
        Número de palabras compartidas entre fragmentos consecutivos.

    Returns
    -------
    list[str]
        Fragmentos de texto.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size debe ser mayor que cero.")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap no puede ser negativo.")

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap debe ser menor que chunk_size."
        )

    words = text.split()

    if not words:
        return []

    chunks = []
    start = 0

    while start < len(words):

        end = min(start + chunk_size, len(words))

        chunk = " ".join(words[start:end]).strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(words):
            break

        start = end - chunk_overlap

    return chunks