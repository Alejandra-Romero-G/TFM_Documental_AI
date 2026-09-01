import argparse
import csv
import re
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")


CANONICAL_CSV = (
    PROJECT_ROOT
    / "reports"
    / "canonical_documents.csv"
)

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "reports"
    / "evaluation"
)

RESULTS_CSV = (
    OUTPUT_DIRECTORY
    / "rag_grounding_results.csv"
)

SUMMARY_MD = (
    OUTPUT_DIRECTORY
    / "rag_grounding_summary.md"
)

N_RESULTS = 3
LOCAL_LLM_NAME = "Qwen/Qwen2.5-3B-Instruct"


CASES = [
    {
        "id": "RAG01",
        "file_name": "2016-106.pdf",
        "question": (
            "What should employers do to protect workers "
            "from occupational heat stress?"
        ),
        "concept_groups": [
            ["training", "train"],
            ["water", "hydration", "hydrate"],
            ["rest", "break", "work/rest"],
            ["acclimatization", "acclimatize"]
        ],
        "expected_abstention": False
    },
    {
        "id": "RAG02",
        "file_name": "2014-108.pdf",
        "question": (
            "How can roof parapets help prevent falls "
            "during construction and maintenance?"
        ),
        "concept_groups": [
            ["parapet"],
            ["fall"],
            ["39", "height"]
        ],
        "expected_abstention": False
    },
    {
        "id": "RAG03",
        "file_name": "OSHA3902.pdf",
        "question": (
            "What measures should construction employers use "
            "to control respirable crystalline silica exposure?"
        ),
        "concept_groups": [
            ["silica"],
            ["exposure"],
            ["control", "engineering"]
        ],
        "expected_abstention": False
    },
    {
        "id": "RAG04",
        "file_name": "99-112.pdf",
        "question": (
            "How can workers control chemical hazards when "
            "applying artificial fingernails?"
        ),
        "concept_groups": [
            ["chemical", "exposure", "hazard"],
            ["fingernail", "nail"],
            ["ventilation", "ventilated", "exhaust"]
        ],
        "expected_abstention": False
    },
    {
        "id": "RAG05",
        "file_name": "OSHA3151.pdf",
        "question": (
            "How should employers assess hazards and select "
            "personal protective equipment?"
        ),
        "concept_groups": [
            ["hazard"],
            ["personal protective equipment", "ppe"],
            ["employer", "worker"]
        ],
        "expected_abstention": False
    },
    {
        "id": "RAG06",
        "file_name": "2010-114.pdf",
        "question": (
            "What encryption algorithm and password length does "
            "this document require for cybersecurity systems?"
        ),
        "concept_groups": [],
        "expected_abstention": True
    }
]


ABSTENTION_PATTERNS = [
    "not available in the provided",
    "not available in these documents",
    "not available in the documents",
    "does not contain",
    "do not contain",
    "does not specify",
    "not specified",
    "insufficient evidence",
    "insufficient information",
    "no esta disponible",
    "no contiene",
    "no contienen",
    "evidencia insuficiente"
]


def load_document_ids():
    """Loads canonical IDs for the evaluation files."""

    if not CANONICAL_CSV.exists():
        raise FileNotFoundError(
            f"Canonical manifest not found: {CANONICAL_CSV}"
        )

    with CANONICAL_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:
        rows = list(csv.DictReader(csv_file))

    ids_by_name = {
        row["file_name"]: row["canonical_document_id"]
        for row in rows
    }

    missing_files = [
        case["file_name"]
        for case in CASES
        if case["file_name"] not in ids_by_name
    ]

    if missing_files:
        raise ValueError(
            "Evaluation files missing from the manifest: "
            + ", ".join(missing_files)
        )

    return ids_by_name


def normalize_for_checks(text):
    """Normalizes generated text for automatic checks."""

    return (
        str(text)
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )


def calculate_concept_coverage(answer, concept_groups):
    """Calculates coverage using groups of accepted synonyms."""

    if not concept_groups:
        return 1.0, 0, 0

    normalized_answer = normalize_for_checks(answer)

    matched_groups = sum(
        any(
            normalize_for_checks(term) in normalized_answer
            for term in group
        )
        for group in concept_groups
    )

    return (
        matched_groups / len(concept_groups),
        matched_groups,
        len(concept_groups)
    )


def detect_abstention(answer):
    """Detects explicit insufficient-evidence responses."""

    normalized_answer = normalize_for_checks(answer)

    return any(
        pattern in normalized_answer
        for pattern in ABSTENTION_PATTERNS
    )


def evaluate_case(case, document_id):
    """Runs one grounded generation case."""

    from src.analysis.analyzer import analyze_documents

    started_at = time.perf_counter()

    result = analyze_documents(
        question=case["question"],
        n_results=N_RESULTS,
        document_ids=[document_id]
    )

    latency_seconds = (
        time.perf_counter()
        - started_at
    )

    answer = result.get("response", "").strip()
    sources = result.get("sources", [])

    source_document_ids = {
        source.get("document_id", "")
        for source in sources
    }

    unauthorized_ids = (
        source_document_ids
        - {document_id}
    )

    valid_labels = {
        f"[S{position}]"
        for position in range(
            1,
            len(sources) + 1
        )
    }

    cited_labels = set(
        re.findall(
            r"\[S\d+\]",
            answer
        )
    )

    invalid_labels = (
        cited_labels
        - valid_labels
    )

    concept_coverage, matched_concepts, total_concepts = (
        calculate_concept_coverage(
            answer,
            case["concept_groups"]
        )
    )

    abstention_detected = detect_abstention(
        answer
    )

    answer_nonempty = bool(answer)
    document_isolation = (
        bool(sources)
        and not unauthorized_ids
        and source_document_ids == {document_id}
    )
    citation_present = bool(cited_labels)
    citations_valid = (
        citation_present
        and not invalid_labels
    )

    if case["expected_abstention"]:
        semantic_condition = abstention_detected
    else:
        semantic_condition = (
            concept_coverage >= 2 / 3
        )

    automatic_pass = all(
        [
            answer_nonempty,
            document_isolation,
            citations_valid,
            semantic_condition
        ]
    )

    return {
        "case_id": case["id"],
        "file_name": case["file_name"],
        "document_id": document_id,
        "question": case["question"],
        "expected_abstention": int(
            case["expected_abstention"]
        ),
        "answer_nonempty": int(answer_nonempty),
        "source_count": len(sources),
        "document_isolation": int(document_isolation),
        "unauthorized_document_ids": "; ".join(
            sorted(unauthorized_ids)
        ),
        "valid_source_labels": "; ".join(
            sorted(valid_labels)
        ),
        "cited_source_labels": "; ".join(
            sorted(cited_labels)
        ),
        "citation_present": int(citation_present),
        "citations_valid": int(citations_valid),
        "invalid_source_labels": "; ".join(
            sorted(invalid_labels)
        ),
        "matched_concept_groups": matched_concepts,
        "total_concept_groups": total_concepts,
        "concept_coverage": concept_coverage,
        "abstention_detected": int(abstention_detected),
        "automatic_pass": int(automatic_pass),
        "latency_seconds": latency_seconds,
        "answer": answer
    }


def calculate_metrics(rows):
    """Calculates aggregate grounding metrics."""

    factual_rows = [
        row
        for row in rows
        if not row["expected_abstention"]
    ]

    abstention_rows = [
        row
        for row in rows
        if row["expected_abstention"]
    ]

    return {
        "cases": len(rows),
        "answer_nonempty_rate": statistics.mean(
            row["answer_nonempty"]
            for row in rows
        ),
        "document_isolation_rate": statistics.mean(
            row["document_isolation"]
            for row in rows
        ),
        "citation_presence_rate": statistics.mean(
            row["citation_present"]
            for row in rows
        ),
        "valid_citation_rate": statistics.mean(
            row["citations_valid"]
            for row in rows
        ),
        "mean_concept_coverage": statistics.mean(
            row["concept_coverage"]
            for row in factual_rows
        ),
        "abstention_success_rate": statistics.mean(
            row["abstention_detected"]
            for row in abstention_rows
        ),
        "automatic_pass_rate": statistics.mean(
            row["automatic_pass"]
            for row in rows
        ),
        "mean_latency_seconds": statistics.mean(
            row["latency_seconds"]
            for row in rows
        )
    }


def load_and_recalculate_saved_results():
    """Reuses generated answers and recalculates deterministic checks."""

    if not RESULTS_CSV.exists():
        raise FileNotFoundError(
            f"Previous RAG results not found: {RESULTS_CSV}"
        )

    with RESULTS_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:
        saved_rows = list(csv.DictReader(csv_file))

    rows_by_id = {
        row["case_id"]: row
        for row in saved_rows
    }

    missing_cases = [
        case["id"]
        for case in CASES
        if case["id"] not in rows_by_id
    ]

    if missing_cases:
        raise ValueError(
            "Previous results are missing cases: "
            + ", ".join(missing_cases)
        )

    integer_fields = [
        "answer_nonempty",
        "source_count",
        "document_isolation",
        "citation_present",
        "citations_valid"
    ]

    recalculated_rows = []

    for case in CASES:
        row = dict(
            rows_by_id[case["id"]]
        )

        for field_name in integer_fields:
            row[field_name] = int(
                row[field_name]
            )

        row["latency_seconds"] = float(
            row["latency_seconds"]
        )

        coverage, matched, total = (
            calculate_concept_coverage(
                row["answer"],
                case["concept_groups"]
            )
        )

        abstention_detected = detect_abstention(
            row["answer"]
        )

        row["expected_abstention"] = int(
            case["expected_abstention"]
        )
        row["matched_concept_groups"] = matched
        row["total_concept_groups"] = total
        row["concept_coverage"] = coverage
        row["abstention_detected"] = int(
            abstention_detected
        )

        if case["expected_abstention"]:
            semantic_condition = abstention_detected
        else:
            semantic_condition = coverage >= 2 / 3

        row["automatic_pass"] = int(
            all(
                [
                    row["answer_nonempty"],
                    row["document_isolation"],
                    row["citations_valid"],
                    semantic_condition
                ]
            )
        )

        recalculated_rows.append(row)

    return recalculated_rows


def write_results_csv(rows):
    """Writes detailed results including generated answers."""

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    with RESULTS_CSV.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)


def build_summary(rows, metrics):
    """Builds a Markdown grounding report."""

    generated_at = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    lines = [
        "# Grounded RAG generation evaluation",
        "",
        f"- Generated at: {generated_at}",
        f"- Local LLM: `{LOCAL_LLM_NAME}`",
        f"- Cases: {metrics['cases']}",
        f"- Sources requested per case: {N_RESULTS}",
        "",
        "## Aggregate metrics",
        "",
        (
            "- Non-empty answer rate: "
            f"{metrics['answer_nonempty_rate']:.2%}"
        ),
        (
            "- Document isolation rate: "
            f"{metrics['document_isolation_rate']:.2%}"
        ),
        (
            "- Source-label presence rate: "
            f"{metrics['citation_presence_rate']:.2%}"
        ),
        (
            "- Valid source-label rate: "
            f"{metrics['valid_citation_rate']:.2%}"
        ),
        (
            "- Mean expected-concept coverage: "
            f"{metrics['mean_concept_coverage']:.2%}"
        ),
        (
            "- Abstention success rate: "
            f"{metrics['abstention_success_rate']:.2%}"
        ),
        (
            "- Automatic acceptance rate: "
            f"{metrics['automatic_pass_rate']:.2%}"
        ),
        (
            "- Mean end-to-end latency: "
            f"{metrics['mean_latency_seconds']:.2f} seconds"
        ),
        "",
        "## Results by case",
        "",
        (
            "| Case | File | Isolation | Valid labels | "
            "Concept coverage | Abstention | Pass | Latency |"
        ),
        "|---|---|---:|---:|---:|---:|---:|---:|"
    ]

    for row in rows:
        lines.append(
            "| "
            f"{row['case_id']} | "
            f"{row['file_name']} | "
            f"{row['document_isolation']} | "
            f"{row['citations_valid']} | "
            f"{row['concept_coverage']:.2%} | "
            f"{row['abstention_detected']} | "
            f"{row['automatic_pass']} | "
            f"{row['latency_seconds']:.2f} s |"
        )

    lines.extend(
        [
            "",
            "## Generated answers",
            ""
        ]
    )

    for row in rows:
        lines.extend(
            [
                f"### {row['case_id']} - {row['file_name']}",
                "",
                f"Question: {row['question']}",
                "",
                row["answer"],
                ""
            ]
        )

    lines.extend(
        [
            "## Interpretation and limitations",
            "",
            (
                "- Document isolation verifies that retrieval obeyed "
                "the selected canonical document ID."
            ),
            (
                "- Valid source-label rate verifies label syntax and "
                "range, not whether every claim is fully entailed."
            ),
            (
                "- Concept coverage is a deterministic lexical proxy "
                "using accepted synonym groups."
            ),
            (
                "- Generated answers still require manual factual "
                "review against the cited page evidence."
            ),
            (
                "- The system performs documentary analysis and does "
                "not determine legal compliance."
            ),
            ""
        ]
    )

    return "\n".join(lines)


def print_case(row):
    """Prints one compact case result."""

    print("-" * 80)
    print(
        f"{row['case_id']} | "
        f"{row['file_name']}"
    )
    print(
        "Isolation:",
        bool(row["document_isolation"])
    )
    print(
        "Citations valid:",
        bool(row["citations_valid"])
    )
    print(
        "Concept coverage:",
        f"{row['concept_coverage']:.2%}"
    )
    print(
        "Abstention detected:",
        bool(row["abstention_detected"])
    )
    print(
        "Automatic pass:",
        bool(row["automatic_pass"])
    )
    print(
        "Latency:",
        f"{row['latency_seconds']:.2f} s"
    )


def parse_arguments():
    """Parses evaluation options."""

    parser = argparse.ArgumentParser(
        description=(
            "Evaluates grounded RAG generation and citations."
        )
    )

    parser.add_argument(
        "--reuse-results",
        action="store_true",
        help=(
            "Recalculates deterministic metrics from the existing "
            "CSV without running the local LLM again."
        )
    )

    return parser.parse_args()


def main():
    arguments = parse_arguments()

    print("=" * 80)
    print("GROUNDED RAG GENERATION EVALUATION")
    print("=" * 80)
    print("LLM:", LOCAL_LLM_NAME)
    print("Cases:", len(CASES))
    print("Sources per case:", N_RESULTS)

    if arguments.reuse_results:
        print("Mode: reuse existing generated answers")
        rows = load_and_recalculate_saved_results()

        for row in rows:
            print_case(row)

    else:
        print("Mode: run retrieval and local generation")
        ids_by_name = load_document_ids()
        rows = []

        for case in CASES:
            row = evaluate_case(
                case,
                ids_by_name[case["file_name"]]
            )
            rows.append(row)
            print_case(row)

    metrics = calculate_metrics(rows)

    write_results_csv(rows)

    summary = build_summary(
        rows,
        metrics
    )

    SUMMARY_MD.write_text(
        summary,
        encoding="utf-8"
    )

    print()
    print("=" * 80)
    print("AGGREGATE RAG METRICS")
    print("=" * 80)
    print(
        "Non-empty answers:",
        f"{metrics['answer_nonempty_rate']:.2%}"
    )
    print(
        "Document isolation:",
        f"{metrics['document_isolation_rate']:.2%}"
    )
    print(
        "Source-label presence:",
        f"{metrics['citation_presence_rate']:.2%}"
    )
    print(
        "Valid source labels:",
        f"{metrics['valid_citation_rate']:.2%}"
    )
    print(
        "Mean concept coverage:",
        f"{metrics['mean_concept_coverage']:.2%}"
    )
    print(
        "Abstention success:",
        f"{metrics['abstention_success_rate']:.2%}"
    )
    print(
        "Automatic acceptance:",
        f"{metrics['automatic_pass_rate']:.2%}"
    )
    print(
        "Mean end-to-end latency:",
        f"{metrics['mean_latency_seconds']:.2f} s"
    )
    print("Detailed CSV:", RESULTS_CSV.resolve())
    print("Summary report:", SUMMARY_MD.resolve())


if __name__ == "__main__":
    main()
