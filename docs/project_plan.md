# Plan de desarrollo del TFM

## Título provisional

**Sistema inteligente para la búsqueda semántica, comparación y consulta de colecciones documentales mediante modelos de lenguaje y bases de datos vectoriales**

## Objetivo

Desarrollar una plataforma de análisis documental capaz de procesar archivos PDF, DOCX y TXT, extraer y fragmentar su contenido, generar representaciones vectoriales con un modelo BGE y almacenarlas en ChromaDB. El sistema permitirá realizar búsquedas semánticas y formular preguntas sobre la colección mediante una arquitectura RAG, mostrando las fuentes utilizadas para generar cada respuesta.

## Alcance

El proyecto se limita al análisis de documentos. No incluye módulos independientes de análisis de imágenes o vídeos.

El corpus principal está formado por 162 documentos PDF de OSHA. Tras el procesamiento actual, se dispone de 5.143 chunks representados mediante embeddings de 768 dimensiones generados con `BAAI/bge-base-en-v1.5`.

## Cambios respecto al plan inicial

- Se eliminan las fases independientes de imágenes, vídeos, OpenCLIP, Florence-2 y Qwen2.5-VL.
- Se conserva la arquitectura documental ya desarrollada con BGE, ChromaDB y RAG.
- Se añaden fases de auditoría del corpus, evaluación cuantitativa, comparación documental y control de calidad de las respuestas.
- El posible OCR de PDF escaneados queda como mejora opcional dentro del procesamiento documental, no como una modalidad independiente.

## Arquitectura del sistema

1. Ingesta de documentos PDF, DOCX y TXT.
2. Extracción y limpieza del texto.
3. División del texto en chunks con metadatos de procedencia.
4. Generación de embeddings mediante BGE.
5. Almacenamiento y consulta de vectores en ChromaDB.
6. Recuperación de los fragmentos más relevantes para cada pregunta.
7. Generación de respuestas mediante un modelo de lenguaje local.
8. Presentación de la respuesta junto con los documentos fuente.

---

## Fase 1 - Base documental

- [x] Configurar la estructura del proyecto y el entorno virtual.
- [x] Implementar la lectura de archivos PDF, DOCX y TXT.
- [x] Extraer y limpiar el texto de los documentos.
- [x] Implementar el chunking y conservar los metadatos de cada fragmento.
- [x] Crear una primera versión con `all-MiniLM-L6-v2`.
- [x] Sustituir el modelo inicial por `BAAI/bge-base-en-v1.5`.
- [x] Regenerar los embeddings con 768 dimensiones.
- [x] Almacenar 5.143 chunks en ChromaDB.
- [x] Implementar la búsqueda semántica.
- [x] Implementar el chat RAG con un modelo de lenguaje local.
- [x] Mostrar las fuentes documentales recuperadas.

## Fase 2 - Preparación y control del corpus

- [x] Incorporar los 162 PDF de OSHA.
- [ ] Documentar el origen, la licencia y los derechos de uso del conjunto de datos.
- [ ] Identificar documentos repetidos o versiones duplicadas.
- [ ] Registrar el número de documentos originales, duplicados y documentos finales.
- [ ] Analizar la distribución de páginas, caracteres y chunks por documento.
- [ ] Explicar el criterio de limpieza y deduplicación aplicado.
- [ ] Añadir, solo si es necesario, documentos oficiales de OSHA para aumentar la diversidad temática del corpus.

## Fase 3 - Evaluación del sistema de recuperación

- [ ] Crear un conjunto de evaluación con preguntas y documentos relevantes esperados.
- [ ] Incluir preguntas de distintos temas presentes en el corpus.
- [ ] Medir `Precision@5`, `Recall@5`, `MRR` y tiempo medio de recuperación.
- [ ] Comparar los resultados de `all-MiniLM-L6-v2` y `BAAI/bge-base-en-v1.5`.
- [ ] Analizar al menos varios casos correctos y casos de fallo.
- [ ] Justificar con resultados la selección final de BGE.
- [ ] Guardar los resultados en CSV o JSON para que la evaluación sea reproducible.

## Fase 4 - Mejora y evaluación del RAG

- [ ] Ajustar el prompt para que el modelo responda únicamente con el contexto recuperado.
- [ ] Indicar expresamente cuando la colección no contiene información suficiente.
- [ ] Incorporar en cada respuesta el nombre del archivo y el identificador del chunk utilizado.
- [ ] Evitar que fragmentos duplicados ocupen varios puestos del `top-k`.
- [ ] Evaluar la relevancia, fidelidad y utilidad de las respuestas con una rúbrica definida.
- [ ] Medir el tiempo total de respuesta.
- [ ] Documentar ejemplos de respuestas correctas, incompletas y erróneas.

## Fase 5 - Comparación y análisis documental

- [ ] Calcular la similitud semántica entre documentos.
- [ ] Detectar documentos idénticos, casi duplicados o relacionados.
- [ ] Permitir seleccionar dos documentos para compararlos.
- [ ] Recuperar los fragmentos más semejantes y las diferencias principales.
- [ ] Generar un resumen de coincidencias y diferencias basado en evidencias.
- [ ] Evaluar manualmente varios pares conocidos de documentos.

## Fase 6 - Aplicación final

- [ ] Crear una interfaz sencilla en Streamlit.
- [ ] Permitir cargar o seleccionar documentos.
- [ ] Añadir una vista de búsqueda semántica.
- [ ] Añadir una vista de preguntas y respuestas con fuentes.
- [ ] Añadir una vista de comparación documental.
- [ ] Mostrar las métricas principales del sistema.
- [ ] Gestionar errores y consultas sin resultados.
- [ ] Optimizar los tiempos de carga y consulta.
- [ ] Añadir Docker únicamente si el tiempo disponible lo permite.

## Fase 7 - Validación, documentación y entrega

- [ ] Ejecutar el flujo completo desde la ingesta hasta la respuesta final.
- [ ] Comprobar la reproducibilidad en un entorno limpio.
- [ ] Actualizar `README.md` con instalación, arquitectura y ejemplos de uso.
- [ ] Organizar el código y añadir comentarios donde sean necesarios.
- [ ] Preparar tablas y figuras con los resultados de la evaluación.
- [ ] Redactar la memoria técnica de un máximo de 20 caras.
- [ ] Incluir conclusiones, limitaciones y líneas de trabajo futuro.
- [ ] Añadir una bibliografía breve y las referencias del conjunto de datos y de los modelos.
- [ ] Incluir el código y los estudios detallados como anexos o mediante un repositorio accesible.
- [ ] Grabar un vídeo MP4 de un máximo de 5 minutos con enfoque, demostración, resultados, conclusiones y lecciones aprendidas.
- [ ] Verificar que los tutores tengan acceso a todos los archivos y enlaces entregados.


## Criterio de finalización del proyecto

El proyecto se considerará terminado cuando otra persona pueda instalarlo siguiendo el README, procesar una colección documental, realizar una búsqueda, formular una pregunta, consultar las fuentes y reproducir las métricas de evaluación. La prioridad es demostrar y medir correctamente el sistema documental; Docker y el OCR de documentos escaneados se consideran mejoras opcionales y no deben retrasar la entrega principal.
