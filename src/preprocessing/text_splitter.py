def split_text(text, chunk_size=1000, chunk_overlap=200):
    """
    Divide un texto en fragmentos de tamaño aproximado
    manteniendo un solapamiento entre ellos.
    """

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk)

        start += chunk_size - chunk_overlap

    return chunks