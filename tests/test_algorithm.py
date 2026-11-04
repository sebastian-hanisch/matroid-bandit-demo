"""Kern an Handrechnungen (DEMO-PLAYBOOK §1b): Greedy, Lücken, Index, Basen zählen und aufzählen, die Läufe."""

import math

import pytest

import mbd_algorithm as A


def test_greedy_and_best_basis_by_hand(drei_arme, card2, dreieck):
    assert A.greedy_basis(*drei_arme) == [0] and A.best_basis(*drei_arme) == ([0], 0.9)
    mat, mu = card2
    b, val = A.best_basis(mat, mu)
    assert b == [0, 1] and val == pytest.approx(1.7)
    mat, mu = dreieck
    b, val = A.best_basis(mat, mu)
    assert sorted(b) == [0, 1, 3] and val == pytest.approx(1.6)                  # ab, bc, cd; ac würde das Dreieck schließen


def test_gaps_by_hand(card2, dreieck):
    mat, mu = card2
    g = A.gaps(mat, mu)
    assert set(g) == {2, 3} and g[2] == pytest.approx(0.5) and g[3] == pytest.approx(0.6)           # min(0,9; 0,8) − 0,3 und − 0,2
    mat, mu = dreieck
    assert A.gaps(mat, mu) == {2: pytest.approx(0.2)}                                              # ac liegt im Kreis ab, bc, ac: min(0,9; 0,6) − 0,4


def test_omm_index_by_hand():
    idx = A.omm_index([2, 1, 1], [1.8, 0.5, 0.1], 5, 1.5)
    assert idx[0] == pytest.approx(0.9 + math.sqrt(1.5 * math.log(5) / 2)) and idx[0] == pytest.approx(1.9986, abs=1e-4)
    assert idx[1] == pytest.approx(0.5 + math.sqrt(1.5 * math.log(5))) and idx[1] == pytest.approx(2.0538, abs=1e-4)
    assert idx[2] == pytest.approx(1.6538, abs=1e-4)
    assert A.omm_index([0, 3], [0.0, 1.0], 7, 1.5)[0] == math.inf and A.omm_index([0], [0.0], 1, 1.5) == [math.inf]
    assert A.omm_index([1], [1.0], 1, 1.5) == [1.0]                                                # ln 1 = 0: kein Bonus


def test_the_three_arm_example_without_noise(drei_arme):
    mat, mu = drei_arme
    counts, sums, seq, regret = [0] * 3, [0.0] * 3, [], 0.0
    for t in range(1, 13):
        e = A.greedy_basis(mat, A.omm_index(counts, sums, t, 1.5))[0]
        seq.append(e)
        counts[e] += 1
        sums[e] += mu[e]
        regret += 0.9 - mu[e]
    assert seq == [0, 1, 2, 0, 1, 0, 0, 2, 0, 1, 0, 0] and counts == [7, 3, 2] and regret == pytest.approx(2.8)
    idx5 = A.omm_index([2, 1, 1], [1.8, 0.5, 0.1], 5, 1.5)                                         # t = 5: Arm 1 liegt vor Arm 0 (optimistisches Erkunden)
    assert idx5[1] > idx5[0]


def test_count_bases_by_hand(dreieck):
    assert A.count_bases(dreieck[0]) == 3
    k5 = A.make_matroid("wald", 10, 0, [(a, b) for a in range(5) for b in range(a + 1, 5)], 5)
    assert A.count_bases(k5) == 125 == 5 ** 3
    assert A.count_bases(A.make_matroid("card", 14, 3)) == 364 and A.count_bases(A.make_matroid("card", 3, 5)) == 1
    assert A.count_bases(A.make_matroid("farbe", 14, 4)) == 4 * 4 * 3 * 3                          # Klassen {0, 4, 8, 12}, {1, 5, 9, 13}, {2, 6, 10}, {3, 7, 11}


def test_enumerate_bases_by_hand(dreieck, card2):
    bases = A.enumerate_bases(dreieck[0])
    assert sorted(sorted(b) for b in bases) == [[0, 1, 3], [0, 2, 3], [1, 2, 3]]
    assert len(A.enumerate_bases(card2[0])) == 6
    assert A.enumerate_bases(A.make_matroid("card", 30, 5)) is None and A.enumerate_bases(A.make_matroid("card", 30, 5), limit=10 ** 6) is not None
    assert A.enumerate_bases(A.make_matroid("wald", 21, 0, [(a, b) for a in range(7) for b in range(a + 1, 7)], 7)) is None     # 16 807 Spannbäume


def test_matroid_oracles_by_hand(dreieck):
    mat, _ = dreieck
    assert mat.independent([0, 1, 3]) and not mat.independent([0, 1, 2]) and mat.rank() == 3
    farbe = A.make_matroid("farbe", 6, 3)
    assert farbe.cls == (0, 1, 2, 0, 1, 2) and farbe.independent([0, 1, 2]) and not farbe.independent([0, 3]) and farbe.rank() == 3
    card = A.make_matroid("card", 5, 2)
    assert card.independent([0, 1]) and not card.independent([0, 1, 2]) and card.rank() == 2
    with pytest.raises(ValueError):
        A.make_matroid("kreis", 3, 1)


def test_simulate_returns_a_consistent_record(card2):
    mat, mu = card2
    r = A.simulate(mat, mu, "omm", 50, 7, 1.5, record=True)
    assert len(r["curve"]) == 50 == len(r["choices"]) == len(r["rewards"]) and all(len(b) == 2 for b in r["choices"])
    assert sum(r["pulls"]) == 100 and r["regret"] == pytest.approx(r["curve"][-1])
    recomputed = sum(1.7 - sum(mu[e] for e in b) for b in r["choices"])
    assert recomputed == pytest.approx(r["regret"]) and r["last"] == r["choices"][-1] and r["ok"] == (set(r["last"]) == {0, 1})
    assert all(b >= 0 for b in r["bad"]) and sum(r["bad"]) == sum(1 for b in r["choices"] for e in b if e in (2, 3))
    assert A.simulate(mat, mu, "omm", 50, 7, 1.5)["curve"] == r["curve"]                                 # deterministisch
    assert A.simulate(mat, mu, "omm", 50, 8, 1.5)["curve"] != r["curve"]


def test_simulate_rejects_unknown_algorithm_and_missing_bases(card2):
    with pytest.raises(ValueError):
        A.simulate(*card2[:1], card2[1], "thompson", 5, 1)
    with pytest.raises(ValueError):
        A.simulate(card2[0], card2[1], "ubas", 5, 1)


def test_ubas_tries_every_basis_once_first(card2):
    mat, mu = card2
    bases = A.enumerate_bases(mat)
    r = A.simulate(mat, mu, "ubas", len(bases) + 3, 3, 1.5, bases, record=True)
    first = [tuple(sorted(b)) for b in r["choices"][: len(bases)]]
    assert sorted(first) == sorted(tuple(sorted(b)) for b in bases)
