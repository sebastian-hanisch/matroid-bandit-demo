"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): kleinste Fälle, Gleichstände, k = 1, Reglergrenzen, Spielwiese."""

import math
import random

import pytest

import mbd_algorithm as A
import mbd_constants as C
import mbd_evaluation as ev
from mbd_scenario import make_instance, make_means


def test_one_arm_and_a_trivial_matroid_have_no_regret():
    mat = A.make_matroid("card", 1, 1)
    for algo in ("omm", "eps", "zufall"):
        r = A.simulate(mat, [0.4], algo, 20, 1)
        assert r["regret"] == 0.0 and r["ok"] and r["pulls"] == [20]
    free = A.make_matroid("card", 5, 9)                                    # k > n: jede Menge ist eine Basis, es gibt nur eine
    assert A.count_bases(free) == 1 and A.simulate(free, [0.1, 0.5, 0.9, 0.3, 0.7], "omm", 30, 2)["regret"] == 0.0


def test_one_round_and_equal_means():
    mat = A.make_matroid("card", 4, 2)
    r = A.simulate(mat, [0.6, 0.5, 0.4, 0.3], "omm", 1, 1)
    assert len(r["curve"]) == 1 and r["pulls"] == [1, 1, 0, 0] and r["curve"] == [0.0]            # t = 1: alle Indizes ∞, Greedy nimmt die ersten beiden: zufällig die beste Basis
    same = A.simulate(mat, [0.5] * 4, "omm", 200, 1)
    assert same["regret"] == 0.0                                           # alle Basen gleich gut: kein Bedauern, kein Lücken


def test_one_color_and_k_equal_one():
    one = A.make_matroid("farbe", 5, 1)
    assert set(one.cls) == {0} and A.count_bases(one) == 5 and one.rank() == 1
    assert A.gaps(one, [0.9, 0.5, 0.4, 0.3, 0.2]) == {1: pytest.approx(0.4), 2: pytest.approx(0.5), 3: pytest.approx(0.6), 4: pytest.approx(0.7)}


def test_gaps_of_a_basis_without_outside_arms_is_empty():
    mat = A.make_matroid("card", 3, 5)
    assert A.gaps(mat, [0.1, 0.2, 0.3]) == {}
    b = ev.build(ev.Settings("plan", 8, 4, "card", 14))                    # k = Zahl der Leitungen: alle Arme in der Basis
    assert b["gaps"] == {} and b["min_gap"] == math.inf and b["n_bases"] == 1


def test_ubas_is_skipped_above_the_limit_and_the_verdict_says_so():
    s = ev.Settings("gross", 12)
    v = ev.run_view(s)
    assert "ubas" not in v["runs"] and v["b"]["bases"] is None
    kind, text = ev.verdict_run(s, v)
    assert kind == "info" and "nicht anwendbar" in text and ev.run_rows(s, v)[-1]["Bedauern"] == "–"


def test_instance_generation_is_valid_at_every_size():
    for inst, v in (("plan", 6), ("gross", C.V_MIN), ("gross", C.V_MAX)):
        a = make_instance(inst, v, 5)
        assert a == make_instance(inst, v, 5) and a.m == (C.PLAN_EDGES if inst == "plan" else v * (v - 1) // 2)
    with pytest.raises(ValueError):
        make_instance("gross", 40, 1)
    with pytest.raises(ValueError):
        make_means(A.make_matroid("card", 3, 1), "dreieck", 0.2, 1)


def test_every_regler_corner_gives_consistent_numbers():
    for inst in C.INSTANCES:
        for cons in C.CONSTRAINTS:
            for mus in C.MEANS:
                for delta in (C.DELTAS[0], C.DELTAS[-1]):
                    s = ev.Settings(inst, C.V_MIN, 0, cons, C.K_MAX, mus, delta, C.T_CHOICES[0], C.C_CHOICES[0], 0)
                    v = ev.run_view(s)
                    assert all(r["regret"] >= -1e-9 for r in v["runs"].values()) and ev.verdict_run(s, v)[0] == "info"
                    assert len(ev.run_rows(s, v)) == 4 and len(ev.element_rows(v)) == v["b"]["inst"].m


def test_curve_points_always_end_at_the_last_round():
    curve = list(range(1, 1001))
    xs, ys = ev.curve_points(curve)
    assert xs[-1] == 1000 and ys[-1] == 1000 and len(xs) <= C.CURVE_POINTS + 1
    xs, ys = ev.curve_points([1.0, 2.0, 3.0])
    assert xs == [1, 2, 3]
    assert ev.curve_points([5.0]) == ([1], [5.0])


def test_play_view_is_consistent_with_the_simulation():
    s = ev.Settings()
    for steps in (0, 1, 7, 100):
        p = ev.play_view(s, steps)
        assert p["steps"] == steps and len(p["choices"]) == steps and len(p["round_regret"]) == steps
        if steps:
            r = A.simulate(ev.build(s)["mat"], ev.build(s)["mu"], "omm", steps, s.rseed, s.c)
            assert p["regret"] == pytest.approx(r["regret"]) and sum(p["round_regret"]) == pytest.approx(p["regret"]) and p["curve"] == r["curve"]
    p0 = ev.play_view(s, 0)
    assert all(x == math.inf for x in p0["index"]) and p0["curve"] == [] and ev.play_round_rows(p0) == []
    assert ev.play_view(s, 100)["choices"][:50] == ev.play_view(s, 50)["choices"]                       # Präfix-Konsistenz
    rows = ev.play_rows(ev.play_view(s, 5))
    assert len(rows) == ev.build(s)["inst"].m and ev.play_round_rows(ev.play_view(s, 12))[0]["Runde"] == 12 and len(ev.play_round_rows(ev.play_view(s, 12))) == 8


def test_random_orders_in_eps_greedy_are_permutations():
    rng = random.Random(1)
    for _ in range(20):
        o = A._random_order(rng, 9)
        assert sorted(o) == list(range(9))
