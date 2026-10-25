# repo/src/guard_repr.py
from __future__ import annotations
import numpy as np
from dataclasses import dataclass

def l2_normalize(x: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    n = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.clip(n, eps, None)

@dataclass(frozen=True)
class ReprSpec:
    proj_dim: int        # projected dimension
    q_bits: int          # quantization bits (e.g., 4/6/8/10/12/16)
    clip: float = 1.0    # clip range before quantization (assume embeddings roughly in [-1,1])

def eps_to_repr_spec(eps: int, d_in: int) -> ReprSpec:
    """
    Protocol v1 eps ∈ {0,2,4,8,16,32,64}
    eps가 커질수록 제약이 완화되도록 설계:
      - eps=0  -> 강제약: proj_dim=128, q_bits=4
      - eps=64 -> 약제약: proj_dim=d_in, q_bits=16 (거의 raw)
    """
    # eps를 레벨로 매핑(0~6)
    levels = {0:0, 2:1, 4:2, 8:3, 16:4, 32:5, 64:6}
    if eps not in levels:
        raise ValueError(f"eps must be one of {sorted(levels.keys())}, got {eps}")
    lvl = levels[eps]

    # proj_dim 스케줄: 128 -> 160 -> 192 -> 224 -> 256 -> 320 -> d_in
    dim_table = [128, 160, 192, 224, 256, 320, d_in]
    proj_dim = dim_table[lvl]
    proj_dim = min(proj_dim, d_in)

    # q_bits 스케줄: 4 -> 5 -> 6 -> 7 -> 8 -> 10 -> 16
    bits_table = [4, 5, 6, 7, 8, 10, 16]
    q_bits = bits_table[lvl]

    return ReprSpec(proj_dim=proj_dim, q_bits=q_bits, clip=1.0)

def make_projection_matrix(d_in: int, d_out: int, seed: int) -> np.ndarray:
    """
    Random Gaussian projection matrix with 1/sqrt(d_out) scaling.
    Deterministic via seed.
    """
    rng = np.random.default_rng(seed)
    W = rng.normal(0.0, 1.0, size=(d_in, d_out)).astype(np.float32)
    W /= np.sqrt(float(d_out))
    return W

def uniform_quantize(x: np.ndarray, q_bits: int, clip: float = 1.0) -> np.ndarray:
    """
    Symmetric uniform quantization to q_bits in [-clip, clip].
    Returns de-quantized float32 (so downstream FAISS works unchanged).
    """
    x = np.clip(x, -clip, clip)
    # levels per side
    q_levels = (2 ** q_bits) - 1  # e.g., 15 for 4-bit
    # map [-clip, clip] -> [0, q_levels]
    scaled = (x + clip) * (q_levels / (2 * clip))
    q = np.round(scaled)
    # dequantize back to [-clip, clip]
    x_hat = (q * (2 * clip) / q_levels) - clip
    return x_hat.astype(np.float32)

def apply_guard_repr(emb: np.ndarray, eps: int, seed: int) -> np.ndarray:
    """
    Structural-constraint Guard:
      1) L2 normalize
      2) random projection (if proj_dim < d_in)
      3) uniform quantize (q_bits)
      4) L2 normalize
    """
    emb = emb.astype(np.float32, copy=False)
    emb = l2_normalize(emb)

    n, d_in = emb.shape
    spec = eps_to_repr_spec(eps, d_in=d_in)

    # projection
    if spec.proj_dim < d_in:
        W = make_projection_matrix(d_in, spec.proj_dim, seed=seed)
        emb = emb @ W  # (n, d_out)
    # quantization
    emb = uniform_quantize(emb, q_bits=spec.q_bits, clip=spec.clip)
    emb = l2_normalize(emb)
    return emb
