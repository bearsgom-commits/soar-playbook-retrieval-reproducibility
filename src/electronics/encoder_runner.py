"""Electronics v3.4 E5 encoder preparation and injectable encoding contract.

This module does not instantiate or download a model, run experiments, or
write scientific results. Scientific execution requires a later E09 gate.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from electronics.pre_embedding_contract import (
    check_input_record_text,
    verify_vector_array,
    require_mps_available,
)

MODEL_ID = "intfloat/multilingual-e5-base"
MODEL_REVISION = "d128750597153bb5987e10b1c3493a34e5a4502a"

EXPECTED_COUNTS = {
    "playbooks": 1606,
    "queries": 30,
    "anchors": 50,
}

EXPECTED_DIMENSION = 768
EXPECTED_MAX_SEQ_LENGTH = 512

ARRAY_ORDER = (
    "C_query",
    "C_broad",
    "B0_query",
    "B0_anchor",
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    path = Path(path)
    rows = []

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(
                    f"BLANK_JSONL_LINE:{path.name}:{line_number}"
                )

            row = json.loads(line)

            if not isinstance(row, dict):
                raise ValueError(
                    f"NON_OBJECT_JSONL_ROW:{path.name}:{line_number}"
                )

            rows.append(row)

    return rows


def build_input_plan(
    playbooks: list[dict],
    queries: list[dict],
    anchors: list[dict],
) -> dict:
    """Bind actual source-clean inputs; never reconstruct conference text."""

    observed = {
        "playbooks": len(playbooks),
        "queries": len(queries),
        "anchors": len(anchors),
    }

    if observed != EXPECTED_COUNTS:
        raise ValueError(
            f"FROZEN_INPUT_COUNTS_CHANGED:{observed}"
        )

    check_input_record_text(playbooks, queries, anchors)

    playbook_ids = [
        row["electronics_id"]
        for row in playbooks
    ]

    query_ids = [
        row["query_id"]
        for row in queries
    ]

    anchor_ids = [
        row["electronics_id"]
        for row in anchors
    ]

    if len(set(playbook_ids)) != len(playbook_ids):
        raise ValueError("DUPLICATE_ELECTRONICS_ID")

    if len(set(query_ids)) != len(query_ids):
        raise ValueError("DUPLICATE_QUERY_ID")

    if len(set(anchor_ids)) != len(anchor_ids):
        raise ValueError("DUPLICATE_ANCHOR_ELECTRONICS_ID")

    by_eid = {
        row["electronics_id"]: row
        for row in playbooks
    }

    # Historical B0 order is the order of the anchor binding file.
    # Its unprefixed input is the matched original YAML source-clean text.
    b0_anchor_texts = []

    for anchor in anchors:
        source = by_eid[anchor["electronics_id"]]

        if (
            sha256_text(source["source_text"])
            != anchor["B0_text_sha256"]
        ):
            raise ValueError("B0_ANCHOR_TEXT_HASH_DRIFT")

        if (
            sha256_text(source["C_encoder_text"])
            != anchor["B1_passage_text_sha256"]
        ):
            raise ValueError("B1_ANCHOR_PASSAGE_HASH_DRIFT")

        b0_anchor_texts.append(source["source_text"])

    arrays = {
        "C_query": [
            row["C_encoder_text"]
            for row in queries
        ],
        "C_broad": [
            row["C_encoder_text"]
            for row in playbooks
        ],
        "B0_query": [
            row["query_text"]
            for row in queries
        ],
        "B0_anchor": b0_anchor_texts,
    }

    if any(
        text.startswith(("query: ", "passage: "))
        for text in arrays["B0_query"] + arrays["B0_anchor"]
    ):
        raise ValueError("B0_UNPREFIXED_INPUT_CONTRACT_VIOLATION")

    if any(
        not isinstance(text, str) or not text
        for values in arrays.values()
        for text in values
    ):
        raise ValueError("EMPTY_OR_INVALID_ENCODER_INPUT")

    return {
        "arrays": arrays,
        "C_broad_ids": [
            row["electronics_id"]
            for row in playbooks
        ],
        "query_ids": [
            row["query_id"]
            for row in queries
        ],
        "B0_anchor_ids": [
            row["playbook_id"]
            for row in anchors
        ],
        "B1_broad_indices": [
            next(
                index
                for index, row in enumerate(playbooks)
                if row["electronics_id"] == anchor["electronics_id"]
            )
            for anchor in anchors
        ],
        "text_sha256": {
            name: [
                sha256_text(text)
                for text in arrays[name]
            ]
            for name in ARRAY_ORDER
        },
    }


def validate_model_contract(
    model,
    *,
    requested_device: str = "mps",
    mps_available: bool,
) -> None:
    """Fail closed on device, model identity, revision, and prompt drift."""

    require_mps_available(
        mps_available,
        requested_device=requested_device,
    )

    if getattr(model, "device", None) is None:
        raise ValueError("MODEL_DEVICE_UNAVAILABLE")

    if str(model.device).split(":")[0] != "mps":
        raise ValueError("MODEL_NOT_ON_MPS")

    if (
        getattr(model, "max_seq_length", None)
        != EXPECTED_MAX_SEQ_LENGTH
    ):
        raise ValueError("MODEL_MAX_SEQ_LENGTH_DRIFT")

    if getattr(model, "default_prompt_name", None) is not None:
        raise ValueError("MODEL_DEFAULT_PROMPT_DRIFT")

    prompts = getattr(model, "prompts", None)

    if not isinstance(prompts, dict) or (
        prompts.get("query") != ""
        or prompts.get("document") != ""
    ):
        raise ValueError("MODEL_REGISTERED_PROMPTS_DRIFT")

    try:
        observed_revision = (
            model[0].auto_model.config._commit_hash
        )
    except (AttributeError, IndexError, KeyError, TypeError):
        raise ValueError(
            "MODEL_REVISION_UNAVAILABLE"
        ) from None

    if observed_revision != MODEL_REVISION:
        raise ValueError("MODEL_REVISION_DRIFT")


def encode_with_injected_model(
    model,
    plan: dict,
    *,
    mps_available: bool,
    requested_device: str = "mps",
    batch_size: int = 16,
) -> dict[str, np.ndarray]:
    """Future E09-controlled caller supplies the already-pinned model.

    Never load a model or infer authorization from this function.
    Four independent arrays only; B1 and PRIMARY remain C BROAD views.
    """

    validate_model_contract(
        model,
        requested_device=requested_device,
        mps_available=mps_available,
    )

    if not isinstance(batch_size, int) or batch_size < 1:
        raise ValueError("INVALID_BATCH_SIZE")

    if set(plan.get("arrays", {})) != set(ARRAY_ORDER):
        raise ValueError("ENCODER_ARRAY_PLAN_DRIFT")

    outputs = {}

    for name in ARRAY_ORDER:
        texts = plan["arrays"][name]

        if len(texts) != {
            "C_query": 30,
            "C_broad": 1606,
            "B0_query": 30,
            "B0_anchor": 50,
        }[name]:
            raise ValueError("ENCODER_ARRAY_ROW_COUNT_DRIFT")

        # Explicit empty prompt prevents implicit additional E5 prefixes.
        array = model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,
            prompt="",
        )

        if not isinstance(array, np.ndarray):
            raise ValueError("ENCODER_NON_NUMPY_OUTPUT")

        if array.dtype != np.dtype("float32"):
            raise ValueError("ENCODER_NON_FLOAT32_OUTPUT")

        outputs[name] = verify_vector_array(
            array,
            expected_rows=len(texts),
            dimension=EXPECTED_DIMENSION,
        )

    if (
        outputs["C_query"] is outputs["B0_query"]
        or outputs["C_broad"] is outputs["B0_anchor"]
    ):
        raise ValueError("PREFIXED_UNPREFIXED_ARRAY_ALIAS")

    return outputs


def build_output_provenance(
    plan: dict,
    outputs: dict[str, np.ndarray],
) -> dict:
    """Prepare future provenance; does not save or publish arrays."""

    if set(outputs) != set(ARRAY_ORDER):
        raise ValueError("OUTPUT_ARRAY_SET_DRIFT")

    records = {}

    for name in ARRAY_ORDER:
        array = verify_vector_array(
            outputs[name],
            len(plan["arrays"][name]),
            EXPECTED_DIMENSION,
        )

        records[name] = {
            "rows": int(array.shape[0]),
            "dimension": int(array.shape[1]),
            "dtype": str(array.dtype),
            "input_text_sha256": plan["text_sha256"][name],
            "array_sha256": hashlib.sha256(
                np.ascontiguousarray(array).tobytes()
            ).hexdigest(),
        }

    return {
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "device_required": "mps",
        "normalize_embeddings": True,
        "arrays": records,
        "B1": "VIEW_OF_C_BROAD_NOT_REENCODED",
        "C_PRIMARY": "VIEW_OF_C_BROAD_NOT_REENCODED",
    }
