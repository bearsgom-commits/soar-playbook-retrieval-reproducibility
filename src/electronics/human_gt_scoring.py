"""Human-ground-truth scoring primitives for Electronics.

This module is intentionally pure and pre-execution:
- it does not run retrieval;
- it does not load frozen research artifacts on import;
- it does not score scientific results on import.

The functions implement the frozen E03/E03A metric semantics for later
E09-authorized execution.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Iterable, Mapping, Optional, Sequence


PHASE3_QRELS_BASENAME = "phase3_relevance_final_qrels_v1.csv"
PHASE2_OPERATIONAL_GT_BASENAME = (
    "phase2_operational_labels_final_gt_v1.csv"
)

RELEVANCE_THRESHOLD = 2
UTILITY_CUTOFF = 10
OMF_COVERAGE_THRESHOLD = 0.95

EPSILONS = (0, 2, 4, 8, 16, 32, 64)
SEEDS = (7, 13, 42)
ADJACENT_EPSILON_PAIRS = tuple(
    zip(EPSILONS[:-1], EPSILONS[1:])
)

OPERATIONAL_DIMENSIONS = (
    "response_categories",
    "critical_actions",
    "human_approval_required",
    "automation_level",
    "action_reversibility",
)

UNCERTAIN = "UNCERTAIN"
NONE_TOKEN = "NONE"


class ScoringContractError(ValueError):
    """Raised when an input violates the frozen scoring contract."""


class UnjudgedItemError(ScoringContractError):
    """Raised when a required retrieval item has no relevance judgment."""


@dataclass(frozen=True)
class QueryUtility:
    query_id: str
    covered_query: bool
    total_relevant: int
    ndcg_at_10: float
    recall_at_5: float
    recall_at_10: float
    mrr_at_10: float
    top1_relevance_rate: float
    top1_mean_relevance_grade: float


@dataclass(frozen=True)
class OperationalLabel:
    response_categories: Optional[frozenset[str]]
    critical_actions: Optional[frozenset[str]]
    human_approval_required: Optional[str]
    automation_level: Optional[str]
    action_reversibility: Optional[str]


@dataclass(frozen=True)
class OperationalComparison:
    top1_flip: bool
    category_shift: Optional[bool]
    critical_action_shift: Optional[bool]
    human_approval_shift: Optional[bool]
    automation_level_shift: Optional[bool]
    action_reversibility_shift: Optional[bool]
    covered_for_omf: bool
    omf: Optional[bool]
    propagation_class: Optional[str]


@dataclass(frozen=True)
class OMFCoverageResult:
    eligible_transition_count: int
    covered_transition_count: int
    overall_coverage: float
    pair_coverage: Mapping[str, float]
    pair_denominators: Mapping[str, int]
    pair_covered_counts: Mapping[str, int]


@dataclass(frozen=True)
class OMFRResult:
    coverage: OMFCoverageResult
    coverage_gate_pass: bool
    available_case_omfr: Optional[float]
    validated_omfr: Optional[float]
    status: str


def _read_csv(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open(
        encoding="utf-8-sig",
        newline="",
    ) as stream:
        return list(csv.DictReader(stream))


def parse_pipe_multivalue(
    raw: str,
) -> Optional[frozenset[str]]:
    """Parse frozen Phase-2 pipe-delimited set labels.

    UNCERTAIN means unavailable.
    NONE represents the empty set.
    """
    value = str(raw).strip()

    if not value:
        raise ScoringContractError(
            "empty multi-value operational label"
        )

    if value.upper() == UNCERTAIN:
        return None

    tokens = [
        token.strip()
        for token in value.split("|")
        if token.strip()
    ]

    if not tokens:
        raise ScoringContractError(
            "empty tokenized multi-value label"
        )

    if UNCERTAIN in {
        token.upper() for token in tokens
    }:
        return None

    if NONE_TOKEN in tokens:
        if len(tokens) != 1:
            raise ScoringContractError(
                "NONE cannot co-occur with another set label"
            )
        return frozenset()

    return frozenset(tokens)


def parse_scalar_label(raw: str) -> Optional[str]:
    value = str(raw).strip()

    if not value:
        raise ScoringContractError(
            "empty scalar operational label"
        )

    if value.upper() == UNCERTAIN:
        return None

    return value


def operational_label_from_row(
    row: Mapping[str, str],
) -> OperationalLabel:
    missing = [
        field
        for field in OPERATIONAL_DIMENSIONS
        if field not in row
    ]

    if missing:
        raise ScoringContractError(
            "missing operational fields: "
            + ",".join(missing)
        )

    return OperationalLabel(
        response_categories=parse_pipe_multivalue(
            row["response_categories"]
        ),
        critical_actions=parse_pipe_multivalue(
            row["critical_actions"]
        ),
        human_approval_required=parse_scalar_label(
            row["human_approval_required"]
        ),
        automation_level=parse_scalar_label(
            row["automation_level"]
        ),
        action_reversibility=parse_scalar_label(
            row["action_reversibility"]
        ),
    )


def load_phase2_operational_gt(
    path: Path | str,
) -> dict[str, OperationalLabel]:
    rows = _read_csv(path)

    if not rows:
        raise ScoringContractError(
            "Phase-2 operational GT is empty"
        )

    if "electronics_id" not in rows[0]:
        raise ScoringContractError(
            "Phase-2 operational GT lacks electronics_id"
        )

    result: dict[str, OperationalLabel] = {}

    for row in rows:
        electronics_id = str(
            row["electronics_id"]
        ).strip()

        if not electronics_id:
            raise ScoringContractError(
                "empty electronics_id"
            )

        if electronics_id in result:
            raise ScoringContractError(
                f"duplicate electronics_id: {electronics_id}"
            )

        result[electronics_id] = (
            operational_label_from_row(row)
        )

    return result


def load_phase3_qrels(
    path: Path | str,
) -> dict[str, dict[str, int]]:
    rows = _read_csv(path)

    if not rows:
        raise ScoringContractError(
            "Phase-3 qrels are empty"
        )

    required = {
        "query_id",
        "electronics_id",
        "relevance_grade",
    }

    missing = required - set(rows[0])

    if missing:
        raise ScoringContractError(
            "Phase-3 qrels missing fields: "
            + ",".join(sorted(missing))
        )

    result: dict[str, dict[str, int]] = {}

    for row in rows:
        query_id = str(row["query_id"]).strip()
        electronics_id = str(
            row["electronics_id"]
        ).strip()

        try:
            grade = int(
                str(row["relevance_grade"]).strip()
            )
        except Exception as exc:
            raise ScoringContractError(
                "invalid relevance grade"
            ) from exc

        if grade not in {0, 1, 2, 3}:
            raise ScoringContractError(
                f"relevance grade outside 0..3: {grade}"
            )

        by_doc = result.setdefault(
            query_id,
            {},
        )

        if electronics_id in by_doc:
            raise ScoringContractError(
                f"duplicate qrel pair: "
                f"{query_id}/{electronics_id}"
            )

        by_doc[electronics_id] = grade

    return result


def _dcg(
    grades: Sequence[int],
    cutoff: int = UTILITY_CUTOFF,
) -> float:
    total = 0.0

    for rank, grade in enumerate(
        grades[:cutoff],
        start=1,
    ):
        gain = (2 ** grade) - 1
        total += gain / math.log2(rank + 1)

    return total


def score_query_utility(
    query_id: str,
    ranked_ids: Sequence[str],
    qrels: Mapping[str, Mapping[str, int]],
) -> QueryUtility:
    if query_id not in qrels:
        raise ScoringContractError(
            f"query absent from qrels: {query_id}"
        )

    if len(ranked_ids) < UTILITY_CUTOFF:
        raise ScoringContractError(
            "ranking shorter than Top-10"
        )

    top10 = [
        str(x)
        for x in ranked_ids[:UTILITY_CUTOFF]
    ]

    if len(top10) != len(set(top10)):
        raise ScoringContractError(
            f"duplicate ID in Top-10: {query_id}"
        )

    judged = qrels[query_id]

    missing = [
        doc_id
        for doc_id in top10
        if doc_id not in judged
    ]

    if missing:
        raise UnjudgedItemError(
            "unjudged Top-10 item(s): "
            + ",".join(missing)
        )

    retrieved_grades = [
        int(judged[doc_id])
        for doc_id in top10
    ]

    all_grades = [
        int(value)
        for value in judged.values()
    ]

    total_relevant = sum(
        grade >= RELEVANCE_THRESHOLD
        for grade in all_grades
    )

    covered_query = total_relevant > 0

    ideal_grades = sorted(
        all_grades,
        reverse=True,
    )

    dcg = _dcg(retrieved_grades)
    idcg = _dcg(ideal_grades)

    ndcg = (
        dcg / idcg
        if idcg > 0
        else 0.0
    )

    relevant_top5 = sum(
        grade >= RELEVANCE_THRESHOLD
        for grade in retrieved_grades[:5]
    )

    relevant_top10 = sum(
        grade >= RELEVANCE_THRESHOLD
        for grade in retrieved_grades
    )

    if total_relevant:
        recall5 = (
            relevant_top5 / total_relevant
        )
        recall10 = (
            relevant_top10 / total_relevant
        )
    else:
        recall5 = 0.0
        recall10 = 0.0

    reciprocal_rank = 0.0

    for rank, grade in enumerate(
        retrieved_grades,
        start=1,
    ):
        if grade >= RELEVANCE_THRESHOLD:
            reciprocal_rank = 1.0 / rank
            break

    top1_grade = float(
        retrieved_grades[0]
    )

    top1_relevant = float(
        retrieved_grades[0]
        >= RELEVANCE_THRESHOLD
    )

    return QueryUtility(
        query_id=query_id,
        covered_query=covered_query,
        total_relevant=total_relevant,
        ndcg_at_10=ndcg,
        recall_at_5=recall5,
        recall_at_10=recall10,
        mrr_at_10=reciprocal_rank,
        top1_relevance_rate=top1_relevant,
        top1_mean_relevance_grade=top1_grade,
    )


UTILITY_FIELDS = (
    "ndcg_at_10",
    "recall_at_5",
    "recall_at_10",
    "mrr_at_10",
    "top1_relevance_rate",
    "top1_mean_relevance_grade",
)


def aggregate_query_utility(
    scores: Sequence[QueryUtility],
    view: str = "covered",
) -> dict[str, float | int]:
    if view not in {
        "covered",
        "all_query_zero_uncovered",
    }:
        raise ScoringContractError(
            f"unknown utility view: {view}"
        )

    if not scores:
        raise ScoringContractError(
            "utility score collection is empty"
        )

    rows: list[dict[str, float]] = []

    for score in scores:
        if view == "covered":
            if not score.covered_query:
                continue

            rows.append({
                field: float(
                    getattr(score, field)
                )
                for field in UTILITY_FIELDS
            })

        else:
            if score.covered_query:
                rows.append({
                    field: float(
                        getattr(score, field)
                    )
                    for field in UTILITY_FIELDS
                })
            else:
                rows.append({
                    field: 0.0
                    for field in UTILITY_FIELDS
                })

    if not rows:
        raise ScoringContractError(
            "utility denominator is zero"
        )

    output: dict[str, float | int] = {
        "query_denominator": len(rows),
    }

    for field in UTILITY_FIELDS:
        output[field] = mean(
            row[field]
            for row in rows
        )

    return output


def _optional_shift(
    left: object,
    right: object,
) -> Optional[bool]:
    if left is None or right is None:
        return None

    return left != right


def compare_operational_labels(
    left: OperationalLabel,
    right: OperationalLabel,
    *,
    top1_flip: bool,
) -> OperationalComparison:
    category_shift = _optional_shift(
        left.response_categories,
        right.response_categories,
    )

    critical_action_shift = _optional_shift(
        left.critical_actions,
        right.critical_actions,
    )

    human_approval_shift = _optional_shift(
        left.human_approval_required,
        right.human_approval_required,
    )

    automation_level_shift = _optional_shift(
        left.automation_level,
        right.automation_level,
    )

    action_reversibility_shift = _optional_shift(
        left.action_reversibility,
        right.action_reversibility,
    )

    shifts = (
        category_shift,
        critical_action_shift,
        human_approval_shift,
        automation_level_shift,
        action_reversibility_shift,
    )

    covered = all(
        value is not None
        for value in shifts
    )

    if not covered:
        return OperationalComparison(
            top1_flip=top1_flip,
            category_shift=category_shift,
            critical_action_shift=critical_action_shift,
            human_approval_shift=human_approval_shift,
            automation_level_shift=automation_level_shift,
            action_reversibility_shift=action_reversibility_shift,
            covered_for_omf=False,
            omf=None,
            propagation_class=None,
        )

    any_shift = any(
        bool(value)
        for value in shifts
    )

    omf = bool(
        top1_flip and any_shift
    )

    if not top1_flip:
        propagation_class = "A"

    elif (
        bool(human_approval_shift)
        or bool(automation_level_shift)
    ):
        propagation_class = "E"

    elif (
        bool(critical_action_shift)
        or bool(action_reversibility_shift)
    ):
        propagation_class = "D"

    elif bool(category_shift):
        propagation_class = "C"

    else:
        propagation_class = "B"

    return OperationalComparison(
        top1_flip=top1_flip,
        category_shift=bool(category_shift),
        critical_action_shift=bool(
            critical_action_shift
        ),
        human_approval_shift=bool(
            human_approval_shift
        ),
        automation_level_shift=bool(
            automation_level_shift
        ),
        action_reversibility_shift=bool(
            action_reversibility_shift
        ),
        covered_for_omf=True,
        omf=omf,
        propagation_class=propagation_class,
    )


def _transition_key(
    row: Mapping[str, object],
) -> tuple[str, int, int, int]:
    try:
        return (
            str(row["query_id"]),
            int(row["seed"]),
            int(row["epsilon_from"]),
            int(row["epsilon_to"]),
        )
    except Exception as exc:
        raise ScoringContractError(
            "invalid transition identity"
        ) from exc


def compute_omf_coverage(
    transition_rows: Sequence[
        Mapping[str, object]
    ],
    eligible_query_ids: Iterable[str],
) -> OMFCoverageResult:
    queries = {
        str(q)
        for q in eligible_query_ids
    }

    if not queries:
        raise ScoringContractError(
            "eligible query set is empty"
        )

    expected = {
        (
            query_id,
            seed,
            epsilon_from,
            epsilon_to,
        )
        for query_id in queries
        for seed in SEEDS
        for (
            epsilon_from,
            epsilon_to,
        ) in ADJACENT_EPSILON_PAIRS
    }

    indexed = {}

    for row in transition_rows:
        key = _transition_key(row)

        if key[0] not in queries:
            continue

        if key in indexed:
            raise ScoringContractError(
                f"duplicate OMF transition: {key}"
            )

        indexed[key] = row

    actual = set(indexed)

    if actual != expected:
        missing = expected - actual
        extra = actual - expected

        raise ScoringContractError(
            "OMF transition coverage grid mismatch; "
            f"missing={len(missing)}, "
            f"extra={len(extra)}"
        )

    pair_denominators: dict[str, int] = {}
    pair_covered: dict[str, int] = {}

    covered_total = 0

    for (
        epsilon_from,
        epsilon_to,
    ) in ADJACENT_EPSILON_PAIRS:

        pair_name = (
            f"{epsilon_from}->{epsilon_to}"
        )

        pair_rows = [
            row
            for key, row in indexed.items()
            if key[2:] == (
                epsilon_from,
                epsilon_to,
            )
        ]

        covered = sum(
            bool(
                row.get(
                    "covered_for_omf",
                    False,
                )
            )
            for row in pair_rows
        )

        pair_denominators[pair_name] = (
            len(pair_rows)
        )

        pair_covered[pair_name] = covered

        covered_total += covered

    total = len(indexed)

    pair_coverage = {
        pair: (
            pair_covered[pair]
            / pair_denominators[pair]
        )
        for pair in pair_denominators
    }

    return OMFCoverageResult(
        eligible_transition_count=total,
        covered_transition_count=covered_total,
        overall_coverage=covered_total / total,
        pair_coverage=pair_coverage,
        pair_denominators=pair_denominators,
        pair_covered_counts=pair_covered,
    )


def compute_validated_omfr(
    transition_rows: Sequence[
        Mapping[str, object]
    ],
    eligible_query_ids: Iterable[str],
    *,
    threshold: float = OMF_COVERAGE_THRESHOLD,
) -> OMFRResult:
    coverage = compute_omf_coverage(
        transition_rows,
        eligible_query_ids,
    )

    pair_gate = all(
        value >= threshold
        for value in coverage.pair_coverage.values()
    )

    gate_pass = (
        coverage.overall_coverage >= threshold
        and pair_gate
    )

    available_values: list[float] = []

    eligible = {
        str(q)
        for q in eligible_query_ids
    }

    for row in transition_rows:
        if str(row["query_id"]) not in eligible:
            continue

        if not bool(
            row.get(
                "covered_for_omf",
                False,
            )
        ):
            continue

        value = row.get("omf")

        if value is None:
            raise ScoringContractError(
                "covered OMF row has omf=None"
            )

        available_values.append(
            float(bool(value))
        )

    available_case = (
        mean(available_values)
        if available_values
        else None
    )

    validated = (
        available_case
        if gate_pass
        else None
    )

    status = (
        "ADJUDICATED_OMFR"
        if gate_pass
        else "AVAILABLE_CASE_EXPLORATORY"
    )

    return OMFRResult(
        coverage=coverage,
        coverage_gate_pass=gate_pass,
        available_case_omfr=available_case,
        validated_omfr=validated,
        status=status,
    )


def utility_noninferiority_retained(
    *,
    raw_mean_ndcg_at_10: float,
    guard_mean_ndcg_at_10: float,
    lower95_delta: float,
    retention_fraction: float = 0.95,
) -> bool:
    """Apply the frozen Raw-relative utility non-inferiority rule."""
    if not 0 < retention_fraction <= 1:
        raise ScoringContractError(
            "retention_fraction must be in (0,1]"
        )

    delta_u = (
        guard_mean_ndcg_at_10
        - raw_mean_ndcg_at_10
    )

    # Explicitly compute the frozen margin from Raw.
    margin = (
        (1.0 - retention_fraction)
        * raw_mean_ndcg_at_10
    )

    # The point estimate is retained for audit/debug consistency,
    # but the frozen decision is made by Lower95.
    _ = delta_u

    return lower95_delta >= -margin
