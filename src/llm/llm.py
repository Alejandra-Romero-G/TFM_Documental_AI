import re
import torch
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

MAX_CHARS_PER_CHUNK = 2500
MAX_INPUT_TOKENS = 8192
MAX_NEW_TOKENS = 400


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

model.eval()

print("Modelo LLM cargado.")


# ============================================================
# CONSTRUIR CONTEXTO CON FUENTES
# ============================================================

def build_context_with_sources(context):
    """
    Convierte los resultados del retrieval en evidencias
    identificadas como S1, S2, etc.
    """

    if not context:
        return ""

    context_parts = []

    for position, item in enumerate(
        context,
        start=1
    ):
        source_id = f"S{position}"

        text = str(
            item.get("text", "")
        )[:MAX_CHARS_PER_CHUNK]

        file_name = item.get(
            "file_name",
            "documento_desconocido"
        )

        page_number = item.get(
            "page_number",
            "desconocida"
        )

        chunk_index = item.get(
            "chunk_index",
            item.get("chunk", "desconocido")
        )

        context_parts.append(
            f"[{source_id}]\n"
            f"Document: {file_name}\n"
            f"Page: {page_number}\n"
            f"Chunk: {chunk_index}\n"
            f"Text:\n{text}"
        )

    return "\n\n".join(context_parts)


# ============================================================
# GENERAR RESPUESTA
# ============================================================

def generate_response(question, context):
    """
    Genera una respuesta fundamentada exclusivamente
    en los fragmentos documentales recuperados.
    """

    if not question or not question.strip():
        raise ValueError(
            "La pregunta no puede estar vacía."
        )

    if not context:
        return (
            "La información no está disponible "
            "en los documentos proporcionados."
        )

    context_text = build_context_with_sources(
        context
    )

    system_message = """
You are an evidence-based document analysis assistant.

Follow these rules:

1. Use only the supplied documentary evidence.
2. Do not use outside knowledge.
3. Do not invent facts, requirements or conclusions.
4. Answer in the same language as the user's question.
5. Cite supporting evidence using labels such as [S1] or [S2].
6. Every important factual claim must have at least one citation.
7. Never invent a source label.
8. If sources disagree, describe the disagreement and cite both.
9. If the evidence is insufficient, state that the information is
   not available in the provided documents.
10. Do not claim that an organization legally complies with a
    regulation based only on documentary evidence.
11. Finish with a short line identifying the source labels used.

Keep the response concise, factual and clearly structured.
""".strip()

    user_message = f"""
DOCUMENTARY EVIDENCE:

{context_text}

USER QUESTION:

{question.strip()}

MANDATORY OUTPUT FORMAT:

ANSWER:
- Write each claim followed by its supporting label, for example [S1].
- Do not include a claim if it cannot be supported by a supplied label.

SOURCES USED:
- List only valid labels from the documentary evidence.

A valid answer must contain at least one source label.
""".strip()

    messages = [
        {
            "role": "system",
            "content": system_message
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    chat_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(
        chat_text,
        return_tensors="pt",
        truncation=True,
        max_length=MAX_INPUT_TOKENS
    )

    with torch.inference_mode():

        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            repetition_penalty=1.05,
            pad_token_id=tokenizer.eos_token_id
        )

    generated_tokens = outputs[0][
        inputs["input_ids"].shape[-1]:
    ]

    response = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True
    ).strip()

    valid_source_labels = [
        f"[S{position}]"
        for position in range(
            1,
            len(context) + 1
        )
    ]

    cited_labels = set(
        re.findall(
            r"\[S\d+\]",
            response
        )
    )

    # Elimina etiquetas inventadas por el modelo.
    for cited_label in cited_labels:

        if cited_label not in valid_source_labels:
            response = response.replace(
                cited_label,
                ""
            )

    has_valid_citation = any(
        source_label in response
        for source_label in valid_source_labels
    )

    # Qwen 1.5B puede omitir las etiquetas aunque el
    # contenido sea correcto. Se añade entonces una lista
    # determinista de las evidencias que recibió.
    if not has_valid_citation:

        response = (
            f"{response}\n\n"
            "Evidencias documentales recuperadas: "
            + ", ".join(valid_source_labels)
        )

    return response.strip()