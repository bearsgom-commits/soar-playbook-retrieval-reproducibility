"""Behavioral checks of the publicly released Guard representation function.

These deterministic tests are NOT a replay of the paper's E5 embeddings,
retrieval results, or original scientific environment.
"""
import numpy as np
import pytest

from guard_repr import apply_guard_repr, eps_to_repr_spec, make_projection_matrix, l2_normalize

@pytest.mark.parametrize(
    ("epsilon", "dimension", "bits"),
    [(0, 128, 4), (2, 160, 5), (4, 192, 6),
     (8, 224, 7), (16, 256, 8), (32, 320, 10), (64, 768, 16)],
)
def test_control_mapping(epsilon, dimension, bits):
    spec = eps_to_repr_spec(epsilon, d_in=768)
    assert (spec.proj_dim, spec.q_bits) == (dimension, bits)

def test_unsupported_epsilon_fails():
    with pytest.raises(ValueError):
        eps_to_repr_spec(7, d_in=768)

def test_gaussian_projection_deterministic():
    a = make_projection_matrix(768, 256, 13)
    b = make_projection_matrix(768, 256, 13)
    c = make_projection_matrix(768, 256, 42)
    assert a.dtype == np.float32
    np.testing.assert_array_equal(a, b)
    assert not np.array_equal(a, c)

@pytest.mark.parametrize("epsilon", [0, 8, 16, 32, 64])
def test_guard_deterministic_shape_and_normalization(epsilon):
    x = np.random.default_rng(17).normal(size=(6, 768)).astype(np.float32)
    actual = apply_guard_repr(x, epsilon, seed=13)
    repeated = apply_guard_repr(x, epsilon, seed=13)
    assert actual.shape == (6, eps_to_repr_spec(epsilon, 768).proj_dim)
    assert actual.dtype == np.float32
    np.testing.assert_array_equal(actual, repeated)
    np.testing.assert_allclose(
        np.linalg.norm(actual, axis=1), np.ones(6), rtol=1e-5, atol=1e-6
    )

def test_epsilon64_is_not_the_raw_baseline():
    x = np.random.default_rng(123).normal(size=(8, 768)).astype(np.float32)
    raw_normalized = l2_normalize(x)
    guarded = apply_guard_repr(x, 64, seed=7)
    assert guarded.shape == raw_normalized.shape
    assert not np.array_equal(guarded, raw_normalized)

def test_seed_changes_projected_representation():
    x = np.random.default_rng(123).normal(size=(3, 768)).astype(np.float32)
    a = apply_guard_repr(x, 16, seed=7)
    b = apply_guard_repr(x, 16, seed=13)
    assert not np.array_equal(a, b)
