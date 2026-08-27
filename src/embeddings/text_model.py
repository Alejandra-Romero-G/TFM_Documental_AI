from sentence_transformers import SentenceTransformer


# ============================================================
# MODELO DE EMBEDDINGS
# ============================================================

MODEL_NAME = "BAAI/bge-base-en-v1.5"

model = SentenceTransformer(MODEL_NAME)


# ============================================================
# GENERAR EMBEDDING
# ============================================================

def generate_embedding(text):
    """
    Genera un embedding normalizado utilizando BGE-base-en-v1.5.
    """

    return model.encode(
        text,
        normalize_embeddings=True
    )