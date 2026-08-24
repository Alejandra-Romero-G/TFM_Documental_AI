from transformers import AutoTokenizer, AutoModelForCausalLM


MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"


print("Cargando modelo LLM...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME
)

print("Modelo LLM cargado.")


def generate_response(question, context):
    """
    Genera una respuesta utilizando la pregunta y
    el contexto recuperado desde los documentos.
    """

    context_text = "\n\n".join(
        [
            f"Documento: {item['file_name']}\n"
            f"Fragmento: {item['text']}"
            for item in context
        ]
    )

    prompt = f"""
You are an assistant specialized in analyzing documents.

Answer the user's question using ONLY the information
contained in the provided context.

If the answer cannot be found in the context,
say that the information is not available in the documents.

Context:
{context_text}

Question:
{question}

Answer:
"""

    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(
        text,
        return_tensors="pt"
    )

    outputs = model.generate(
        **inputs,
        max_new_tokens=300,
        do_sample=False
    )

    generated_tokens = outputs[0][inputs["input_ids"].shape[-1]:]

    response = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True
    )

    return response.strip()