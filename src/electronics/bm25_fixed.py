"""Fixed E04 lexical BM25 implementation.

No E5 prefixes, evaluation labels, epsilon or seed are
introduced by this module.

Scientific corpus execution is deliberately separate.
"""

from collections import Counter
from dataclasses import dataclass
import math
import re
import unicodedata

TOKEN_PATTERN = re.compile(
    r"[가-힣]+|[a-z]+|[0-9]+"
)

K1 = 1.2
B = 0.75


def tokenize(text: str) -> list[str]:
    if not isinstance(text, str):
        raise TypeError("BM25 text must be str")

    normalized = unicodedata.normalize(
        "NFKC", text
    ).casefold()

    tokens = []

    for match in TOKEN_PATTERN.finditer(normalized):
        run = match.group()
        tokens.append("w:" + run)

        if re.fullmatch(r"[가-힣]+", run):
            for i in range(len(run) - 1):
                tokens.append(
                    "ko2:" + run[i:i + 2]
                )

    return tokens


@dataclass(frozen=True)
class RankedDocument:
    playbook_id: str
    rank: int
    score: float


class FixedBM25:
    def __init__(
        self,
        documents: list[tuple[str, str]]
    ):
        if not documents:
            raise ValueError("Empty BM25 corpus")

        ids = [item[0] for item in documents]

        if any(
            not isinstance(i, str) or not i.strip()
            for i in ids
        ):
            raise ValueError("Invalid playbook ID")

        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate playbook ID")

        self.ids = tuple(ids)
        self.tf = []
        self.dl = []
        self.df = Counter()

        for _, text in documents:
            tokens = tokenize(text)
            counts = Counter(tokens)

            self.tf.append(counts)
            self.dl.append(len(tokens))
            self.df.update(counts.keys())

        self.n = len(documents)
        self.avgdl = sum(self.dl) / self.n

        if self.avgdl == 0:
            raise ValueError("avgdl=0")

        self.idf = {
            term: math.log1p(
                (
                    self.n - freq + 0.5
                ) / (freq + 0.5)
            )
            for term, freq in self.df.items()
        }

    def score(self, query: str) -> list[float]:
        terms = set(tokenize(query))
        scores = []

        for counts, dl in zip(
            self.tf, self.dl
        ):
            norm = K1 * (
                1 - B + B * dl / self.avgdl
            )

            total = 0.0

            # Canonical summation order avoids dependence
            # on Python set iteration order.
            for term in sorted(terms):
                tf = counts.get(term, 0)

                if not tf:
                    continue

                total += (
                    self.idf[term]
                    * tf * (K1 + 1)
                    / (tf + norm)
                )

            if not math.isfinite(total):
                raise ValueError(
                    "Nonfinite BM25 score"
                )

            scores.append(total)

        return scores

    def rank(
        self,
        query: str,
        limit: int | None = None
    ) -> list[RankedDocument]:
        scores = self.score(query)

        order = sorted(
            range(self.n),
            key=lambda i: (
                -scores[i],
                self.ids[i]
            )
        )

        if limit is not None:
            if (
                not isinstance(limit, int)
                or isinstance(limit, bool)
                or limit < 1
            ):
                raise ValueError(
                    "Invalid ranking limit"
                )

            order = order[:limit]

        return [
            RankedDocument(
                playbook_id=self.ids[i],
                rank=rank,
                score=scores[i]
            )
            for rank, i in enumerate(
                order, start=1
            )
        ]

    def top11(
        self, query: str
    ) -> list[RankedDocument]:
        return self.rank(
            query,
            limit=min(11, self.n)
        )
