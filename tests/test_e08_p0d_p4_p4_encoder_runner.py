"""Synthetic-only contract tests. No model loading or scientific inputs."""

import hashlib
import unittest
from types import SimpleNamespace

import numpy as np

from electronics.encoder_runner import (
    MODEL_REVISION,
    build_input_plan,
    build_output_provenance,
    encode_with_injected_model,
    validate_model_contract,
)


def digest(value):
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def synthetic_records():
    playbooks = []

    for index in range(1606):
        eid = f"E-{index:04d}"
        text = f"Original YAML text {index}"

        playbooks.append({
            "electronics_id": eid,
            "source_text": text,
            "source_text_sha256": digest(text),
            "C_encoder_text": "passage: " + text,
            "C_encoder_text_sha256": digest(
                "passage: " + text
            ),
            "source_file": f"item_{index}.yml",
            "source_sha256": digest(f"yaml_{index}"),
            "status": "SOURCE_TEXT_AVAILABLE",
            "flags": [],
            "reason": None,
            "track_c_stratum": (
                "PRIMARY_MACHINE_SELECTED"
                if index < 830
                else "UNRESOLVED_DEFERRED"
            ),
        })

    queries = []

    for index in range(30):
        text = f"Question {index}"

        queries.append({
            "query_id": f"Q-{index:02d}",
            "query_text": text,
            "query_text_sha256": digest(text),
            "C_encoder_text": "query: " + text,
            "C_encoder_text_sha256": digest(
                "query: " + text
            ),
        })

    anchors = []

    for index in range(50):
        row = playbooks[index]

        anchors.append({
            "playbook_id": f"H-{index:02d}",
            "electronics_id": row["electronics_id"],
            "source_file": row["source_file"],
            "source_sha256": row["source_sha256"],
            "B0_text_sha256": row["source_text_sha256"],
            "B1_passage_text_sha256": (
                row["C_encoder_text_sha256"]
            ),
        })

    return playbooks, queries, anchors


class FakeModel:
    def __init__(self):
        self.device = "mps:0"
        self.max_seq_length = 512
        self.default_prompt_name = None
        self.prompts = {
            "query": "",
            "document": "",
        }
        self.calls = []
        self.module = SimpleNamespace(
            auto_model=SimpleNamespace(
                config=SimpleNamespace(
                    _commit_hash=MODEL_REVISION
                )
            )
        )

    def __getitem__(self, index):
        if index != 0:
            raise IndexError(index)
        return self.module

    def encode(self, texts, **kwargs):
        self.calls.append({
            "count": len(texts),
            "kwargs": kwargs,
        })

        array = np.zeros(
            (len(texts), 768),
            dtype=np.float32,
        )

        array[:, 0] = 1.0

        return array


class EncoderRunnerSyntheticTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.playbooks, cls.queries, cls.anchors = (
            synthetic_records()
        )

    def test_exact_four_array_plan(self):
        plan = build_input_plan(
            self.playbooks,
            self.queries,
            self.anchors,
        )

        self.assertEqual(
            [len(plan["arrays"][name]) for name in (
                "C_query",
                "C_broad",
                "B0_query",
                "B0_anchor",
            )],
            [30, 1606, 30, 50],
        )

        self.assertEqual(
            plan["arrays"]["B0_anchor"][0],
            self.playbooks[0]["source_text"],
        )

        self.assertEqual(
            plan["B1_broad_indices"],
            list(range(50)),
        )

    def test_four_encode_calls_only(self):
        plan = build_input_plan(
            self.playbooks,
            self.queries,
            self.anchors,
        )

        model = FakeModel()

        arrays = encode_with_injected_model(
            model,
            plan,
            mps_available=True,
        )

        self.assertEqual(
            [call["count"] for call in model.calls],
            [30, 1606, 30, 50],
        )

        self.assertTrue(
            all(
                call["kwargs"]["prompt"] == ""
                and call["kwargs"]["normalize_embeddings"]
                for call in model.calls
            )
        )

        self.assertEqual(
            set(arrays),
            {
                "C_query",
                "C_broad",
                "B0_query",
                "B0_anchor",
            },
        )

        provenance = build_output_provenance(
            plan,
            arrays,
        )

        self.assertEqual(
            provenance["B1"],
            "VIEW_OF_C_BROAD_NOT_REENCODED",
        )

    def test_reject_wrong_b0_anchor_hash(self):
        anchors = [
            dict(row)
            for row in self.anchors
        ]

        anchors[0]["B0_text_sha256"] = "0" * 64

        with self.assertRaises(ValueError):
            build_input_plan(
                self.playbooks,
                self.queries,
                anchors,
            )

    def test_reject_unregistered_device(self):
        with self.assertRaises(ValueError):
            validate_model_contract(
                FakeModel(),
                requested_device="cpu",
                mps_available=True,
            )

    def test_reject_unavailable_mps(self):
        with self.assertRaises(ValueError):
            validate_model_contract(
                FakeModel(),
                mps_available=False,
            )

    def test_reject_revision_drift(self):
        model = FakeModel()
        model.module.auto_model.config._commit_hash = (
            "wrong-revision"
        )

        with self.assertRaises(ValueError):
            validate_model_contract(
                model,
                mps_available=True,
            )

    def test_reject_implicit_prompt(self):
        model = FakeModel()
        model.default_prompt_name = "query"

        with self.assertRaises(ValueError):
            validate_model_contract(
                model,
                mps_available=True,
            )



    def test_reject_wrong_b1_anchor_hash(self):
        anchors = [dict(row) for row in self.anchors]
        anchors[0]["B1_passage_text_sha256"] = "0" * 64

        with self.assertRaisesRegex(
            ValueError, "ANCHOR_SOURCE_TEXT_DRIFT|B1_ANCHOR_PASSAGE_HASH_DRIFT"
        ):
            build_input_plan(
                self.playbooks, self.queries, anchors
            )

    def test_reject_duplicate_playbook_id(self):
        playbooks = [dict(row) for row in self.playbooks]
        playbooks[1]["electronics_id"] = (
            playbooks[0]["electronics_id"]
        )

        with self.assertRaisesRegex(
            ValueError, "BROAD_ID_INVALID|DUPLICATE_ELECTRONICS_ID"
        ):
            build_input_plan(
                playbooks, self.queries, self.anchors
            )

    def test_reject_duplicate_query_id(self):
        queries = [dict(row) for row in self.queries]
        queries[1]["query_id"] = queries[0]["query_id"]

        with self.assertRaisesRegex(
            ValueError, "QUERY_DUPLICATE_OR_LABEL_LEAK|DUPLICATE_QUERY_ID"
        ):
            build_input_plan(
                self.playbooks, queries, self.anchors
            )

    def test_reject_duplicate_anchor_id(self):
        anchors = [dict(row) for row in self.anchors]
        anchors[1]["electronics_id"] = (
            anchors[0]["electronics_id"]
        )

        with self.assertRaisesRegex(
            ValueError, "ANCHOR_SOURCE_TEXT_DRIFT|DUPLICATE_ANCHOR_ELECTRONICS_ID"
        ):
            build_input_plan(
                self.playbooks, self.queries, anchors
            )

if __name__ == "__main__":
    unittest.main()
