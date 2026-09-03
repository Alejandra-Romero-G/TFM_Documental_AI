# Modelos y tecnologías del proyecto

## Alcance

El proyecto utiliza modelos de procesamiento del lenguaje natural para analizar colecciones documentales. El sistema procesa archivos PDF, DOCX y TXT, genera embeddings de sus fragmentos, recupera el contenido más relevante y produce respuestas mediante una arquitectura RAG.

No se utilizan modelos independientes para imágenes o vídeos. El OCR se mantiene únicamente como una posible mejora para documentos escaneados.

---

## Embeddings documentales

### Modelo principal

`BAAI/bge-base-en-v1.5`

### Función en el sistema

Generar las representaciones vectoriales de los chunks documentales y de las consultas realizadas por el usuario.

### Motivo de selección

- Está especializado en recuperación semántica de textos.
- Produce embeddings de 768 dimensiones.
- Puede utilizarse como modelo preentrenado sin necesidad de entrenarlo desde cero.
- Es adecuado para los documentos en inglés del corpus de OSHA.
- Ofrece una base técnica más sólida para evaluar la calidad del retrieval.

### Estado

Implementado. Los 5.143 chunks actuales están almacenados en ChromaDB con embeddings generados mediante BGE.

---

## Modelo de referencia para la evaluación

### Modelo

`sentence-transformers/all-MiniLM-L6-v2`

### Función en el sistema

Actuar como baseline para comparar el rendimiento del sistema de recuperación frente a BGE.

### Motivo de inclusión

- Fue el primer modelo de embeddings utilizado en el proyecto.
- Es ligero y rápido en CPU.
- Permite justificar el cambio a BGE mediante métricas como `Precision@5`, `Recall@5`, `MRR` y tiempo de consulta.

### Estado

Sustituido como modelo principal. Se conserva únicamente como referencia experimental y comparativa.

---

## Modelo generativo del RAG

### Modelo

Modelo de lenguaje local cargado mediante Hugging Face Transformers.

> Antes de entregar la memoria, se debe sustituir esta descripción por el identificador exacto del modelo configurado en `src/llm/llm.py`.

### Función en el sistema

Generar una respuesta a partir de la pregunta del usuario y de los chunks recuperados por BGE desde ChromaDB.

### Motivo de selección

- Permite ejecutar el sistema localmente sin enviar los documentos a servicios externos.
- Es compatible con el entorno disponible sin GPU.
- Facilita la reproducibilidad del proyecto.
- Puede limitarse mediante el prompt para responder únicamente con el contexto documental recuperado.

### Estado

Implementado e integrado en el chat RAG.

---

## Base de datos vectorial

### Tecnología

ChromaDB

### Función en el sistema

Almacenar los embeddings, el texto de los chunks y sus metadatos, y recuperar los fragmentos más relevantes para cada consulta.

### Motivo de selección

- Permite almacenamiento persistente en local.
- Se integra directamente con Python.
- Facilita la búsqueda vectorial y el filtrado mediante metadatos.
- Es suficiente para el tamaño actual del corpus: 162 PDF y 5.143 chunks.

### Estado

Implementada mediante un cliente persistente y una colección documental.

---

## OCR de documentos escaneados

### Tecnología prevista

PaddleOCR

### Función en el sistema

Extraer texto de páginas escaneadas que no contengan una capa de texto utilizable.

### Motivo de selección

- Permite ampliar la ingesta a PDF formados por imágenes escaneadas.
- Se mantiene dentro del alcance documental porque su salida es texto.

### Estado

Opcional y no implementado en el sistema base. Solo debe incorporarse si se detectan documentos relevantes que el extractor actual no puede leer. No es necesario para completar la versión mínima defendible del TFM.

---

## Librerías y framework de implementación

### Sentence Transformers

Se utiliza para cargar BGE y MiniLM y generar los embeddings de documentos y consultas.

### Hugging Face Transformers

Se utiliza para cargar y ejecutar localmente el modelo generativo del RAG.

### ChromaDB

Se utiliza como cliente y base de datos vectorial persistente.

### Pipeline modular en Python

La orquestación se realiza mediante los módulos propios del proyecto:

- `src/loaders`: lectura y extracción de documentos.
- `src/embeddings`: generación de embeddings.
- `src/vector_db`: persistencia y búsqueda en ChromaDB.
- `src/retrieval`: recuperación del contexto.
- `src/analysis`: coordinación del análisis documental.
- `src/llm`: generación de respuestas.

LangChain no debe incluirse como tecnología del proyecto salvo que se encuentre realmente importado y utilizado en el código final. La arquitectura modular existente ya permite explicar y controlar directamente el flujo RAG.

### Streamlit

Tecnología prevista para construir una interfaz sencilla de búsqueda semántica, preguntas y respuestas con fuentes y comparación documental.

---

## Componentes eliminados del plan inicial

| Componente | Motivo de eliminación |
| --- | --- |
| OpenCLIP ViT-B/32 | El proyecto ya no genera embeddings de imágenes ni vídeos. |
| Extracción de fotogramas | Los vídeos están fuera del alcance documental. |
| Florence-2 | No se realizará localización visual ni se mostrarán bounding boxes. |
| Qwen2.5-VL-7B | No se necesita un modelo visión-lenguaje para analizar texto documental. |
| Comparación imagen-texto-vídeo | La comparación se realizará exclusivamente entre documentos. |

---

## Resumen de la arquitectura final

| Etapa | Modelo o tecnología | Estado |
| --- | --- | --- |
| Lectura documental | Loaders propios para PDF, DOCX y TXT | Implementado |
| Embeddings principales | `BAAI/bge-base-en-v1.5` | Implementado |
| Baseline experimental | `all-MiniLM-L6-v2` | Sustituido; pendiente de comparación final |
| Base vectorial | ChromaDB | Implementado |
| Recuperación | Pipeline RAG propio en Python | Implementado |
| Generación de respuestas | Modelo local mediante Transformers | Implementado; falta registrar el identificador exacto |
| OCR | PaddleOCR | Opcional |
| Interfaz | Streamlit | Pendiente |

## Criterio para justificar los modelos en la memoria

La elección de los modelos no debe justificarse únicamente con expresiones como «excelente rendimiento». La memoria debe aportar:

1. El propósito de cada modelo dentro de la arquitectura.
2. Sus dimensiones, requisitos y condiciones de ejecución.
3. La razón por la que resulta adecuado para el corpus de OSHA.
4. Resultados medidos en el proyecto.
5. Limitaciones observadas y posibles mejoras futuras.

La decisión final entre MiniLM y BGE deberá apoyarse en los resultados del conjunto de evaluación, no únicamente en la reputación general de los modelos.
