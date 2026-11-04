"""Jede Zahl der README („Befunde“) wird hier mit den Funktionen der App nachgerechnet (DEMO-PLAYBOOK §4)."""

from pathlib import Path

import mbd_algorithm as A
import mbd_constants as C
import mbd_evaluation as ev

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")


def _r(x):
    return ev.de(x, 1)


EXAMPLES = {
    "Standardfall (Plan, Wald, Lücke 0,2, 2 000 Runden, c = 1,5)": "Standardfall (Voreinstellung)",
    "Kleine Konstante (c = 0,25)": "Kleine Konstante",
    "Kleine Lücke (Lücke 0,05, 5 000 Runden)": "Kleine Lücke",
    "Viele Arme (12 Standorte, Wald)": "Viele Arme",
    "Ohne Struktur (4 Farben)": "Ohne Struktur",
}


def test_the_example_table():
    for name, preset in EXAMPLES.items():
        s = ev.Settings(**C.PRESETS[preset])
        v = ev.run_view(s)
        runs = v["runs"]
        ubas = _r(runs["ubas"]["regret"]) if "ubas" in runs else "nicht anwendbar"
        row = f"| {name} | {v['b']['inst'].m} | {ev.zahl(v['b']['n_bases'])} | {_r(runs['omm']['regret'])} | {_r(runs['eps']['regret'])} | {_r(runs['zufall']['regret'])} | {ubas} |"
        assert row in README, row


def test_experiment_1():
    rows = {(r["matroid"], r["algo"]): r for r in ev.ex1_series()}
    assert [_r(rows[("Wald", a)]["mean"][2000]) for a in ev.E1_KEYS] == ["217,1", "71,1", "90,3", "1 380,0", "1 358,8"] and _r(rows[("Wald", "eps")]["std"][2000]) == "44,5"
    assert [_r(rows[("Kardinalität 3", a)]["mean"][2000]) for a in ev.E1_KEYS] == ["327,8", "79,6", "139,2", "943,8", "929,9"] and _r(rows[("Kardinalität 3", "eps")]["std"][2000]) == "142,4"
    assert [_r(rows[("4 Farben", a)]["mean"][2000]) for a in ev.E1_KEYS] == ["279,8", "79,9", "81,0", "1 132,8", "1 101,9"] and _r(rows[("4 Farben", "eps")]["std"][2000]) == "81,2"
    assert [rows[(m, "zufall")]["n_bases"] for m in ("Wald", "Kardinalität 3", "4 Farben")] == [1049, 364, 144]
    for text in ("OMM c = 1,5 **217,1**, OMM c = 0,25 **71,1**, ε-Greedy **90,3** (± 44,5), Zufall **1 380,0**, UCB über Basen **1 358,8**", "**327,8** / **79,6** / **139,2** (± 142,4) / 943,8 / 929,9",
                 "**279,8** / **79,9** / **81,0** (± 81,2) / 1 132,8 / **1 101,9**"):
        assert text in README, text


def test_experiment_2():
    rows = {r["delta"]: r for r in ev.ex2_series()}
    expected = {0.4: ("22,8 / 22,8 / 25,4 / 23,9 / 26,0", True), 0.2: ("37,9 / 50,0 / 55,7 / 57,4 / 67,3", False), 0.1: ("38,2 / 64,3 / 87,1 / 105,1 / 123,4", False), 0.05: ("31,7 / 56,9 / 92,0 / 143,6 / 204,9", False)}
    for delta, (incs, phase) in expected.items():
        assert " / ".join(_r(x) for x in rows[delta]["increments"]) == incs and rows[delta]["in_phase"] == phase, delta
        head, last = incs.rsplit(" / ", 1)
        assert f"{head} / **{last}**" in README, incs


def test_experiment_3():
    rows = ev.ex3_series()
    wald = [_r(r["regret"]) for r in rows if r["matroid"] == "Wald"]
    card = [_r(r["regret"]) for r in rows if r["matroid"] == "Kardinalität 3"]
    assert wald == ["125,8", "144,7", "177,2", "215,1", "249,2", "211,5", "119,1"] and card == ["195,1", "227,9", "268,2", "314,5", "297,9", "201,8", "91,2"]
    for text in ("**125,8 / 144,7 / 177,2 / 215,1 / 249,2 / 211,5 / 119,1**", "**195,1 / 227,9 / 268,2 / 314,5 / 297,9 / 201,8 / 91,2**", "Lücke 0,5 / 0,4 / 0,3 / 0,2 / 0,1 / 0,05 / 0,02"):
        assert text in README, text


def test_experiment_4():
    res = ev.ex4_series()
    assert [_r(r["regret"]) for r in res["by_n"]] == ["205,1", "462,0", "781,3", "1 047,5"] and round(res["by_n"][-1]["max"], 6) == 1200.0
    wald = [_r(r["regret"]) for r in res["vs"] if r["matroid"] == "Wald"]
    card = [_r(r["regret"]) for r in res["vs"] if r["matroid"] == "Kardinalität"]
    assert wald == ["186,3", "611,9", "1 511,1"] and card == ["184,2", "638,8", "1 508,1"] and [r["arms"] for r in res["vs"] if r["matroid"] == "Wald"] == [10, 28, 66]
    for text in ("**205,1 / 462,0 / 781,3 / 1 047,5** (höchstmöglich 1 200)", "**186,3 / 611,9 / 1 511,1** gegen **184,2 / 638,8 / 1 508,1**"):
        assert text in README, text


def test_experiment_5():
    by = {(r["delta"], r["key"]): r for r in ev.ex5_series()}
    assert _r(by[(0.2, "omm1.5")]["mean"]) == "212,4" and _r(by[(0.2, "omm0.5")]["mean"]) == "93,6" and _r(by[(0.2, "omm0.25")]["mean"]) == "77,9" and _r(by[(0.2, "eps")]["mean"]) == "101,4" and _r(by[(0.2, "eps")]["max"]) == "693,0"
    assert [by[(0.2, k)]["ok"] for k in ("omm1.5", "omm0.5", "omm0.25")] == [24, 29, 28]
    assert (_r(by[(0.1, "omm1.5")]["mean"]), by[(0.1, "omm1.5")]["ok"], _r(by[(0.1, "omm0.25")]["mean"]), by[(0.1, "omm0.25")]["ok"]) == ("249,6", 10, "104,9", 27)
    assert (_r(by[(0.1, "eps")]["mean"]), _r(by[(0.1, "eps")]["q90"]), _r(by[(0.1, "eps")]["max"]), by[(0.1, "eps")]["ok"]) == ("208,6", "416,1", "439,9", 14)
    assert (by[(0.05, "omm1.5")]["ok"], by[(0.05, "omm0.25")]["ok"], by[(0.05, "eps")]["ok"]) == (2, 15, 2)
    for text in ("c = 1,5 **212,4**; c = 0,5 93,6; c = 0,25 **77,9** (24 / 29 / 28 von 30); ε-Greedy 101,4 (Maximum **693,0**)", "c = 1,5 249,6 (**10 von 30**); c = 0,25 104,9 (27 von 30); ε-Greedy 208,6, 90 %-Quantil **416,1**, Maximum **439,9**, **14 von 30**",
                 "c = 1,5 **2 von 30**, c = 0,25 **15 von 30**, ε-Greedy 2 von 30"):
        assert text in README, text


def test_the_hand_examples():
    mat, mu = A.make_matroid("card", 3, 1), [0.9, 0.5, 0.1]
    counts, sums, seq, regret = [0] * 3, [0.0] * 3, [], 0.0
    for t in range(1, 13):
        e = A.greedy_basis(mat, A.omm_index(counts, sums, t, 1.5))[0]
        seq.append(e)
        counts[e] += 1
        sums[e] += mu[e]
        regret += 0.9 - mu[e]
    assert seq == [0, 1, 2, 0, 1, 0, 0, 2, 0, 1, 0, 0] and counts == [7, 3, 2] and round(regret, 1) == 2.8
    idx = A.omm_index([2, 1, 1], [1.8, 0.5, 0.1], 5, 1.5)
    assert (round(idx[1], 3), round(idx[0], 3)) == (2.054, 1.999)
    g = A.gaps(A.make_matroid("card", 4, 2), [0.9, 0.8, 0.3, 0.2])
    assert (round(g[2], 3), round(g[3], 3)) == (0.5, 0.6)
    assert A.count_bases(A.make_matroid("wald", 4, 0, [(0, 1), (1, 2), (0, 2), (2, 3)], 4)) == 3
    assert A.count_bases(A.make_matroid("wald", 10, 0, [(a, b) for a in range(5) for b in range(a + 1, 5)], 5)) == 125
    for text in ("**0, 1, 2, 0, 1, 0, 0, 2, 0, 1, 0, 0**; Züge **7 / 3 / 2**; Bedauern **2,8**", "Index 2,054 gegen 1,999", "**0,5** und **0,6**", "**3** Spannbäume", "**125**"):
        assert text in README, text


def test_constants_in_the_readme():
    assert (C.PLAN_NODES, C.PLAN_EDGES, C.V_MIN, C.V_MAX, C.E1_RUNS, C.E1_UBAS_RUNS, C.E2_RUNS, C.E3_RUNS, C.E5_RUNS, A.BASES_LIMIT) == (8, 14, 5, 12, 20, 8, 20, 20, 30, 3000)
    for text in ("8 Standorte, 14 zufällige Leitungen", "5 bis 12 Standorten, bis 66 Arme", "Mittel über 20 Läufe, UCB über Basen 8", "höchstens 3 000 Basen", "Port 9354"):
        assert text in README, text
    assert ev.build(ev.Settings("gross", 12))["inst"].m == 66 and ev.build(ev.Settings("gross", 12))["n_bases"] == 12 ** 10
