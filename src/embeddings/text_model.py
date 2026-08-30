from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURACIÓN
# ============================================================

MODEL_NAME = "BAAI/bge-base-en-v1.5"

QUERY_INSTRUCTION = (
    "Represent this sentence for searching relevant passages: "
)


# ============================================================
# CARGAR MODELO
# ============================================================

print("Cargando modelo BGE...")

model = SentenceTransformer(
    MODEL_NAME,
    device="cpu"
)

print("Modelo BGE cargado.")


# ============================================================
# EMBEDDING DE DOCUMENTOS
# ============================================================

def generate_document_embedding(text):
    """
    Genera un embedding normalizado para un fragmento documental.

    Devuelve:
        list[float]: embedding BGE de 768 dimensiones.
    """

    embedding = model.encode(
        text,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    return embedding.tolist()


# ============================================================
# EMBEDDINGS DE VARIOS DOCUMENTOS
# ============================================================

def generate_document_embeddings(texts, batch_size=32):
    """
    Genera embeddings normalizados para varios fragmentos.

    Es más eficiente que procesarlos uno a uno durante
    la indexación del corpus.
    """

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True
    )

    return embeddings.tolist()


# ============================================================
# EMBEDDING DE CONSULTAS
# ============================================================

def generate_query_embedding(question):
    """
    Genera el embedding normalizado de una pregunta.

    BGE recomienda añadir una instrucción a las consultas
    de recuperación, pero no a los documentos.
    """

    query = QUERY_INSTRUCTION + question.strip()

    embedding = model.encode(
        query,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    return embedding.tolist()


# ============================================================
# COMPATIBILIDAD CON EL CÓDIGO ANTERIOR
# ============================================================

def generate_embedding(text):
    """
    Alias temporal para el código anterior.

    Se considera que el texto recibido es un documento.
    """

    return generate_document_embedding(text)