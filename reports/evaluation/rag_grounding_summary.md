# Grounded RAG generation evaluation

- Generated at: 2026-09-01T13:47:51+02:00
- Local LLM: `Qwen/Qwen2.5-3B-Instruct`
- Cases: 6
- Sources requested per case: 3

## Aggregate metrics

- Non-empty answer rate: 100.00%
- Document isolation rate: 100.00%
- Source-label presence rate: 100.00%
- Valid source-label rate: 100.00%
- Mean expected-concept coverage: 95.00%
- Abstention success rate: 100.00%
- Automatic acceptance rate: 100.00%
- Mean end-to-end latency: 113.92 seconds

## Results by case

| Case | File | Isolation | Valid labels | Concept coverage | Abstention | Pass | Latency |
|---|---|---:|---:|---:|---:|---:|---:|
| RAG01 | 2016-106.pdf | 1 | 1 | 75.00% | 0 | 1 | 121.20 s |
| RAG02 | 2014-108.pdf | 1 | 1 | 100.00% | 0 | 1 | 137.46 s |
| RAG03 | OSHA3902.pdf | 1 | 1 | 100.00% | 0 | 1 | 133.44 s |
| RAG04 | 99-112.pdf | 1 | 1 | 100.00% | 0 | 1 | 125.20 s |
| RAG05 | OSHA3151.pdf | 1 | 1 | 100.00% | 0 | 1 | 100.86 s |
| RAG06 | 2010-114.pdf | 1 | 1 | 100.00% | 1 | 1 | 65.35 s |

## Generated answers

### RAG01 - 2016-106.pdf

Question: What should employers do to protect workers from occupational heat stress?

ANSWER:
Employers should provide a heat stress training program that effectively trains all workers and supervisors about the following:

[1] Recognition of the signs and symptoms of the various types of heat-related illnesses and in administration of first aid.
[1] The causes of heat-related illnesses and the personal care procedures that will minimize the risk of their occurrence, such as drinking enough water and monitoring the color and amount of urine output.
[1] The proper care and use of heat-protective clothing and equipment and the added heat load caused by exertion, clothing, and personal protective equipment.
[1] The effects of nonoccupational factors (drugs, alcohol, obesity, etc.) on tolerance to occupational heat stress.
[1] The importance of acclimatization.
[1] The importance of immediately reporting to the supervisor any symptoms or signs of heat-related illness in themselves or in their coworkers.
[1] The employer’s procedures for responding to symptoms of possible heat-related illness and for contacting emergency medical services if needed.

SOURCES USED:
[S1], [S2], [S3]

### RAG02 - 2014-108.pdf

Question: How can roof parapets help prevent falls during construction and maintenance?

ANSWER:
- Roof parapets can prevent falls from low-sloped roofs during construction and maintenance tasks [S1].
- Properly designed parapets (39 inches or taller) can eliminate the need for additional fall arrest roof anchors, temporary barricades, or signs during operation and maintenance tasks [S1].
- Parapets can minimize costs associated with additional fall protection equipment and reduce the risk of falling during servicing and maintenance operations [S2].
- Parapets can reduce wind flow over the roof, distribute wind uplift resistance evenly, and help prevent rainwater damage on the exterior of buildings [S2].
- Parapets can serve as a barrier to prevent workers from approaching roof edges too closely, thereby reducing the risk of falls [S1].
- Parapets can be used as anchorage points for personal fall arrest systems and support for window-washing scaffolds [S3].

SOURCES USED:
[S1], [S2], [S3]

### RAG03 - OSHA3902.pdf

Question: What measures should construction employers use to control respirable crystalline silica exposure?

ANSWER:
- Employers must avoid certain housekeeping practices such as dry brushing, dry sweeping, and cleaning with compressed air, unless alternative methods like wet sweeping and HEPA-filtered vacuuming are not feasible.
- Employers are required to use other cleaning methods such as wet sweeping and HEPA-filtered vacuums, whenever feasible, to reduce employee exposures by preventing silica-containing dust from getting into the air.
- Employers should schedule work so that tasks involving high exposures are performed when no other employees are in the area.
- Employers should use the hierarchy of controls, prioritizing engineering controls over respirators, due to their reliability, predictability, and consistency in providing protection.

SOURCES USED:
[S1], [S2]

### RAG04 - 99-112.pdf

Question: How can workers control chemical hazards when applying artificial fingernails?

ANSWER:
- Apply artificial fingernails at a ventilated work table [S1].
- Keep all bottles of fingernail liquid tightly capped [S1].
- Improve work habits to reduce exposure [S1].
- Wash hands, arms, and face with mild soap and water several times throughout the day [S2].
- Wear personal protective clothing and glasses [S2].
- Remove potentially irritating dust by washing hands, arms, and face [S2].
- Ban smoking in the entire salon [S2].
- Avoid eating and drinking where artificial fingernails are applied or in other working areas [S2].

SOURCES USED:
[S1], [S2], [S3]

### RAG05 - OSHA3151.pdf

Question: How should employers assess hazards and select personal protective equipment?

ANSWER:
- Employers should conduct a hazard assessment to identify physical and health hazards in the workplace [S3].
- After identifying hazards, employers should select appropriate personal protective equipment (PPE) based on the identified hazards [S1].

SOURCES USED:
- S1, S3

### RAG06 - 2010-114.pdf

Question: What encryption algorithm and password length does this document require for cybersecurity systems?

ANSWER:
- This document does not specify any encryption algorithm or password length requirement for cybersecurity systems. [S1]

SOURCES USED:
- [S1]

## Interpretation and limitations

- Document isolation verifies that retrieval obeyed the selected canonical document ID.
- Valid source-label rate verifies label syntax and range, not whether every claim is fully entailed.
- Concept coverage is a deterministic lexical proxy using accepted synonym groups.
- Generated answers still require manual factual review against the cited page evidence.
- The system performs documentary analysis and does not determine legal compliance.
