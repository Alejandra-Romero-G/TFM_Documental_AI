# Sistema inteligente para la búsqueda semántica, comparación y consulta de colecciones documentales mediante IA generativa y bases vectoriales

## Descripción

Este proyecto corresponde al Trabajo Fin de Máster en Big Data, Data Science e Inteligencia Artificial.

Su objetivo es desarrollar un sistema capaz de procesar, indexar y consultar colecciones documentales mediante técnicas de procesamiento del lenguaje natural, modelos de embeddings, bases de datos vectoriales y Recuperación Aumentada por Generación (RAG).

La aplicación permite recuperar fragmentos relevantes a partir de una consulta en lenguaje natural y generar una respuesta fundamentada en el contenido de los documentos. Cada respuesta puede acompañarse de las fuentes utilizadas, lo que facilita su revisión y reduce el riesgo de generar información no respaldada por el corpus.

El alcance actual es exclusivamente documental. El proyecto no incluye análisis independiente de imágenes o vídeos.

## Funcionalidades

### Implementadas

- Lectura de documentos PDF, DOCX y TXT.
- Extracción y limpieza del texto.
- División del contenido en chunks con metadatos de procedencia.
- Generación de embeddings documentales con `BAAI/bge-base-en-v1.5`.
- Almacenamiento persistente de embeddings en ChromaDB.
- Búsqueda semántica por similitud.
- Recuperación de los fragmentos más relevantes para cada consulta.
- Generación de respuestas mediante un pipeline RAG local.
- Uso de `Qwen/Qwen2.5-1.5B-Instruct` como modelo generativo.
- Presentación de los documentos y chunks utilizados como fuentes.
- Evaluación inicial del retrieval mediante `Precision@5`.

### Pendientes

- Ampliar el conjunto de preguntas de evaluación.
- Calcular `Recall@5`, `MRR` y tiempos medios de consulta.
- Comparar los resultados de BGE con `all-MiniLM-L6-v2` como baseline.
- Detectar documentos idénticos o casi duplicados.
- Implementar la comparación semántica entre documentos.
- Crear una interfaz en Streamlit.
- Incorporar OCR únicamente para PDF escaneados que no contengan texto extraíble.
- Preparar Docker como mejora opcional.

## Corpus documental

El corpus principal está formado por 162 documentos PDF relacionados con seguridad y salud laboral, recopilados a partir del conjunto [All OSHA PDF de Kaggle](https://www.kaggle.com/datasets/aminhaghiii/all-osha-pdf?resource=download).

Los documentos proceden de publicaciones de la [Occupational Safety and Health Administration (OSHA)](https://www.osha.gov/publications/all) y están redactados principalmente en inglés. Incluyen contenidos sobre prevención de riesgos laborales, exposición a sustancias peligrosas, equipos de protección, estrés térmico y otras materias de salud ocupacional.

Tras el procesamiento actual, el corpus contiene 5.143 chunks almacenados en ChromaDB. Cada chunk está representado mediante un embedding de 768 dimensiones generado con `BAAI/bge-base-en-v1.5`.

Los documentos no se utilizan para entrenar los modelos desde cero. Funcionan como base de conocimiento para la recuperación de información y la generación de respuestas mediante RAG.

## Arquitectura

El sistema sigue el siguiente flujo:

1. Carga de documentos desde `data/documents`.
2. Extracción y limpieza del texto.
3. División del contenido en chunks.
4. Generación de embeddings mediante BGE.
5. Almacenamiento de vectores, texto y metadatos en ChromaDB.
6. Conversión de la pregunta del usuario en un embedding.
7. Recuperación de los chunks más cercanos semánticamente.
8. Construcción del contexto para el modelo de lenguaje.
9. Generación de una respuesta con `Qwen/Qwen2.5-1.5B-Instruct`.
10. Presentación de la respuesta y sus fuentes documentales.

## Tecnologías

| Tecnología | Uso en el proyecto |
| --- | --- |
| Python | Desarrollo del pipeline documental |
| Sentence Transformers | Generación de embeddings con BGE y MiniLM |
| `BAAI/bge-base-en-v1.5` | Modelo principal de embeddings, con vectores de 768 dimensiones |
| Hugging Face Transformers | Carga y ejecución del modelo generativo local |
| `Qwen/Qwen2.5-1.5B-Instruct` | Generación de respuestas a partir del contexto recuperado |
| ChromaDB | Almacenamiento persistente y búsqueda vectorial |
| Streamlit | Interfaz prevista; todavía no implementada |
| PaddleOCR | Mejora opcional para documentos escaneados |

El proyecto utiliza un pipeline modular propio en Python. LangChain no forma parte de la arquitectura actual.

## Estructura del proyecto

```text
TFM_DOCUMENTAL_AI/
├── data/
│   ├── documents/
│   │   └── osha/
│   └── chroma/
├── docs/
├── evidencias/
├── src/
│   ├── analysis/
│   ├── embeddings/
│   ├── llm/
│   ├── loaders/
│   ├── retrieval/
│   └── vector_db/
├── tests/
├── ask.py
├── main.py
├── README.md
└── requirements.txt
```

## Requisitos

- Python 3.11 o superior.
- Memoria suficiente para ejecutar localmente los modelos de embeddings y generación.
- No es obligatorio disponer de GPU; el proyecto puede ejecutarse en CPU, aunque la generación de respuestas será más lenta.

El entorno utilizado durante el desarrollo dispone de aproximadamente 32 GB de RAM y no utiliza CUDA.

## Instalación

### 1. Clonar el repositorio

```powershell
git clone <URL_DEL_REPOSITORIO>
cd TFM_Multimodal_AI
```

Sustituye `<URL_DEL_REPOSITORIO>` por la dirección real del repositorio de GitHub.

### 2. Crear y activar un entorno virtual

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
```

### 3. Instalar las dependencias

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Preparación de los documentos

Los documentos deben almacenarse en:

```text
data/documents/osha/
```

Para comprobar la carga y el procesamiento documental puede utilizarse:

```powershell
python -m src.loaders.text_loader
```

La generación de embeddings debe ejecutarse cuando se añadan documentos nuevos, se modifique el chunking o se cambie el modelo de embeddings. No se deben mezclar en una misma colección vectores de MiniLM, de 384 dimensiones, con vectores de BGE, de 768 dimensiones.

## Ejecución

Para ejecutar el flujo principal:

```powershell
python main.py
```

Para realizar una consulta mediante el sistema RAG:

```powershell
python ask.py
```

Debido a que los documentos de OSHA están principalmente en inglés, las preguntas de evaluación se formulan inicialmente en ese idioma.

## Evaluación del retrieval

La evaluación inicial puede ejecutarse mediante:

```powershell
python tests/evaluate_retrieval.py
```

La primera métrica utilizada es `Precision@5`, calculada como:

```text
Precision@5 = número de resultados relevantes entre los cinco primeros / 5
```

Esta métrica constituye una evaluación inicial. Para la versión final se incorporarán un conjunto de preguntas con relevancia esperada, `Recall@5`, `MRR`, tiempos de consulta y un análisis de casos correctos y fallidos.

## Estado del proyecto

| Componente | Estado |
| --- | --- |
| Ingesta de PDF, DOCX y TXT | Completado |
| Extracción y chunking | Completado |
| Embeddings con BGE | Completado |
| Persistencia en ChromaDB | Completado |
| Búsqueda semántica | Completado |
| Chat RAG local | Completado |
| Evaluación inicial `Precision@5` | Completado |
| Evaluación ampliada | En desarrollo |
| Comparación documental | Pendiente |
| Interfaz Streamlit | Pendiente |
| OCR | Opcional |
| Docker | Opcional |

## Limitaciones actuales

- El corpus puede contener documentos repetidos o versiones diferentes de una misma publicación.
- La calidad de las respuestas depende de los chunks recuperados.
- El modelo generativo puede producir respuestas incompletas si el contexto no contiene información suficiente.
- La ejecución del modelo de lenguaje en CPU puede ser lenta.
- Los PDF escaneados sin capa de texto todavía no pueden procesarse mediante OCR.
- La evaluación actual debe ampliarse para justificar cuantitativamente la selección de BGE.

## Reproducibilidad

Para reproducir el proyecto se deben conservar:

- La versión de las dependencias en `requirements.txt`.
- La referencia al conjunto de datos utilizado.
- Los parámetros de chunking.
- El identificador de los modelos de embeddings y generación.
- La configuración de ChromaDB.
- Las preguntas, etiquetas de relevancia y resultados de evaluación.

## Uso de los datos

Kaggle funciona como plataforma de recopilación y descarga. La procedencia institucional de los documentos debe atribuirse a OSHA. Antes de distribuir los PDF junto con el repositorio se deben revisar las condiciones de uso indicadas en el conjunto de Kaggle y en las publicaciones originales.

## Objetivo final

El resultado final será un prototipo reproducible capaz de procesar una colección documental, recuperar información relevante, responder preguntas con apoyo en las fuentes y comparar documentos mediante técnicas de inteligencia artificial y bases de datos vectoriales.
