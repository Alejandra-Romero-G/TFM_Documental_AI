from transformers import AutoTokenizer, AutoModelForCausalLM


# ============================================================
# CONFIGURACIÓN DEL MODELO
# ============================================================

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"


# ============================================================
# CARGAR MODELO
# ============================================================

print("Cargando modelo LLM...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME
)

print("Modelo LLM cargado.")


# ============================================================
# GENERAR RESPUESTA
# ============================================================

def generate_response(question, context):
    """
    Genera una respuesta utilizando únicamente
    la información recuperada de los documentos.
    """

    # ========================================================
    # CONSTRUIR CONTEXTO
    # ========================================================

    context_parts = []

    max_chars_per_chunk = 3500

    for item in context:

        text = item["text"][:max_chars_per_chunk]

        context_parts.append(
            f"Documento: {item['file_name']}\n"
            f"Fragmento:\n{text}"
        )

    context_text = "\n\n".join(context_parts)

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = f"""
You are a document analysis assistant.

Answer the user's question using ONLY the information
contained in the provided document fragments.

Do not use outside knowledge.

Do not invent facts.

If the documents do not contain enough information
to answer the question, say:

"The information is not available in the provided documents."

Give a concise and factual answer.

At the end, list the documents used as sources.

DOCUMENT CONTEXT:
{context_text}

QUESTION:
{question}

ANSWER:
"""

    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    # ========================================================
    # CHAT TEMPLATE
    # ========================================================

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    # ========================================================
    # TOKENIZACIÓN
    # ========================================================

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=12000
    )

    # ========================================================
    # GENERACIÓN
    # ========================================================

    outputs = model.generate(
        **inputs,
        max_new_tokens=300,
        do_sample=False
    )

    # ========================================================
    # EXTRAER RESPUESTA
    # ========================================================

    generated_tokens = outputs[
        0
    ][
        inputs["input_ids"].shape[-1]:
    ]

    response = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True
    )

    return response.strip()