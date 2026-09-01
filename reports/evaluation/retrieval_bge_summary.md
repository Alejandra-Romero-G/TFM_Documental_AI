# BGE retrieval evaluation

- Generated at: 2026-09-01T13:23:18+02:00
- Collection: `documents_bge_base_v1_5`
- Indexed chunks: 8828
- Embedding model: `BAAI/bge-base-en-v1.5`
- Evaluation queries: 11
- Retrieval depth: 5 documents

## Aggregate metrics

- Hit@1: 90.91%
- Hit@3: 100.00%
- Hit@5: 100.00%
- MRR@5: 0.9545
- Mean document Precision@5: 0.2364
- Maximum attainable mean Precision@5 with the annotated relevant set: 0.2364
- Normalized Precision@5: 1.0000
- Mean document Recall@5: 1.0000
- Mean retrieval latency: 0.0927 seconds

## Results by query

| ID | Category | First relevant rank | Hit@1 | Hit@3 | Hit@5 | Top result |
|---|---|---:|---:|---:|---:|---|
| Q01 | heat_monitoring | 1 | 1 | 1 | 1 | cdc_115958_DS1.pdf |
| Q02 | occupational_heat | 1 | 1 | 1 | 1 | 2016-106.pdf |
| Q03 | work_schedules | 1 | 1 | 1 | 1 | 2016-106.pdf |
| Q04 | heat_first_aid | 1 | 1 | 1 | 1 | 2010-114.pdf |
| Q05 | construction_falls | 2 | 0 | 1 | 1 | 2014-108.pdf |
| Q06 | embedded_safety | 1 | 1 | 1 | 1 | 2014-124.pdf |
| Q07 | prevention_through_design | 1 | 1 | 1 | 1 | 2024-124.pdf |
| Q08 | roof_parapets | 1 | 1 | 1 | 1 | 2014-108.pdf |
| Q09 | silica | 1 | 1 | 1 | 1 | OSHA3902.pdf |
| Q10 | chemical_hazards | 1 | 1 | 1 | 1 | 99-112.pdf |
| Q11 | ppe | 1 | 1 | 1 | 1 | OSHA3151.pdf |

## Method

Queries were evaluated with the production BGE query instruction, ChromaDB collection and RAG retrieval function. Results were deduplicated at document level by allowing one chunk per PDF.

## Limitations

- The benchmark contains manually curated queries for eleven NIOSH and OSHA publications.
- Relevance is defined from documentary titles and known subject matter, not from legal judgments.
- Most queries have one annotated relevant document. Therefore raw Precision@5 cannot reach 1.0; normalized Precision@5 compares it with the annotated maximum.
- These metrics evaluate retrieval ranking and do not measure factual quality of generated answers.
