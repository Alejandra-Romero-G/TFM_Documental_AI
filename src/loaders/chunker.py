def split_text(text, chunk_size=800, chunk_overlap=150):
    """
    Divide un texto en fragmentos solapados.

    Parameters
    ----------
    text : str
        Texto completo del documento.
    chunk_size : int
        Número aproximado de palabras por fragmento.
    chunk_overlap : int
        Número de palabras compartidas entre fragmentos.

    Returns
    -------
    list
        Lista de fragmentos de texto.
    """

    words = text.split()

    if not words:
        return []

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(words[start:end])

        if chunk.strip():
            chunks.append(chunk)

        if end >= len(words):
            break

        start = end - chunk_overlap

    return chunks