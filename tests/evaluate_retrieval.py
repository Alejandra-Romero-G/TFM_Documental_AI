import csv
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.retrieval.rag import retrieve_context
from src.vector_db.chroma_db import get_collection_info
from tests.evaluation_questions import QUESTIONS


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
    / "retrieval_bge_results.csv"
)

SUMMARY_MD = (
    OUTPUT_DIRECTORY
    / "retrieval_bge_summary.md"
)

TOP_K = 5


def load_manifest():
    """Loads canonical document identifiers by file name."""

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

    return {
        row["file_name"]: row
        for row in rows
    }


def validate_questions(manifest_by_name):
    """Ensures every expected file belongs to the canonical corpus."""

    errors = []

    for item in QUESTIONS:
        for file_name in item["expected_files"]:
            if file_name not in manifest_by_name:
                errors.append(
                    f"{item['id']}: {file_name}"
                )

    if errors:
        raise ValueError(
            "Expected files missing from the canonical manifest: "
            + ", ".join(errors)
        )


def evaluate_question(item, manifest_by_name):
    """Evaluates one query using the production RAG retriever."""

    started_at = time.perf_counter()

    results = retrieve_context(
        query=item["question"],
        n_results=TOP_K,
        max_chunks_per_document=1
    )

    latency_seconds = (
        time.perf_counter()
        - started_at
    )

    retrieved_files = [
        result["file_name"]
        for result in results
    ]

    expected_files = set(
        item["expected_files"]
    )

    expected_ids = [
        manifest_by_name[file_name][
            "canonical_document_id"
        ]
        for file_name in item["expected_files"]
    ]

    relevant_ranks = [
        rank
        for rank, file_name in enumerate(
            retrieved_files,
            start=1
        )
        if file_name in expected_files
    ]

    first_relevant_rank = (
        min(relevant_ranks)
        if relevant_ranks
        else None
    )

    relevant_at_5 = len(
        relevant_ranks
    )

    precision_at_5 = (
        relevant_at_5
        / TOP_K
    )

    recall_at_5 = (
        relevant_at_5
        / len(expected_files)
    )

    reciprocal_rank = (
        1.0 / first_relevant_rank
        if first_relevant_rank is not None
        else 0.0
    )

    top_result = (
        results[0]
        if results
        else {}
    )

    return {
        "question_id": item["id"],
        "category": item["category"],
        "question": item["question"],
        "expected_files": "; ".join(
            item["expected_files"]
        ),
        "expected_document_ids": "; ".join(
            expected_ids
        ),
        "expected_document_count": len(
            expected_files
        ),
        "first_relevant_rank": (
            first_relevant_rank
            if first_relevant_rank is not None
            else ""
        ),
        "hit_at_1": int(
            first_relevant_rank == 1
        ),
        "hit_at_3": int(
            first_relevant_rank is not None
            and first_relevant_rank <= 3
        ),
        "hit_at_5": int(
            first_relevant_rank is not None
            and first_relevant_rank <= 5
        ),
        "reciprocal_rank": reciprocal_rank,
        "precision_at_5": precision_at_5,
        "recall_at_5": recall_at_5,
        "results_returned": len(results),
        "latency_seconds": latency_seconds,
        "top_1_file": top_result.get(
            "file_name",
            ""
        ),
        "top_1_document_id": top_result.get(
            "document_id",
            ""
        ),
        "top_1_distance": top_result.get(
            "distance",
            ""
        ),
        "retrieved_files": " | ".join(
            retrieved_files
        )
    }


def calculate_metrics(rows):
    """Calculates aggregate document-level retrieval metrics."""

    mean_precision_at_5 = statistics.mean(
        row["precision_at_5"]
        for row in rows
    )

    maximum_mean_precision_at_5 = statistics.mean(
        row["expected_document_count"]
        / TOP_K
        for row in rows
    )

    normalized_precision_at_5 = (
        mean_precision_at_5
        / maximum_mean_precision_at_5
        if maximum_mean_precision_at_5 > 0
        else 0.0
    )

    return {
        "queries": len(rows),
        "hit_at_1": statistics.mean(
            row["hit_at_1"]
            for row in rows
        ),
        "hit_at_3": statistics.mean(
            row["hit_at_3"]
            for row in rows
        ),
        "hit_at_5": statistics.mean(
            row["hit_at_5"]
            for row in rows
        ),
        "mrr_at_5": statistics.mean(
            row["reciprocal_rank"]
            for row in rows
        ),
        "mean_precision_at_5": mean_precision_at_5,
        "maximum_mean_precision_at_5": (
            maximum_mean_precision_at_5
        ),
        "normalized_precision_at_5": (
            normalized_precision_at_5
        ),
        "mean_recall_at_5": statistics.mean(
            row["recall_at_5"]
            for row in rows
        ),
        "mean_latency_seconds": statistics.mean(
            row["latency_seconds"]
            for row in rows
        )
    }


def write_results_csv(rows):
    """Exports detailed results in UTF-8 CSV format."""

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    fieldnames = list(
        rows[0].keys()
    )

    with RESULTS_CSV.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames
        )
        writer.writeheader()
        writer.writerows(rows)


def build_markdown_summary(rows, metrics, collection_info):
    """Builds a reproducible Markdown evaluation report."""

    generated_at = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    metadata = collection_info.get(
        "metadata",
        {}
    ) or {}

    lines = [
        "# BGE retrieval evaluation",
        "",
        f"- Generated at: {generated_at}",
        f"- Collection: `{collection_info.get('name', '')}`",
        f"- Indexed chunks: {collection_info.get('count', 0)}",
        (
            "- Embedding model: `"
            f"{metadata.get('embedding_model', '')}`"
        ),
        f"- Evaluation queries: {metrics['queries']}",
        f"- Retrieval depth: {TOP_K} documents",
        "",
        "## Aggregate metrics",
        "",
        f"- Hit@1: {metrics['hit_at_1']:.2%}",
        f"- Hit@3: {metrics['hit_at_3']:.2%}",
        f"- Hit@5: {metrics['hit_at_5']:.2%}",
        f"- MRR@5: {metrics['mrr_at_5']:.4f}",
        (
            "- Mean document Precision@5: "
            f"{metrics['mean_precision_at_5']:.4f}"
        ),
        (
            "- Maximum attainable mean Precision@5 with the "
            "annotated relevant set: "
            f"{metrics['maximum_mean_precision_at_5']:.4f}"
        ),
        (
            "- Normalized Precision@5: "
            f"{metrics['normalized_precision_at_5']:.4f}"
        ),
        (
            "- Mean document Recall@5: "
            f"{metrics['mean_recall_at_5']:.4f}"
        ),
        (
            "- Mean retrieval latency: "
            f"{metrics['mean_latency_seconds']:.4f} seconds"
        ),
        "",
        "## Results by query",
        "",
        (
            "| ID | Category | First relevant rank | "
            "Hit@1 | Hit@3 | Hit@5 | Top result |"
        ),
        "|---|---|---:|---:|---:|---:|---|"
    ]

    for row in rows:
        lines.append(
            "| "
            f"{row['question_id']} | "
            f"{row['category']} | "
            f"{row['first_relevant_rank'] or '-'} | "
            f"{row['hit_at_1']} | "
            f"{row['hit_at_3']} | "
            f"{row['hit_at_5']} | "
            f"{row['top_1_file']} |"
        )

    lines.extend(
        [
            "",
            "## Method",
            "",
            (
                "Queries were evaluated with the production BGE "
                "query instruction, ChromaDB collection and RAG "
                "retrieval function. Results were deduplicated at "
                "document level by allowing one chunk per PDF."
            ),
            "",
            "## Limitations",
            "",
            (
                "- The benchmark contains manually curated queries "
                "for eleven NIOSH and OSHA publications."
            ),
            (
                "- Relevance is defined from documentary titles and "
                "known subject matter, not from legal judgments."
            ),
            (
                "- Most queries have one annotated relevant document. "
                "Therefore raw Precision@5 cannot reach 1.0; normalized "
                "Precision@5 compares it with the annotated maximum."
            ),
            (
                "- These metrics evaluate retrieval ranking and do "
                "not measure factual quality of generated answers."
            ),
            ""
        ]
    )

    return "\n".join(lines)


def print_query_result(row):
    """Prints one compact result block."""

    print("-" * 80)
    print(
        f"{row['question_id']} | "
        f"{row['category']}"
    )
    print(row["question"])
    print(
        "Expected:",
        row["expected_files"]
    )
    print(
        "Retrieved:",
        row["retrieved_files"]
    )
    print(
        "First relevant rank:",
        row["first_relevant_rank"] or "not found"
    )
    print(
        "Latency:",
        f"{row['latency_seconds']:.4f} s"
    )


def main():
    manifest_by_name = load_manifest()
    validate_questions(
        manifest_by_name
    )

    collection_info = get_collection_info()

    if collection_info.get("count", 0) == 0:
        raise RuntimeError(
            "The BGE collection is empty."
        )

    print("=" * 80)
    print("DOCUMENT-LEVEL BGE RETRIEVAL EVALUATION")
    print("=" * 80)
    print(
        "Collection:",
        collection_info.get("name", "")
    )
    print(
        "Indexed chunks:",
        collection_info.get("count", 0)
    )
    print(
        "Queries:",
        len(QUESTIONS)
    )

    rows = []

    for item in QUESTIONS:
        row = evaluate_question(
            item,
            manifest_by_name
        )
        rows.append(row)
        print_query_result(row)

    metrics = calculate_metrics(rows)

    write_results_csv(rows)

    markdown_summary = build_markdown_summary(
        rows,
        metrics,
        collection_info
    )

    SUMMARY_MD.write_text(
        markdown_summary,
        encoding="utf-8"
    )

    print()
    print("=" * 80)
    print("AGGREGATE METRICS")
    print("=" * 80)
    print(f"Hit@1: {metrics['hit_at_1']:.2%}")
    print(f"Hit@3: {metrics['hit_at_3']:.2%}")
    print(f"Hit@5: {metrics['hit_at_5']:.2%}")
    print(f"MRR@5: {metrics['mrr_at_5']:.4f}")
    print(
        "Mean Precision@5:",
        f"{metrics['mean_precision_at_5']:.4f}"
    )
    print(
        "Maximum mean Precision@5:",
        f"{metrics['maximum_mean_precision_at_5']:.4f}"
    )
    print(
        "Normalized Precision@5:",
        f"{metrics['normalized_precision_at_5']:.4f}"
    )
    print(
        "Mean Recall@5:",
        f"{metrics['mean_recall_at_5']:.4f}"
    )
    print(
        "Mean latency:",
        f"{metrics['mean_latency_seconds']:.4f} s"
    )
    print("Detailed CSV:", RESULTS_CSV.resolve())
    print("Summary report:", SUMMARY_MD.resolve())


if __name__ == "__main__":
    main()