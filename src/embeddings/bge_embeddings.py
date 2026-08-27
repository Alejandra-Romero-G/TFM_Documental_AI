from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-base-en-v1.5"

model = SentenceTransformer(MODEL_NAME)


def generate_embedding(text):
    """
    Genera el embedding semántico de un texto.
    """

    embedding = model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding