"""Orakel (ORACLE-PLAYBOOK §5): unabhängig geschriebene, einfache Gegenproben für Greedy, Lücken, Basenzahl und das Bedauern."""

import itertools
import random

import pytest

import mbd_algorithm as A

SEED = 20261127


def _random_matroid(rng, kind=None):
    kind = kind or rng.choice(["card", "farbe", "wald"])
    if kind == "card":
        return A.make_matroid("card", rng.randint(3, 8), rng.randint(1, 4))
    if kind == "farbe":
        return A.make_matroid("farbe", rng.randint(3, 8), rng.randint(1, 4))
    nodes = rng.randint(3, 5)
    edges = [(a, b) for a in range(nodes) for b in range(a + 1, nodes)]
    rng.shuffle(edges)
    chosen = sorted(edges[: rng.randint(nodes - 1, len(edges))])
    return A.make_matroid("wald", len(chosen), 0, chosen, nodes)


def _all_bases(mat):
    """Alle Basen durch Aufzählung aller Mengen der Größe des Rangs (einfach, ohne die Aufzähler der App)."""
    r = mat.rank()
    return [list(c) for c in itertools.combinations(range(mat.n), r) if mat.independent(c)]


def test_fast_greedy_equals_the_simple_greedy_on_random_matroids():
    rng = random.Random(SEED)
    for _ in range(300):
        mat = _random_matroid(rng)
        w = [rng.choice([0.1, 0.2, 0.5, 0.7, 0.9]) for _ in range(mat.n)]                          # viele Gleichstände
        assert A.greedy_basis(mat, w) == mat.greedy_naive(w)                                       # auch in derselben Reihenfolge der Aufnahme


def test_best_basis_equals_the_maximum_over_all_bases():
    rng = random.Random(SEED + 1)
    for _ in range(100):
        mat = _random_matroid(rng)
        mu = [rng.random() for _ in range(mat.n)]
        assert A.best_basis(mat, mu)[1] == pytest.approx(max(sum(mu[e] for e in b) for b in _all_bases(mat)))


def test_gaps_equal_the_loss_of_the_best_basis_containing_the_arm():
    """Δ_e = μ(B*) − max über alle Basen B mit e von μ(B): Aufzählung statt Kreisformel."""
    rng = random.Random(SEED + 2)
    for _ in range(120):
        mat = _random_matroid(rng)
        mu = [rng.random() for _ in range(mat.n)]
        bases = _all_bases(mat)
        opt = A.best_basis(mat, mu)[1]
        best = set(A.greedy_basis(mat, mu))
        got = A.gaps(mat, mu)
        assert set(got) == set(range(mat.n)) - best
        for e, delta in got.items():
            with_e = [sum(mu[x] for x in b) for b in bases if e in b]
            assert delta == pytest.approx(opt - max(with_e)), (mat.kind, e)


def test_count_bases_equals_the_enumeration():
    rng = random.Random(SEED + 3)
    for _ in range(80):
        mat = _random_matroid(rng)
        assert A.count_bases(mat) == len(_all_bases(mat)), mat.kind


def test_kirchhoff_equals_cayley_on_complete_graphs():
    for v in range(2, 8):
        edges = [(a, b) for a in range(v) for b in range(a + 1, v)]
        assert A.count_bases(A.make_matroid("wald", len(edges), 0, edges, v)) == (v ** (v - 2) if v > 1 else 1)


def test_enumerate_bases_equals_the_simple_enumeration():
    rng = random.Random(SEED + 4)
    for _ in range(60):
        mat = _random_matroid(rng)
        assert sorted(sorted(b) for b in A.enumerate_bases(mat)) == sorted(sorted(b) for b in _all_bases(mat))


def test_regret_equals_the_recomputation_from_the_choices():
    rng = random.Random(SEED + 5)
    for algo in ("omm", "eps", "zufall"):
        mat = _random_matroid(rng, "wald")
        mu = [rng.uniform(0.1, 0.9) for _ in range(mat.n)]
        r = A.simulate(mat, mu, algo, 120, 11, 1.5, record=True)
        opt = A.best_basis(mat, mu)[1]
        cum, curve = 0.0, []
        for b in r["choices"]:
            assert mat.independent(b) and len(b) == len(set(b)) == mat.rank()
            cum += opt - sum(mu[e] for e in b)
            curve.append(cum)
        assert curve == pytest.approx(r["curve"]) and all(x >= -1e-12 for x in curve)


def test_observed_means_equal_the_sum_of_draws_over_the_pulls():
    rng = random.Random(SEED + 6)
    mat = _random_matroid(rng, "card")
    mu = [rng.uniform(0.2, 0.8) for _ in range(mat.n)]
    r = A.simulate(mat, mu, "omm", 80, 3, 1.5, record=True)
    assert sum(r["rewards"]) == pytest.approx(sum(m * c for m, c in zip((x if x is not None else 0 for x in r["means"]), r["pulls"])))
    assert all(m is None or 0.0 <= m <= 1.0 for m in r["means"]) and [m is None for m in r["means"]] == [c == 0 for c in r["pulls"]]
