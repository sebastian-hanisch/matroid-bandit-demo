"""Eigenschaftstests (Schicht „Eigenschaften“): Invarianten auf Zufallsinstanzen mit festem Seed."""

import mbd_algorithm as A
import mbd_constants as C
import mbd_evaluation as ev
from mbd_scenario import make_instance, make_means

PLAN = ev.Settings()


def _plan(cons="wald", delta=0.2, mus="zwei", k=3):
    s = ev.Settings(cons=cons, k=k, delta=delta, mus=mus)
    b = ev.build(s)
    return b["mat"], b["mu"]


def test_regret_is_never_negative_and_the_curve_never_decreases_for_all_algorithms():
    for cons in C.CONSTRAINTS:
        mat, mu = _plan(cons)
        bases = A.enumerate_bases(mat)
        for algo in C.ALGOS:
            if algo == "ubas" and bases is None:
                continue
            curve = A.simulate(mat, mu, algo, 300, 5, 1.5, bases)["curve"]
            assert all(x >= -1e-12 for x in curve) and all(b >= a - 1e-12 for a, b in zip(curve, curve[1:])), (cons, algo)


def test_omm_pulls_every_arm_within_a_few_rounds():
    for cons in C.CONSTRAINTS:
        mat, mu = _plan(cons)
        r = A.simulate(mat, mu, "omm", 3 * mat.n, 1, 1.5)
        assert all(c >= 1 for c in r["pulls"]), cons


def test_a_larger_constant_explores_more_suboptimal_arms():
    mat, mu = _plan("wald", 0.4)
    bad = {c: sum(sum(A.simulate(mat, mu, "omm", 600, seed, c)["bad"]) for seed in range(8)) for c in (0.1, 0.25, 0.5, 1.0, 1.5)}
    assert bad[0.1] < bad[0.5] < bad[1.5] and bad[0.25] < bad[1.0] and bad[0.1] < bad[1.0]


def test_the_random_basis_has_linear_regret_with_the_expected_rate():
    mat, mu = _plan("wald", 0.2)
    r = A.simulate(mat, mu, "zufall", 4000, 2)
    first, whole = r["curve"][1999] / 2000, r["curve"][3999] / 4000
    assert abs(first - whole) < 0.03 * whole and r["curve"][3999] > 2 * r["curve"][1999] * 0.9


def test_omm_finds_the_best_basis_with_a_large_gap_and_enough_rounds():
    for cons in C.CONSTRAINTS:
        mat, mu = _plan(cons, 0.4)
        r = A.simulate(mat, mu, "omm", 1500, 4, 0.25)
        assert r["ok"], cons


def test_the_increment_per_doubling_levels_off_for_a_large_gap_but_not_for_a_small_one():
    big = {r["delta"]: r for r in ev.ex2_series()}
    assert big[0.4]["in_phase"] and not big[0.05]["in_phase"]
    inc = big[0.05]["increments"]
    assert inc[-1] > 1.5 * inc[0]                                                                  # bei Δ = 0,05 wächst der Zuwachs noch stark


def test_regret_depends_on_the_gap_but_not_on_the_matroid_kind_at_equal_arms_and_rank():
    res = ev.ex4_series()
    for wald, card in zip([r for r in res["vs"] if r["matroid"] == "Wald"], [r for r in res["vs"] if r["matroid"] == "Kardinalität"]):
        assert abs(wald["regret"] - card["regret"]) < 0.15 * max(wald["regret"], card["regret"]), wald["v"]


def test_regret_at_fixed_horizon_is_not_monotone_in_the_gap():
    rows = ev.ex3_series()
    for name in ("Wald", "Kardinalität 3"):
        by = {r["delta"]: r["regret"] for r in rows if r["matroid"] == name}
        peak = max(by, key=by.get)
        assert 0.05 < peak < 0.5 and by[0.02] < 0.6 * by[peak] and by[0.5] < by[peak]


def test_the_structure_free_baseline_does_not_learn_in_the_shown_horizon():
    rows = {(r["matroid"], r["algo"]): r["mean"][2000] for r in ev.ex1_series()}
    for m in ("Wald", "Kardinalität 3", "4 Farben"):
        assert rows[(m, "ubas")] > 0.9 * rows[(m, "zufall")] and rows[(m, "omm")] < 0.4 * rows[(m, "zufall")] and rows[(m, "omm025")] < rows[(m, "omm")]


def test_instances_and_means_are_reproducible_and_valid():
    for inst, v in (("plan", 8), ("gross", 6)):
        a, b = make_instance(inst, v, 4), make_instance(inst, v, 4)
        assert a == b
        mat = A.make_matroid("wald", a.m, 0, a.edges, a.n)
        mu = make_means(mat, "zwei", 0.2, 4)
        assert mu == make_means(mat, "zwei", 0.2, 4) and set(round(x, 9) for x in mu) == {0.4, 0.6}
        assert len(A.greedy_basis(mat, mu)) == a.n - 1 and all(abs(g - 0.2) < 1e-9 for g in A.gaps(mat, mu).values())
        z = make_means(mat, "zufall", 0.2, 4)
        assert all(0.1 <= x <= 0.9 for x in z)
