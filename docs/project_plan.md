# Plan de Desarrollo del TFM

## Objetivo

Desarrollar una plataforma multimodal capaz de analizar documentos, imágenes y vídeos utilizando modelos de IA generativa y bases de datos vectoriales.

---

# Fase 1 - Base documental

- [ ] Configuración del proyecto
- [ ] Lectura de PDF, DOCX y TXT
- [ ] Extracción de texto
- [ ] Chunking
- [ ] Embeddings con all-MiniLM-L6-v2
- [ ] ChromaDB
- [ ] Búsqueda semántica
- [ ] Chat RAG

---

# Fase 2 - Imágenes

- [ ] Integrar OpenCLIP
- [ ] Generar embeddings de imágenes
- [ ] Almacenar embeddings
- [ ] Recuperación semántica de imágenes

---

# Fase 3 - Vídeos

- [ ] Extracción de fotogramas
- [ ] Embeddings con OpenCLIP
- [ ] Recuperación de vídeos

---

# Fase 4 - Localización visual

- [ ] Integrar Florence-2
- [ ] Localización de objetos
- [ ] Mostrar bounding boxes

---

# Fase 5 - IA Multimodal

- [ ] Integrar Qwen2.5-VL
- [ ] Respuestas multimodales
- [ ] Comparación entre documentos e imágenes
- [ ] Comparación entre imágenes y vídeos

---

# Fase 6 - Aplicación final

- [ ] Interfaz en Streamlit
- [ ] Historial de consultas
- [ ] Optimización
- [ ] Docker
- [ ] Memoria del TFM