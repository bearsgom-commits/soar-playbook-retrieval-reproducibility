import csv

import pytest

from electronics import human_gt_scoring as M


def op_row(**overrides):
    row = {
        "response_categories":
            "INVESTIGATION_EVIDENCE_COLLECTION",
        "critical_actions":
            "EVIDENCE_COLLECT",
        "human_approval_required":
            "NO",
        "automation_level":
            "AUTOMATED",
        "action_reversibility":
            "NO_STATE_CHANGE",
    }

    row.update(overrides)
    return row


def build_transition_grid(
    query_ids=("Q01", "Q02"),
):
    rows = []

    for query in query_ids:
        for seed in M.SEEDS:
            for e0, e1 in M.ADJACENT_EPSILON_PAIRS:
                rows.append({
                    "query_id": query,
                    "seed": seed,
                    "epsilon_from": e0,
                    "epsilon_to": e1,
                    "covered_for_omf": True,
                    "omf": False,
                })

    return rows


def test_pipe_multivalue_is_order_independent():
    a = M.parse_pipe_multivalue(
        "NETWORK_CONTAINMENT|"
        "INVESTIGATION_EVIDENCE_COLLECTION"
    )

    b = M.parse_pipe_multivalue(
        "INVESTIGATION_EVIDENCE_COLLECTION|"
        "NETWORK_CONTAINMENT"
    )

    assert a == b


def test_none_is_empty_set():
    assert M.parse_pipe_multivalue(
        "NONE"
    ) == frozenset()


def test_none_cannot_mix_with_real_label():
    with pytest.raises(M.ScoringContractError):
        M.parse_pipe_multivalue(
            "NONE|NETWORK_CONTAINMENT"
        )


def test_uncertain_is_missing_not_no():
    assert M.parse_scalar_label(
        "UNCERTAIN"
    ) is None

    assert M.parse_scalar_label(
        "NO"
    ) == "NO"


def test_operational_adapter_preserves_uncertainty():
    label = M.operational_label_from_row(
        op_row(
            automation_level="UNCERTAIN"
        )
    )

    assert label.automation_level is None
    assert label.human_approval_required == "NO"


def test_phase3_qrels_adapter(tmp_path):
    path = tmp_path / M.PHASE3_QRELS_BASENAME

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "query_id",
                "electronics_id",
                "relevance_grade",
            ],
        )
        w.writeheader()
        w.writerow({
            "query_id": "Q01",
            "electronics_id": "E1",
            "relevance_grade": "3",
        })

    qrels = M.load_phase3_qrels(path)

    assert qrels == {
        "Q01": {"E1": 3}
    }


def test_phase2_operational_gt_adapter(tmp_path):
    path = tmp_path / M.PHASE2_OPERATIONAL_GT_BASENAME

    fields = [
        "electronics_id",
        *M.OPERATIONAL_DIMENSIONS,
    ]

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        w = csv.DictWriter(
            f,
            fieldnames=fields,
        )
        w.writeheader()

        row = {
            "electronics_id": "E1",
            **op_row(),
        }

        w.writerow(row)

    result = M.load_phase2_operational_gt(
        path
    )

    assert set(result) == {"E1"}
    assert (
        result["E1"].critical_actions
        == frozenset({"EVIDENCE_COLLECT"})
    )


def test_perfect_query_utility():
    qrels = {
        "Q01": {
            "E1": 3,
            "E2": 2,
            "E3": 1,
            "E4": 0,
            "E5": 0,
            "E6": 0,
            "E7": 0,
            "E8": 0,
            "E9": 0,
            "E10": 0,
        }
    }

    ranking = [
        "E1", "E2", "E3", "E4", "E5",
        "E6", "E7", "E8", "E9", "E10",
    ]

    s = M.score_query_utility(
        "Q01",
        ranking,
        qrels,
    )

    assert s.covered_query is True
    assert s.total_relevant == 2
    assert s.ndcg_at_10 == pytest.approx(1.0)
    assert s.recall_at_5 == pytest.approx(1.0)
    assert s.recall_at_10 == pytest.approx(1.0)
    assert s.mrr_at_10 == pytest.approx(1.0)
    assert s.top1_relevance_rate == 1.0
    assert s.top1_mean_relevance_grade == 3.0


def test_unjudged_item_is_not_zero():
    qrels = {
        "Q01": {
            f"E{i}": 0
            for i in range(1, 10)
        }
    }

    ranking = [
        f"E{i}"
        for i in range(1, 11)
    ]

    with pytest.raises(M.UnjudgedItemError):
        M.score_query_utility(
            "Q01",
            ranking,
            qrels,
        )


def test_all_query_sensitivity_zeros_uncovered_query():
    covered = M.QueryUtility(
        query_id="Q01",
        covered_query=True,
        total_relevant=1,
        ndcg_at_10=1.0,
        recall_at_5=1.0,
        recall_at_10=1.0,
        mrr_at_10=1.0,
        top1_relevance_rate=1.0,
        top1_mean_relevance_grade=3.0,
    )

    uncovered = M.QueryUtility(
        query_id="Q02",
        covered_query=False,
        total_relevant=0,
        ndcg_at_10=0.5,
        recall_at_5=0.0,
        recall_at_10=0.0,
        mrr_at_10=0.0,
        top1_relevance_rate=0.0,
        top1_mean_relevance_grade=1.0,
    )

    primary = M.aggregate_query_utility(
        [covered, uncovered],
        view="covered",
    )

    sensitivity = M.aggregate_query_utility(
        [covered, uncovered],
        view="all_query_zero_uncovered",
    )

    assert primary["query_denominator"] == 1
    assert primary["ndcg_at_10"] == 1.0

    assert sensitivity[
        "query_denominator"
    ] == 2

    assert sensitivity[
        "ndcg_at_10"
    ] == pytest.approx(0.5)

    assert sensitivity[
        "top1_mean_relevance_grade"
    ] == pytest.approx(1.5)


def test_order_only_change_in_multivalue_is_not_shift():
    left = M.operational_label_from_row(
        op_row(
            response_categories=(
                "NETWORK_CONTAINMENT|"
                "INVESTIGATION_EVIDENCE_COLLECTION"
            )
        )
    )

    right = M.operational_label_from_row(
        op_row(
            response_categories=(
                "INVESTIGATION_EVIDENCE_COLLECTION|"
                "NETWORK_CONTAINMENT"
            )
        )
    )

    c = M.compare_operational_labels(
        left,
        right,
        top1_flip=True,
    )

    assert c.category_shift is False
    assert c.omf is False
    assert c.propagation_class == "B"


def test_atomic_shift_and_propagation_priority():
    left = M.operational_label_from_row(
        op_row()
    )

    right = M.operational_label_from_row(
        op_row(
            response_categories=
                "NETWORK_CONTAINMENT",
            critical_actions=
                "NETWORK_CONTAIN",
            human_approval_required=
                "YES",
        )
    )

    c = M.compare_operational_labels(
        left,
        right,
        top1_flip=True,
    )

    assert c.category_shift is True
    assert c.critical_action_shift is True
    assert c.human_approval_shift is True
    assert c.omf is True

    # E outranks D and C.
    assert c.propagation_class == "E"


def test_uncertain_dimension_blocks_omf_even_without_flip():
    left = M.operational_label_from_row(
        op_row(
            automation_level="UNCERTAIN"
        )
    )

    right = M.operational_label_from_row(
        op_row()
    )

    c = M.compare_operational_labels(
        left,
        right,
        top1_flip=False,
    )

    assert c.covered_for_omf is False
    assert c.automation_level_shift is None
    assert c.omf is None
    assert c.propagation_class is None


def test_complete_no_flip_is_class_a():
    left = M.operational_label_from_row(
        op_row()
    )

    right = M.operational_label_from_row(
        op_row()
    )

    c = M.compare_operational_labels(
        left,
        right,
        top1_flip=False,
    )

    assert c.covered_for_omf is True
    assert c.omf is False
    assert c.propagation_class == "A"


def test_omf_coverage_complete_grid_passes():
    rows = build_transition_grid()

    result = M.compute_omf_coverage(
        rows,
        {"Q01", "Q02"},
    )

    assert result.eligible_transition_count == 36
    assert result.covered_transition_count == 36
    assert result.overall_coverage == 1.0

    assert all(
        x == 1.0
        for x in result.pair_coverage.values()
    )


def test_omf_grid_missing_transition_fails_closed():
    rows = build_transition_grid()
    rows.pop()

    with pytest.raises(M.ScoringContractError):
        M.compute_omf_coverage(
            rows,
            {"Q01", "Q02"},
        )


def test_validated_omfr_passes_only_when_coverage_gate_passes():
    rows = build_transition_grid()

    rows[0]["omf"] = True

    result = M.compute_validated_omfr(
        rows,
        {"Q01", "Q02"},
    )

    assert result.coverage_gate_pass is True
    assert (
        result.validated_omfr
        == pytest.approx(1 / 36)
    )
    assert result.status == "ADJUDICATED_OMFR"


def test_pair_below_95_blocks_validated_omfr():
    rows = build_transition_grid()

    # One missing OMF label in a single pair gives 5/6 coverage
    # for that adjacent pair, below the frozen 0.95 gate.
    target = rows[0]
    target["covered_for_omf"] = False
    target["omf"] = None

    result = M.compute_validated_omfr(
        rows,
        {"Q01", "Q02"},
    )

    assert result.coverage_gate_pass is False
    assert result.validated_omfr is None
    assert (
        result.status
        == "AVAILABLE_CASE_EXPLORATORY"
    )


def test_utility_noninferiority_uses_lower95_and_raw_margin():
    assert M.utility_noninferiority_retained(
        raw_mean_ndcg_at_10=0.40,
        guard_mean_ndcg_at_10=0.39,
        lower95_delta=-0.019,
    )

    assert not M.utility_noninferiority_retained(
        raw_mean_ndcg_at_10=0.40,
        guard_mean_ndcg_at_10=0.39,
        lower95_delta=-0.021,
    )
