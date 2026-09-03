# Fuentes documentales y derechos de uso

## 1. Composición del corpus

El corpus utilizado en el proyecto está formado por **173 archivos PDF**, obtenidos de dos grupos de fuentes:

| Grupo de documentos | Procedencia | Archivos utilizados |
|---|---|---:|
| Recopilación inicial | Conjunto de datos *All OSHA PDF* disponible en Kaggle | 162 |
| Adiciones oficiales | Publicaciones descargadas desde páginas oficiales de NIOSH y OSHA | 11 |
| **Total** |  | **173** |

El idioma predominante es el inglés y la temática común es la seguridad y la salud en el trabajo. El corpus incluye publicaciones sobre estrés térmico, caídas en construcción, exposición a sílice y otras sustancias químicas, equipos de protección personal, preparación ante emergencias y prevención de riesgos laborales.

## 2. Recopilación inicial de Kaggle

### Identificación

- **Nombre:** *All OSHA PDF*.
- **Plataforma de descarga:** Kaggle.
- **Autor de la recopilación:** usuario `aminhaghiii`.
- **Enlace:** [All OSHA PDF - Kaggle](https://www.kaggle.com/datasets/aminhaghiii/all-osha-pdf?resource=download).
- **Referencia institucional principal:** [Occupational Safety and Health Administration (OSHA)](https://www.osha.gov/publications/all).
- **Archivos disponibles localmente y utilizados:** 162 PDF.
- **Fecha de consulta:** 6 de agosto de 2026.

El catálogo del conjunto de datos contiene 174 registros, pero el corpus local empleado en el proyecto está formado por 162 archivos PDF procedentes de esta recopilación. Por tanto, las métricas de auditoría se calculan sobre los archivos realmente disponibles y no sobre el número de registros del catálogo.

Kaggle actúa como plataforma de recopilación y descarga. Aunque el conjunto se presenta como una colección de documentos de OSHA, la procedencia institucional y las condiciones de uso no se verificaron individualmente para todos los archivos de esta parte del corpus. En consecuencia, no se presupone que cada PDF sea de dominio público por el mero hecho de aparecer en la colección.

## 3. Adiciones oficiales de NIOSH y OSHA

Para ampliar la variedad temática y disponer de documentos con una procedencia mejor documentada, se añadieron **11 publicaciones oficiales** descargadas el 27 de agosto de 2026:

- 9 publicaciones de NIOSH;
- 2 publicaciones de OSHA.

Estas adiciones incluyen documentos sobre estrés térmico, prevención de caídas, exposición a sílice, riesgos químicos y equipos de protección personal. Para cada publicación se registraron, cuando estaban disponibles, el título, la organización, el año, el tema, la página oficial, el enlace al PDF, el estado de derechos, la evidencia correspondiente y la fecha de descarga.

El inventario detallado se conserva en `evidencias/reports/documents_Niosh.csv`. Aunque el nombre del archivo se mantuvo por continuidad con el proceso de recopilación, el inventario incluye también las dos publicaciones oficiales de OSHA.

## 4. Auditoría y selección del corpus canónico

Antes de construir el índice vectorial se ejecutó una auditoría reproducible sobre los 173 PDF. Los resultados fueron:

| Métrica | Resultado |
|---|---:|
| PDF analizados | 173 |
| Duplicados binarios exactos | 93 |
| Duplicados adicionales por texto normalizado | 0 |
| Registros con problemas de extracción o posible necesidad de OCR | 4 |
| Documentos canónicos con texto utilizable | 78 |

Los cuatro registros con problemas de extracción corresponden a dos documentos únicos sin texto extraíble y a sus respectivas copias exactas. Los duplicados no se eliminaron físicamente del corpus original; se identificaron mediante SHA-256 y se excluyeron de la indexación canónica.

Los resultados pueden consultarse en:

- `reports/corpus_audit.csv`: inventario completo de los 173 PDF;
- `reports/canonical_documents.csv`: manifiesto de los 78 documentos canónicos;
- `reports/exact_duplicates.csv`: duplicados binarios exactos;
- `reports/content_duplicates.csv`: duplicados detectados por texto normalizado;
- `reports/extraction_problems.csv`: archivos sin texto útil o con posible necesidad de OCR.

## 5. Uso de los documentos en el sistema

Los PDF no se utilizan para entrenar desde cero ni para ajustar los modelos. El corpus funciona exclusivamente como base de conocimiento documental para:

1. extraer el texto página por página;
2. dividirlo en fragmentos con metadatos de procedencia;
3. generar embeddings con `BAAI/bge-base-en-v1.5`;
4. almacenar y recuperar los fragmentos mediante ChromaDB;
5. responder preguntas con una arquitectura RAG;
6. comparar dos documentos;
7. realizar una preevaluación semántica de cobertura documental.

Tanto BGE como `Qwen/Qwen2.5-3B-Instruct` son modelos preentrenados. La aportación del proyecto se encuentra en la preparación y auditoría del corpus, la arquitectura de recuperación, la trazabilidad de las fuentes, los módulos de análisis y su evaluación.

## 6. Derechos de uso y redistribución

Las condiciones de uso se documentaron de forma diferenciada para la recopilación de Kaggle y para las publicaciones oficiales añadidas:

- La ficha de Kaggle utiliza una licencia de tipo «Other (specified in description)». Esta indicación no se interpreta como una autorización general para redistribuir todos los PDF ni como prueba de que cada archivo sea de dominio público.
- Varias publicaciones oficiales de NIOSH y OSHA contienen declaraciones de dominio público para el texto elaborado por el Gobierno de Estados Unidos.
- Algunas publicaciones incluyen fotografías, ilustraciones, logotipos u otros materiales de terceros que están expresamente excluidos de esas declaraciones y deben conservar su atribución.
- Las evidencias de derechos y las excepciones identificadas se almacenan en `evidencias/02_licencias/` y en los catálogos de fuentes.

Por prudencia, los PDF originales no se distribuyen en el repositorio público. El repositorio conserva únicamente el código, los metadatos, los hashes, los informes de auditoría y las evidencias necesarias para identificar las fuentes. Quien reproduzca el proyecto debe descargar los documentos desde sus páginas de origen y revisar las condiciones aplicables a cada publicación.

## 7. Limitaciones de procedencia

- No se verificó individualmente la página oficial de origen de todos los archivos incluidos en la recopilación de Kaggle.
- La clasificación temática de algunos documentos se obtuvo a partir de sus títulos y contenido extraído.
- La presencia de un documento en un sitio oficial no elimina automáticamente los derechos de terceros incorporados en fotografías, ilustraciones o logotipos.
- Los informes de auditoría describen el corpus local empleado en el experimento y no todo el contenido disponible actualmente en las fuentes externas.

Este registro proporciona trazabilidad sobre la procedencia y el uso académico del corpus, pero no constituye una interpretación jurídica de las licencias ni sustituye la comprobación de las condiciones de cada documento original.
