import math

import pytest

from electronics.bm25_fixed import (
    B,
    K1,
    FixedBM25,
    tokenize,
)


def test_nfkc_casefold():
    assert tokenize("ＡＢＣ １２") == [
        "w:abc", "w:12"
    ]


def test_hangul_bigrams():
    assert tokenize("가나다") == [
        "w:가나다",
        "ko2:가나",
        "ko2:나다",
    ]


def test_single_hangul():
    assert tokenize("가") == ["w:가"]


def test_no_cross_run_bigram():
    assert tokenize("가나 다라") == [
        "w:가나", "ko2:가나",
        "w:다라", "ko2:다라",
    ]


def test_document_frequency():
    bm = FixedBM25([
        ("a", "alpha alpha"),
        ("b", "alpha beta"),
    ])

    assert bm.df["w:alpha"] == 2
    assert bm.tf[0]["w:alpha"] == 2


def test_query_deduplication():
    bm = FixedBM25([
        ("a", "alpha alpha"),
        ("b", "beta"),
    ])

    assert bm.score("alpha") == bm.score(
        "alpha alpha alpha"
    )


def test_exact_formula():
    bm = FixedBM25([
        ("a", "alpha alpha"),
        ("b", "beta"),
    ])

    idf = math.log1p(
        (2 - 1 + 0.5) / (1 + 0.5)
    )

    expected = (
        idf * 2 * (K1 + 1)
        / (
            2 + K1 * (
                1 - B + B * 2 / bm.avgdl
            )
        )
    )

    assert bm.score("alpha")[0] == pytest.approx(
        expected, rel=1e-14
    )


def test_corpus_dependent_idf():
    a = FixedBM25([
        ("a", "alpha"),
        ("b", "beta"),
    ])

    b = FixedBM25([
        ("a", "alpha"),
        ("b", "beta"),
        ("c", "gamma"),
    ])

    assert a.idf["w:alpha"] != b.idf["w:alpha"]


def test_tie_break():
    bm = FixedBM25([
        ("z", "alpha"),
        ("a", "alpha"),
    ])

    assert [
        x.playbook_id
        for x in bm.rank("alpha")
    ] == ["a", "z"]


def test_top11():
    bm = FixedBM25([
        (f"id{i:02d}", "alpha")
        for i in range(15)
    ])

    result = bm.top11("alpha")

    assert len(result) == 11
    assert result[-1].rank == 11


def test_empty_corpus():
    with pytest.raises(ValueError):
        FixedBM25([])


def test_empty_token_corpus():
    with pytest.raises(ValueError):
        FixedBM25([
            ("a", "!!!"),
        ])


def test_duplicate_id():
    with pytest.raises(ValueError):
        FixedBM25([
            ("a", "alpha"),
            ("a", "beta"),
        ])


def test_absent_term():
    bm = FixedBM25([
        ("a", "alpha"),
    ])

    assert bm.score("gamma") == [0.0]


def test_no_e5_prefix_injection():
    assert tokenize("alpha") == ["w:alpha"]


def test_invalid_text():
    with pytest.raises(TypeError):
        tokenize(None)


def test_full_ranking_preserved():
    bm = FixedBM25([
        ("a", "alpha"),
        ("b", "beta"),
        ("c", "gamma"),
    ])

    assert len(bm.rank("alpha")) == 3


def test_invalid_limit():
    bm = FixedBM25([
        ("a", "alpha"),
    ])

    with pytest.raises(ValueError):
        bm.rank("alpha", limit=0)
