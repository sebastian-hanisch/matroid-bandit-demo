"""Verdikte (reine Funktionen in mbd_evaluation.py) an festen Eingaben: jeder Zweig, jede Zahl im Text (DEMO-PLAYBOOK §4). Alles ist deterministisch (keine Löser)."""

import mbd_constants as C
import mbd_evaluation as ev

DEFAULT = ev.Settings()
VIELE = ev.Settings(**C.PRESETS["Viele Arme"])


def test_run_verdict_for_the_default_names_all_four_algorithms():
    kind, text = ev.verdict_run(DEFAULT, ev.run_view(DEFAULT))
    assert kind == "info" and text == (
        "Beste Basis bei bekannten Erfolgswahrscheinlichkeiten: **7 Leitungen** mit erwartetem Nutzen **4,20** je Runde; kleinste Lücke **0,200**. Nach **2 000** Runden: "
        "OMM (c = 1,5) Bedauern **223,4**, ε-Greedy **104,0**, Zufall **1 390,2**, UCB über Basen **1 360,0** (1 049 Basen). Am wenigsten Bedauern: **ε-Greedy**.")


def test_run_verdict_without_the_basis_bandit_and_for_the_other_preset_texts():
    kind, text = ev.verdict_run(VIELE, ev.run_view(VIELE))
    assert "OMM (c = 1,5) Bedauern **1 510,4**, ε-Greedy **577,0**, Zufall **3 652,2**; UCB über Basen ist hier nicht anwendbar (**61 917 364 224** Basen, mehr als 3 000)." in text
    s = ev.Settings(**C.PRESETS["Kleine Konstante"])
    assert "OMM (c = 0,25) Bedauern **49,8**" in ev.verdict_run(s, ev.run_view(s))[1] and ev.verdict_run(s, ev.run_view(s))[1].endswith("Am wenigsten Bedauern: **Optimistisches Greedy (OMM)**.")
    zu = ev.Settings(mus="zufall")
    assert "kleinste Lücke" in ev.verdict_run(zu, ev.run_view(zu))[1]
    v = ev.run_view(DEFAULT)
    assert ev.verdict_run(DEFAULT, {**v, "runs": {**v["runs"], "omm": {**v["runs"]["omm"], "regret": -1.0}}})[0] == "error"


def test_run_rows_and_element_rows():
    rows = ev.run_rows(DEFAULT, ev.run_view(DEFAULT))
    assert [r["Verfahren"] for r in rows] == ["Optimistisches Greedy (OMM) (c = 1,5)", "ε-Greedy", "Zufällige Basis", "UCB über Basen (ohne Struktur)"]
    assert rows[0] == {"Verfahren": "Optimistisches Greedy (OMM) (c = 1,5)", "Bedauern": "223,4", "Bedauern je Runde": "0,112", "Züge von Armen außerhalb der besten Basis": "1 117", "beste Basis in der letzten Runde": "ja"}
    assert rows[2]["beste Basis in der letzten Runde"] == "nein"
    er = ev.element_rows(ev.run_view(DEFAULT))
    assert er[0] == {"Leitung": "A–B", "wahres μ": "0,400", "Schätzung (OMM)": "0,370", "Züge (OMM)": "138", "in der besten Basis": "", "in der letzten Basis": ""} and er[1]["in der besten Basis"] == "ja"
    assert sum(1 for r in er if r["in der besten Basis"] == "ja") == 7


def test_experiment_one_verdict_on_handmade_rows():
    def row(m, nb, algo, v):
        return {"matroid": m, "n_bases": nb, "algo": algo, "mean": {100: v / 20, 500: v / 4, 2000: v}, "std": {100: 1.0, 500: 2.0, 2000: 3.0}}
    rows = [row(m, nb, a, v) for m, nb, vals in (("Wald", 1049, (200.0, 70.0, 90.0, 1380.0, 1360.0)), ("Kardinalität 3", 364, (330.0, 80.0, 140.0, 940.0, 930.0)), ("4 Farben", 144, (280.0, 80.0, 80.0, 1130.0, 1100.0)))
            for a, v in zip(("omm", "omm025", "eps", "zufall", "ubas"), vals)]
    kind, text = ev.verdict_ex1(rows)
    assert kind == "info" and text.startswith("Auf dem Wald des Plans nach 2 000 Runden (Lücke 0,2): OMM mit c = 1,5 **200,0**, mit c = 0,25 **70,0**, ε-Greedy **90,0**, Zufall **1 380,0**, UCB über Basen **1 360,0**.")
    assert "Bei 4 Farben (144 Basen): OMM **280,0**, UCB über Basen **1 100,0** gegen Zufall **1 130,0**" in text
    assert ev.verdict_ex1([dict(rows[0], mean={100: 0, 500: 0, 2000: -5.0})] + rows[1:])[0] == "error"
    assert ev.ex1_table(rows)[0] == {"Nebenbedingung": "Wald (1 049 Basen)", "Verfahren": "OMM (c = 1,5)", "nach 100 Runden": "10,0 (± 1,0)", "nach 500 Runden": "50,0 (± 2,0)", "nach 2 000 Runden": "200,0 (± 3,0)"}


def test_experiment_two_verdict_on_handmade_rows():
    def row(delta, vals):
        inc = [b - a for a, b in zip(vals, vals[1:])]
        return {"delta": delta, "values": vals, "increments": inc, "in_phase": inc[-1] <= 1.1 * inc[-2]}
    rows = [row(0.4, [70.0, 94.0, 117.0, 142.0, 166.0, 192.0]), row(0.05, [36.0, 68.0, 124.0, 216.0, 360.0, 565.0])]
    assert rows[0]["in_phase"] and not rows[1]["in_phase"]
    kind, text = ev.verdict_ex2(rows)
    assert kind == "info" and "Δ = 0,4: 24,0 und 26,0; Δ = 0,05: 144,0 und 205,0." in text and "bei Δ = 0,4 erreicht und bei Δ = 0,05 **noch nicht**" in text and "T ≫ n/Δ²" in text
    assert ev.verdict_ex2([dict(rows[0], increments=[1.0, -2.0, 3.0])] + rows[1:])[0] == "error"
    assert ev.ex2_table(rows)[0]["konstant am Ende?"] == "ja" and ev.ex2_table(rows)[1]["T = 8 000"] == "565,0" and ev.ex2_table(rows)[0]["Zuwächse je Verdopplung"] == "24,0 / 23,0 / 25,0 / 24,0 / 26,0"


def test_experiment_three_four_five_verdicts_on_handmade_rows():
    rows3 = [{"matroid": m, "delta": d, "regret": r, "std": 5.0} for m, vals in (("Wald", ((0.5, 120.0), (0.1, 250.0), (0.02, 110.0))), ("Kardinalität 3", ((0.5, 190.0), (0.2, 310.0), (0.02, 90.0)))) for d, r in vals]
    kind, text = ev.verdict_ex3(rows3)
    assert kind == "info" and "Wald: größtes Bedauern **250,0** bei Δ = 0,1, bei Δ = 0,02 nur **110,0**; Kardinalität 3: größtes Bedauern **310,0** bei Δ = 0,2, bei Δ = 0,02 nur **90,0**" in text
    assert ev.verdict_ex3([dict(rows3[0], regret=-1.0)] + rows3[1:])[0] == "error" and ev.ex3_table(rows3)[1]["Bedauern · Δ"] == "25,0"

    res4 = {"by_n": [{"n": n, "regret": r, "std": 3.0, "max": 1200.0} for n, r in ((10, 200.0), (80, 1050.0))],
            "vs": [{"v": v, "arms": a, "rank": v - 1, "matroid": m, "regret": r, "std": 4.0} for v, a, m, r in ((5, 10, "Wald", 186.0), (5, 10, "Kardinalität", 184.0))]}
    kind, text = ev.verdict_ex4(res4)
    assert kind == "info" and "Bedauern **200,0 / 1 050,0**; bei 80 Armen liegt es nahe am höchstmöglichen Wert **1 200**" in text and "Wald **186,0**, Kardinalität **184,0**" in text
    assert ev.verdict_ex4({**res4, "vs": [dict(res4["vs"][0], regret=-2.0)]})[0] == "error" and ev.ex4_table(res4)[2]["Versuch"] == "Wald (vollständiger Graph, 5 Standorte)"

    def r5(delta, key, mean, q90, mx, ok):
        return {"delta": delta, "key": key, "mean": mean, "median": mean, "q90": q90, "max": mx, "ok": ok, "runs": 30}
    rows5 = [r5(0.2, "omm1.5", 212.0, 240.0, 250.0, 24), r5(0.2, "omm0.25", 78.0, 108.0, 427.0, 28), r5(0.2, "eps", 101.0, 152.0, 693.0, 29), r5(0.1, "eps", 209.0, 416.0, 440.0, 14), r5(0.1, "omm0.25", 105.0, 205.0, 259.0, 27),
             r5(0.05, "omm1.5", 214.0, 246.0, 252.0, 2), r5(0.05, "omm0.25", 129.0, 185.0, 215.0, 15)]
    kind, text = ev.verdict_ex5(rows5)
    assert kind == "info" and "Bei Δ = 0,2: OMM mit c = 1,5 **212,0**, mit c = 0,25 **78,0**, ε-Greedy **101,0**." in text
    assert "ε-Greedy ein 90 %-Quantil von **416,0** und ein Maximum von **440,0** (beste Basis am Ende bei **14 von 30** Läufen), OMM mit c = 0,25 **205,0**, **259,0** und **27 von 30**" in text
    assert "OMM mit c = 1,5 nur in **2 von 30** Läufen die beste Basis, mit c = 0,25 in **15 von 30**" in text
    assert ev.verdict_ex5([dict(rows5[0], mean=-1.0)] + rows5[1:])[0] == "error" and ev.ex5_table(rows5)[1]["Verfahren"] == "OMM (c = 0,25)" and ev.ex5_table(rows5)[2]["beste Basis am Ende"] == "29 von 30"


def test_play_verdict_branches():
    assert ev.verdict_play(DEFAULT, ev.play_view(DEFAULT, 0)) == ("info", "Noch keine Runde gespielt: Alle Arme haben den Index ∞ und werden zuerst ausprobiert. Spielen Sie Runden mit den Knöpfen.")
    assert ev.verdict_play(DEFAULT, ev.play_view(DEFAULT, 1))[1] == "Nach **1 Runde**: kumuliertes Bedauern **0,8**, **4** Züge von Armen außerhalb der besten Basis, 7 Arme noch nie gezogen; die Basis der letzten Runde ist nicht die beste."
    assert ev.verdict_play(DEFAULT, ev.play_view(DEFAULT, 100))[1] == "Nach **100 Runden**: kumuliertes Bedauern **45,6**, **228** Züge von Armen außerhalb der besten Basis, alle Arme mindestens einmal gezogen; die Basis der letzten Runde ist nicht die beste."
    assert "die beste" in ev.verdict_play(DEFAULT, ev.play_view(DEFAULT, 2000))[1] and "ist nicht die beste" not in ev.verdict_play(DEFAULT, ev.play_view(DEFAULT, 2000))[1]
    p = ev.play_view(DEFAULT, 10)
    assert ev.verdict_play(DEFAULT, {**p, "regret": -1.0})[0] == "error"
    assert ev.play_rows(p)[0] == {"Leitung": "A–B", "wahres μ": "0,400", "Schätzung": "0,625", "Züge": "8", "Index (nächste Runde)": "1,296", "beste Basis": ""}
    assert ev.play_round_rows(p)[0] == {"Runde": 10, "gewählte Basis": "A–D, B–D, B–H, C–F, D–G, E–F, F–G", "Erfolge": 4, "Bedauern der Runde": "0,40"}
    assert ev.play_rows(ev.play_view(DEFAULT, 0))[0]["Index (nächste Runde)"] == "∞"


def test_formatting_helpers():
    assert (ev.de(0.5, 3), ev.de(1390.24, 1), ev.num(3.0), ev.num(0.25), ev.prozent(0.5612), ev.zahl(61917364224), ev.leitungen(1), ev.leitungen(7), ev.runden(1), ev.runden(1000)) == (
        "0,500", "1 390,2", "3", "0,25", "56,1", "61 917 364 224", "1 Leitung", "7 Leitungen", "1 Runde", "1 000 Runden")
