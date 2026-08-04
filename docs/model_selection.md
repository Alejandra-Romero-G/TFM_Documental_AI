# Modelos del proyecto

## Embeddings documentos

Modelo:
all-MiniLM-L6-v2

Motivo:
Excelente rendimiento para búsqueda semántica.

---

## Embeddings imágenes

Modelo:
OpenCLIP ViT-B-32

Motivo:
Genera embeddings compatibles entre texto e imágenes.

---

## Vídeos

Modelo:
OpenCLIP

Motivo:
Se reutiliza el mismo pipeline que para imágenes.

---

## Localización

Modelo:
Florence-2

Motivo:
Permite localizar cualquier objeto descrito por el usuario mediante Grounding.

---

## OCR

Modelo:
PaddleOCR

Motivo:
Extracción precisa de texto en imágenes y documentos escaneados.

---

## Modelo multimodal

Modelo:
Qwen2.5-VL-7B

Motivo:
Razonamiento multimodal sobre texto e imágenes.

---

## Base vectorial

ChromaDB

Motivo:
Almacenamiento eficiente de embeddings y recuperación semántica.

---

## Framework

LangChain

Motivo:
Orquestación del flujo RAG y de las herramientas del sistema.