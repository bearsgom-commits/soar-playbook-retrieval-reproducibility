"""Electronics pre-execution pure validation, row-view, representation and tie contracts.

This module never instantiates an encoder, calls encode, creates scientific embeddings,
runs scientific retrieval, modifies canonical Guard or loads frozen sources itself.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np
from guard_repr import (apply_guard_repr, eps_to_repr_spec, l2_normalize,
                        make_projection_matrix, uniform_quantize)

EPS=(0,2,4,8,16,32,64)
SEEDS=(7,13,42)
FROZEN_COUNTS=(1606,30,50,830)

def digest(value: str)->str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def verify_vector_array(array,expected_rows,dimension=768):
    """Validate exact future dense outputs, without creating/re-normalizing them."""
    if not isinstance(array,np.ndarray) or array.shape!=(expected_rows,dimension):
        raise ValueError("EMBEDDING_ARRAY_SHAPE_OR_TYPE_MISMATCH")
    if array.dtype!=np.dtype("float32"):
        raise ValueError("EMBEDDING_DTYPE_NOT_FLOAT32")
    if not np.isfinite(array).all():
        raise ValueError("EMBEDDING_NONFINITE")
    if not np.allclose(np.linalg.norm(array,axis=1),1.0,rtol=0,atol=1e-4):
        raise ValueError("EMBEDDING_NOT_L2_NORMALIZED")
    return array

def select_rows_by_stable_ids(broad_ids,broad_array,selected_ids,require_broad_order=True):
    if len(broad_ids)!=len(broad_array) or len(set(broad_ids))!=len(broad_ids):
        raise ValueError("BROAD_ID_ARRAY_DRIFT")
    if len(selected_ids)!=len(set(selected_ids)) or not selected_ids:
        raise ValueError("DUPLICATE_OR_EMPTY_SELECTED_IDS")
    index={key:i for i,key in enumerate(broad_ids)}
    if any(key not in index for key in selected_ids):
        raise ValueError("SELECTED_ID_NOT_IN_BROAD")
    if require_broad_order:
        wanted=set(selected_ids)
        if selected_ids!=[key for key in broad_ids if key in wanted]:
            raise ValueError("PRIMARY_ORDER_NOT_BROAD_SUBSEQUENCE")
    indices=[index[key] for key in selected_ids]
    return broad_array[indices],indices

def check_input_record_text(playbooks,queries,anchors):
    ids=set()
    for p in playbooks:
        eid=p["electronics_id"]
        if eid in ids or not isinstance(eid,str) or not eid:raise ValueError("BROAD_ID_INVALID")
        ids.add(eid)
        if p["C_encoder_text"]!="passage: "+p["source_text"] or (
            p["source_text_sha256"]!=digest(p["source_text"])) or (
            p["C_encoder_text_sha256"]!=digest(p["C_encoder_text"])):
            raise ValueError("PLAYBOOK_INPUT_PREFIX_OR_HASH_DRIFT")
        if p["status"]!="SOURCE_TEXT_AVAILABLE" or p["flags"] or p["reason"] is not None:
            raise ValueError("SOURCE_INPUT_NOT_CLEAN_AVAILABLE")
    qids=set()
    for q in queries:
        qid=q["query_id"]
        if qid in qids or "expected_category" in q:raise ValueError("QUERY_DUPLICATE_OR_LABEL_LEAK")
        qids.add(qid)
        if q["C_encoder_text"]!="query: "+q["query_text"] or (
            q["query_text_sha256"]!=digest(q["query_text"])) or (
            q["C_encoder_text_sha256"]!=digest(q["C_encoder_text"])):
            raise ValueError("QUERY_INPUT_PREFIX_OR_HASH_DRIFT")
    anchor_ids=set()
    by_id={p["electronics_id"]:p for p in playbooks}
    for a in anchors:
        pid=a["playbook_id"]
        if pid in anchor_ids or a["electronics_id"] not in by_id:
            raise ValueError("ANCHOR_ID_OR_BINDING_DRIFT")
        anchor_ids.add(pid)
        p=by_id[a["electronics_id"]]
        if a["source_file"]!=p["source_file"] or (
          a["source_sha256"]!=p["source_sha256"]) or (
          a["B0_text_sha256"]!=p["source_text_sha256"]) or (
          a["B1_passage_text_sha256"]!=p["C_encoder_text_sha256"]):
            raise ValueError("ANCHOR_SOURCE_TEXT_DRIFT")
    return True

def build_track_views(playbooks,queries,anchors,c_broad,c_queries,b0_anchors,b0_queries,
                      *,synthetic_counts=None):
    """No re-encoding: primary/B1 are ID-indexed C BROAD rows; B1 queries alias C.

    synthetic_counts is forbidden in production and may be supplied only to
    fully isolated synthetic tests. No model is loaded by this function.
    """
    if synthetic_counts is None:
        expected=FROZEN_COUNTS
    elif isinstance(synthetic_counts,tuple) and len(synthetic_counts)==4:
        expected=synthetic_counts
    else:
        raise ValueError("INVALID_SYNTHETIC_COUNT_FIXTURE")
    nb,nq,na,np_=expected
    if (len(playbooks),len(queries),len(anchors))!=(nb,nq,na):
        raise ValueError("FROZEN_INPUT_COUNTS_CHANGED")
    check_input_record_text(playbooks,queries,anchors)
    broad_ids=[x["electronics_id"] for x in playbooks]
    primary_ids=[x["electronics_id"] for x in playbooks
                 if x["track_c_stratum"]=="PRIMARY_MACHINE_SELECTED"]
    strata=Counter(x["track_c_stratum"] for x in playbooks)
    if strata!={"PRIMARY_MACHINE_SELECTED":np_,
                "UNRESOLVED_DEFERRED":nb-np_}:
        raise ValueError("PRIMARY_OR_UNRESOLVED_COUNTS_CHANGED")
    dimension=768
    for arr,n in ((c_broad,nb),(c_queries,nq),(b0_anchors,na),(b0_queries,nq)):
        verify_vector_array(arr,n,dimension)
    if c_broad is b0_anchors or c_queries is b0_queries:
        raise ValueError("B0_UNPREFIXED_ARRAY_ALIASED_TO_PREFIXED_C")
    anchor_eids=[a["electronics_id"] for a in anchors]
    # PRIMARY is a strict order-preserving subsequence. B1 follows historical anchor order.
    primary,primary_index=select_rows_by_stable_ids(broad_ids,c_broad,primary_ids)
    b1,b1_index=select_rows_by_stable_ids(
        broad_ids,c_broad,anchor_eids,require_broad_order=False)
    return {"C_broad":c_broad,"C_query":c_queries,
            "C_broad_ids":broad_ids,
            "C_primary":primary,"C_primary_ids":primary_ids,
            "C_primary_indices":primary_index,
            "B1_anchor":b1,"B1_ids":[a["playbook_id"] for a in anchors],
            "B1_broad_indices":b1_index,"B1_query":c_queries,
            "B0_anchor":b0_anchors,"B0_query":b0_queries,
            "B0_ids":[a["playbook_id"] for a in anchors],
            "production_counts_applied":synthetic_counts is None}

def guarded_four_corner(raw,epsilon,seed):
    """Canonical Guard is ALWAYS called directly, not replaced by this ablation."""
    if epsilon not in EPS or seed not in SEEDS:raise ValueError("UNREGISTERED_GUARD_CONDITION")
    raw=verify_vector_array(raw,len(raw))
    base=l2_normalize(raw)
    spec=eps_to_repr_spec(epsilon,768)
    guard=apply_guard_repr(raw,eps=epsilon,seed=seed)
    if spec.proj_dim==768:
        projection_only=base
        quantization_only=guard
        matrix_sha=None
    else:
        W=make_projection_matrix(768,spec.proj_dim,seed)
        projection_only=l2_normalize(base @ W)
        quantization_only=l2_normalize(
            uniform_quantize(base,q_bits=spec.q_bits,clip=spec.clip))
        matrix_sha=hashlib.sha256(
            np.ascontiguousarray(W).tobytes()).hexdigest()
        reconstructed=l2_normalize(uniform_quantize(
            base @ W,q_bits=spec.q_bits,clip=spec.clip))
        if not np.array_equal(guard,reconstructed):
            raise ValueError("CANONICAL_GUARD_FOUR_CORNER_MISMATCH")
    for item in (base,guard,projection_only,quantization_only):
        if not np.isfinite(item).all():raise ValueError("NONFINITE_REPRESENTATION")
    if spec.proj_dim==768:
        if not np.array_equal(quantization_only,guard):
            raise ValueError("EPS64_QUANT_ONLY_NOT_GUARD_ALIAS")
        if not np.array_equal(projection_only,base):
            raise ValueError("EPS64_PROJECTION_ONLY_NOT_RAW_ALIAS")
    return {"RAW":base,"GUARD":guard,"PROJECTION_ONLY":projection_only,
            "QUANTIZATION_ONLY":quantization_only,"matrix_sha256":matrix_sha,
            "projection_dim":spec.proj_dim,"bits":spec.q_bits}

def paired_representation(query,documents,epsilon,seed):
    """Same canonical projection seed (no offset) and identical fixed base arrays."""
    q=guarded_four_corner(query,epsilon,seed)
    d=guarded_four_corner(documents,epsilon,seed)
    if q["matrix_sha256"]!=d["matrix_sha256"]:
        raise ValueError("QUERY_DOCUMENT_PROJECTION_GEOMETRY_MISMATCH")
    return {"query":q,"documents":d}

def rank_scored_ids(ids,scores,k=10):
    """Full-precision DESC score, Unicode stable ID ASC; retain scored rank 11."""
    a=np.asarray(scores)
    if not isinstance(ids,(list,tuple)) or len(ids)!=len(a) or len(ids)<k+1:
        raise ValueError("RANK_INPUT_TOO_SHORT_OR_MISMATCH")
    if len(set(ids))!=len(ids) or any(not isinstance(x,str) or not x for x in ids):
        raise ValueError("RANK_IDS_DUPLICATED_OR_INVALID")
    if a.ndim!=1 or not np.issubdtype(a.dtype,np.number) or not np.isfinite(a).all():
        raise ValueError("NONFINITE_OR_INVALID_RANK_SCORES")
    items=sorted(zip(ids,a.tolist()),key=lambda entry:(-entry[1],entry[0]))
    tied=Counter(score for _,score in items)
    top=[{"rank":i+1,"electronics_id":eid,"score":score}
         for i,(eid,score) in enumerate(items[:k+1])]
    return {"top_scored":top,"boundary_score_margin":items[k-1][1]-items[k][1],
            "boundary_exact_tie":items[k-1][1]==items[k][1],
            "exact_tied_score_groups":sum(v>1 for v in tied.values()),
            "exact_tied_score_members":sum(v for v in tied.values() if v>1)}

def require_mps_available(mps_available,requested_device="mps"):
    """Never silently switch scientific runs from predeclared MPS to CPU."""
    if requested_device!="mps":raise ValueError("UNREGISTERED_ENCODER_DEVICE")
    if mps_available is not True:raise ValueError("MPS_DEVICE_UNAVAILABLE")
    return "mps"

def require_external_audit_dir(root,destination):
    root=Path(root).resolve()
    dest=Path(destination).resolve()
    if dest.exists() or dest==root or root in dest.parents:
        raise ValueError("AUDIT_OUTPUT_EXISTS_OR_IN_RESEARCH_TREE")
    if "_repro_audits" not in dest.parts:
        raise ValueError("AUDIT_OUTPUT_NOT_IN_REPRO_AUDITS")
    return dest
