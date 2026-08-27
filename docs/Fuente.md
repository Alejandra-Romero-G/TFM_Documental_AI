## Fuente de documentos

### Conjunto de datos

**All OSHA PDF**

* **Plataforma de descarga:** Kaggle
* **Autor de la recopilación:** usuario `aminhaghiii`
* **Enlace:** [All OSHA PDF - Kaggle](https://www.kaggle.com/datasets/aminhaghiii/all-osha-pdf?resource=download)
* **Fuente institucional de los documentos:** [Occupational Safety and Health Administration (OSHA)](https://www.osha.gov/publications/all)
* **Idioma predominante:** inglés
* **Número de documentos utilizados:** 162 archivos PDF
* **Fecha de consulta:** 6 de agosto de 2026

### Descripción

El conjunto de datos consiste en una recopilación de documentos publicados por la Occupational Safety and Health Administration (OSHA), organismo perteneciente al Departamento de Trabajo de Estados Unidos. Los archivos contienen información relacionada con la prevención de riesgos laborales, la seguridad en el trabajo, la exposición a sustancias peligrosas, el estrés térmico, los equipos de protección y otros temas de salud ocupacional.

En este proyecto se descargaron 162 documentos PDF. Estos archivos constituyen el corpus documental sobre el que se realizan la extracción y limpieza del texto, la división en chunks, la generación de embeddings con `BAAI/bge-base-en-v1.5` y el almacenamiento en ChromaDB. Posteriormente, el sistema utiliza estos fragmentos para realizar búsquedas semánticas y generar respuestas mediante una arquitectura RAG.

Los documentos no se utilizan para entrenar desde cero ni para ajustar los modelos empleados. BGE y el modelo generativo son modelos preentrenados; el corpus de OSHA se utiliza únicamente como base de conocimiento documental para la recuperación de información y la generación de respuestas fundamentadas.

### Calidad y limitaciones

El conjunto de datos puede contener documentos repetidos, distintas versiones de una misma publicación y archivos con formatos o extensiones variables. Por este motivo, antes de la indexación definitiva se debe realizar una auditoría del corpus para identificar duplicados, comprobar la legibilidad de los PDF y registrar el número final de documentos únicos.

Kaggle funciona como plataforma de recopilación y descarga, pero la procedencia institucional debe atribuirse a OSHA. También se deben revisar y documentar por separado las condiciones de uso indicadas en Kaggle y en las publicaciones originales.
