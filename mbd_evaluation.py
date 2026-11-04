"""Kennzahlen, Experimente und Verdikte. Alle sichtbaren Zahlen kommen aus diesen Funktionen."""

import statistics
from dataclasses import dataclass
from functools import lru_cache

import mbd_algorithm as A
import mbd_constants as C
from mbd_scenario import complete_edges, make_instance, make_means


def de(x: float, digits: int = 1) -> str:
    """Zahl mit Dezimalkomma und Leerzeichen als Tausendertrenner."""
    return f"{x:,.{digits}f}".replace(",", " ").replace(".", ",")


def num(x: float) -> str:
    """Ganze Zahl ohne, sonst mit bis zu drei Nachkommastellen (Dezimalkomma)."""
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f"{x:.3f}".rstrip("0").rstrip(".").replace(".", ",")


def prozent(x: float, digits: int = 1) -> str:
    return de(100.0 * x, digits)


def zahl(n: int) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner."""
    return f"{n:,}".replace(",", " ")


def runden(n: int) -> str:
    return "1 Runde" if n == 1 else f"{zahl(n)} Runden"


def leitungen(k: int) -> str:
    return "1 Leitung" if k == 1 else f"{k} Leitungen"


@dataclass(frozen=True)
class Settings:
    inst: str = "plan"
    v: int = C.DEFAULT_V                  # Standorte des großen Plans
    seed: int = C.DEFAULT_SEED
    cons: str = "wald"
    k: int = C.DEFAULT_K
    mus: str = "zwei"
    delta: float = C.DEFAULT_DELTA
    T: int = C.DEFAULT_T
    c: float = C.DEFAULT_C
    rseed: int = C.DEFAULT_RSEED


# --- Instanz und Lauf -----------------------------------------------------------------------------------------------------------------------------


@lru_cache(maxsize=64)
def build(s: Settings) -> dict:
    ins = make_instance(s.inst, s.v, s.seed)
    mat = A.make_matroid(s.cons, ins.m, s.k, ins.edges, ins.n)
    mu = make_means(mat, s.mus, s.delta, s.seed)
    best, opt = A.best_basis(mat, mu)
    g = A.gaps(mat, mu)
    return {"inst": ins, "mat": mat, "mu": mu, "best": best, "opt": opt, "gaps": g, "min_gap": min(g.values()) if g else float("inf"),
            "n_bases": A.count_bases(mat), "bases": A.enumerate_bases(mat), "rank": len(best)}


def algos_for(b: dict) -> tuple[str, ...]:
    return C.ALGOS if b["bases"] is not None else C.ALGOS[:3]


@lru_cache(maxsize=64)
def run_view(s: Settings) -> dict:
    b = build(s)
    runs = {a: A.simulate(b["mat"], b["mu"], a, s.T, s.rseed, s.c, b["bases"]) for a in algos_for(b)}
    return {"b": b, "runs": runs}


def curve_points(curve, points: int = C.CURVE_POINTS):
    """Höchstens `points` Stützstellen (Runde, kumuliertes Bedauern) einer Kurve, die letzte immer dabei."""
    T = len(curve)
    step = max(1, T // points)
    xs = list(range(step, T + 1, step))
    if not xs or xs[-1] != T:
        xs.append(T)
    return xs, [curve[x - 1] for x in xs]


def run_rows(s: Settings, v: dict) -> list[dict]:
    b = v["b"]
    rows = []
    for a, r in v["runs"].items():
        rows.append({"Verfahren": C.ALGO_NAMES[a] + (f" (c = {num(s.c)})" if a == "omm" else ""), "Bedauern": de(r["regret"], 1), "Bedauern je Runde": de(r["regret"] / s.T, 3),
                     "Züge von Armen außerhalb der besten Basis": zahl(sum(r["bad"])), "beste Basis in der letzten Runde": "ja" if r["ok"] else "nein"})
    if b["bases"] is None:
        rows.append({"Verfahren": C.ALGO_NAMES["ubas"], "Bedauern": "–", "Bedauern je Runde": "–", "Züge von Armen außerhalb der besten Basis": "–", "beste Basis in der letzten Runde": f"nicht anwendbar ({zahl(b['n_bases'])} Basen)"})
    return rows


def element_rows(v: dict) -> list[dict]:
    """Je Leitung: wahres μ, Schätzung und Züge von OMM, ob in der besten Basis und in der letzten OMM-Basis."""
    b, r = v["b"], v["runs"]["omm"]
    ins = b["inst"]
    return [{"Leitung": ins.label(e), "wahres μ": de(b["mu"][e], 3), "Schätzung (OMM)": "–" if r["means"][e] is None else de(r["means"][e], 3), "Züge (OMM)": zahl(r["pulls"][e]),
             "in der besten Basis": "ja" if e in b["best"] else "", "in der letzten Basis": "ja" if e in r["last"] else ""} for e in range(ins.m)]


def verdict_run(s: Settings, v: dict) -> tuple[str, str]:
    b, runs = v["b"], v["runs"]
    if any(r["regret"] < -1e-9 for r in runs.values()):
        return "error", "Das Bedauern ist negativ: Das ist ein Fehler in der Rechnung."
    gap = "" if b["min_gap"] == float("inf") else f"; kleinste Lücke **{de(b['min_gap'], 3)}**"
    text = (f"Beste Basis bei bekannten Erfolgswahrscheinlichkeiten: **{leitungen(b['rank'])}** mit erwartetem Nutzen **{de(b['opt'], 2)}** je Runde{gap}. Nach **{zahl(s.T)}** Runden: "
            f"OMM (c = {num(s.c)}) Bedauern **{de(runs['omm']['regret'], 1)}**, ε-Greedy **{de(runs['eps']['regret'], 1)}**, Zufall **{de(runs['zufall']['regret'], 1)}**")
    if "ubas" in runs:
        text += f", UCB über Basen **{de(runs['ubas']['regret'], 1)}** ({zahl(b['n_bases'])} Basen). "
    else:
        text += f"; UCB über Basen ist hier nicht anwendbar (**{zahl(b['n_bases'])}** Basen, mehr als {zahl(A.BASES_LIMIT)}). "
    least = min(runs, key=lambda a: runs[a]["regret"])
    text += f"Am wenigsten Bedauern: **{C.ALGO_NAMES[least]}**."
    return "info", text


# --- Messreihen -----------------------------------------------------------------------------------------------------------------------------------


def average(mat, mu, algo: str, runs: int, seed: int, checkpoints, c: float = 1.5, bases=None) -> dict:
    """Mittel über Läufe: Bedauern bei den Stützstellen (Mittel, Standardabweichung, 90 %-Quantil, Maximum), Anteil der Läufe mit bester Basis am Ende, Züge von Armen außerhalb der besten Basis."""
    T = max(checkpoints)
    vals = {cp: [] for cp in checkpoints}
    ok = 0
    bad = 0.0
    for i in range(runs):
        r = A.simulate(mat, mu, algo, T, seed * 1000 + i, c, bases)
        for cp in checkpoints:
            vals[cp].append(r["curve"][cp - 1])
        ok += 1 if r["ok"] else 0
        bad += sum(r["bad"]) / runs
    out = {"mean": {}, "std": {}, "q90": {}, "max": {}, "median": {}}
    for cp, xs in vals.items():
        xs = sorted(xs)
        out["mean"][cp], out["std"][cp], out["median"][cp] = statistics.mean(xs), statistics.pstdev(xs), statistics.median(xs)
        out["q90"][cp], out["max"][cp] = xs[min(len(xs) - 1, int(0.9 * len(xs)))], xs[-1]
    out["ok"], out["runs"], out["bad"] = ok, runs, bad
    return out


def _plan_mats() -> dict:
    ins = make_instance("plan", C.PLAN_NODES, C.DEFAULT_SEED)
    return {"Wald": A.make_matroid("wald", ins.m, 0, ins.edges, ins.n), "Kardinalität 3": A.make_matroid("card", ins.m, 3), "4 Farben": A.make_matroid("farbe", ins.m, 4)}


def _two(mat, delta=0.2):
    return make_means(mat, "zwei", delta, C.DEFAULT_SEED)


# Experiment 1: Verfahren und Zeit

E1_KEYS = ("omm", "omm025", "eps", "zufall", "ubas")
E1_NAMES = {"omm": "OMM (c = 1,5)", "omm025": "OMM (c = 0,25)", "eps": "ε-Greedy", "zufall": "Zufällige Basis", "ubas": "UCB über Basen"}


def ex1_series() -> list[dict]:
    rows = []
    for name, mat in _plan_mats().items():
        mu = _two(mat)
        bases = A.enumerate_bases(mat)
        for key in E1_KEYS:
            if key == "ubas" and bases is None:
                continue
            algo, c = ("omm", 0.25) if key == "omm025" else (key, 1.5)
            runs = C.E1_UBAS_RUNS if key == "ubas" else C.E1_RUNS
            r = average(mat, mu, algo, runs, C.SERIES_SEED % 1000 + 10, C.E1_CHECKPOINTS, c, bases if key == "ubas" else None)
            rows.append({"matroid": name, "n_bases": A.count_bases(mat), "algo": key, "mean": r["mean"], "std": r["std"]})
    return rows


def ex1_table(rows) -> list[dict]:
    cps = C.E1_CHECKPOINTS
    return [{"Nebenbedingung": f"{r['matroid']} ({zahl(r['n_bases'])} Basen)", "Verfahren": E1_NAMES[r["algo"]], **{f"nach {zahl(cp)} Runden": f"{de(r['mean'][cp], 1)} (± {de(r['std'][cp], 1)})" for cp in cps}} for r in rows]


def verdict_ex1(rows) -> tuple[str, str]:
    T = C.E1_T
    if any(r["mean"][T] < -1e-9 for r in rows):
        return "error", "Das Bedauern ist negativ: Das ist ein Fehler in der Rechnung."
    by = {(r["matroid"], r["algo"]): r["mean"][T] for r in rows}
    w = {a: by[("Wald", a)] for a in E1_KEYS}
    f4 = {a: by[("4 Farben", a)] for a in E1_KEYS}
    return "info", (f"Auf dem Wald des Plans nach {zahl(T)} Runden (Lücke 0,2): OMM mit c = 1,5 **{de(w['omm'], 1)}**, mit c = 0,25 **{de(w['omm025'], 1)}**, ε-Greedy **{de(w['eps'], 1)}**, Zufall **{de(w['zufall'], 1)}**, UCB über Basen **{de(w['ubas'], 1)}**. "
                    f"Bei 4 Farben (144 Basen): OMM **{de(f4['omm'], 1)}**, UCB über Basen **{de(f4['ubas'], 1)}** gegen Zufall **{de(f4['zufall'], 1)}**: Ohne Struktur lernt das Verfahren in dieser Zeit praktisch nichts, "
                    f"mit der Struktur (Greedy auf Indizes je Arm) schon.")


# Experiment 2: Wann ist das Wachstum logarithmisch?


def ex2_series() -> list[dict]:
    mat = _plan_mats()["Wald"]
    rows = []
    for delta in C.E2_DELTAS:
        r = average(mat, _two(mat, delta), "omm", C.E2_RUNS, C.SERIES_SEED % 1000 + 20, C.E2_CHECKPOINTS, 1.5)
        vals = [r["mean"][cp] for cp in C.E2_CHECKPOINTS]
        inc = [b - a for a, b in zip(vals, vals[1:])]
        rows.append({"delta": delta, "values": vals, "increments": inc, "in_phase": inc[-1] <= 1.1 * inc[-2]})
    return rows


def ex2_table(rows) -> list[dict]:
    cps = C.E2_CHECKPOINTS
    out = []
    for r in rows:
        row = {"Lücke Δ": num(r["delta"])}
        for cp, val in zip(cps, r["values"]):
            row[f"T = {zahl(cp)}"] = de(val, 1)
        row["Zuwächse je Verdopplung"] = " / ".join(de(x, 1) for x in r["increments"])
        row["konstant am Ende?"] = "ja" if r["in_phase"] else "nein"
        out.append(row)
    return out


def verdict_ex2(rows) -> tuple[str, str]:
    if any(x < -1e-9 for r in rows for x in r["increments"]):
        return "error", "Das kumulierte Bedauern nimmt ab: Das ist ein Fehler in der Rechnung."
    yes = [num(r["delta"]) for r in rows if r["in_phase"]]
    no = [num(r["delta"]) for r in rows if not r["in_phase"]]
    last = "; ".join(f"Δ = {num(r['delta'])}: {de(r['increments'][-2], 1)} und {de(r['increments'][-1], 1)}" for r in rows)
    return "info", (f"Zuwächse des Bedauerns bei den letzten beiden Verdopplungen von T (2 000 auf 4 000 und 4 000 auf 8 000): {last}. "
                    f"Ein **konstanter** Zuwachs je Verdopplung bedeutet logarithmisches Wachstum: Das ist bei Δ = {', '.join(yes) if yes else '–'} erreicht und bei Δ = {', '.join(no) if no else '–'} **noch nicht**: Die logarithmische Phase beginnt erst für T ≫ n/Δ².")


# Experiment 3: Bedauern gegen die Lücke


def ex3_series() -> list[dict]:
    mats = _plan_mats()
    rows = []
    for name in ("Wald", "Kardinalität 3"):
        for delta in C.E3_DELTAS:
            r = average(mats[name], _two(mats[name], delta), "omm", C.E3_RUNS, C.SERIES_SEED % 1000 + 30, (C.E3_T,), 1.5)
            rows.append({"matroid": name, "delta": delta, "regret": r["mean"][C.E3_T], "std": r["std"][C.E3_T]})
    return rows


def ex3_table(rows) -> list[dict]:
    return [{"Nebenbedingung": r["matroid"], "Lücke Δ": num(r["delta"]), "Bedauern": de(r["regret"], 1), "Standardabweichung": de(r["std"], 1), "Bedauern · Δ": de(r["regret"] * r["delta"], 1)} for r in rows]


def verdict_ex3(rows) -> tuple[str, str]:
    if any(r["regret"] < -1e-9 for r in rows):
        return "error", "Das Bedauern ist negativ: Das ist ein Fehler in der Rechnung."
    out = []
    for name in ("Wald", "Kardinalität 3"):
        sub = [r for r in rows if r["matroid"] == name]
        top = max(sub, key=lambda r: r["regret"])
        small = min(sub, key=lambda r: r["delta"])
        out.append(f"{name}: größtes Bedauern **{de(top['regret'], 1)}** bei Δ = {num(top['delta'])}, bei Δ = {num(small['delta'])} nur **{de(small['regret'], 1)}**")
    return "info", ("Bei festem T = 2 000 ist das Bedauern **nicht monoton in der Lücke**: " + "; ".join(out) + ". "
                    "Bei sehr kleiner Lücke kostet jeder falsche Zug fast nichts; bei großer Lücke ist die richtige Basis schnell gefunden.")


# Experiment 4: Armzahl und Art des Matroids


def ex4_series() -> dict:
    by_n = []
    for n in C.E4_NS:
        mat = A.make_matroid("card", n, 3)
        r = average(mat, _two(mat, C.E4_DELTA), "omm", C.E4_RUNS, C.SERIES_SEED % 1000 + 40, (C.E4_T,), 1.5)
        by_n.append({"n": n, "regret": r["mean"][C.E4_T], "std": r["std"][C.E4_T], "max": 3 * C.E4_DELTA * C.E4_T})
    vs = []
    for v in C.E4_VS:
        edges = complete_edges(v)
        for name, mat in (("Wald", A.make_matroid("wald", len(edges), 0, edges, v)), ("Kardinalität", A.make_matroid("card", len(edges), v - 1))):
            r = average(mat, _two(mat, C.E4_DELTA), "omm", C.E4_RUNS, C.SERIES_SEED % 1000 + 50, (C.E4_T,), 1.5)
            vs.append({"v": v, "arms": len(edges), "rank": v - 1, "matroid": name, "regret": r["mean"][C.E4_T], "std": r["std"][C.E4_T]})
    return {"by_n": by_n, "vs": vs}


def ex4_table(res) -> list[dict]:
    rows = [{"Versuch": "Kardinalität 3", "Arme": r["n"], "Rang": 3, "Bedauern": de(r["regret"], 1), "Standardabweichung": de(r["std"], 1)} for r in res["by_n"]]
    rows += [{"Versuch": f"{r['matroid']} (vollständiger Graph, {r['v']} Standorte)", "Arme": r["arms"], "Rang": r["rank"], "Bedauern": de(r["regret"], 1), "Standardabweichung": de(r["std"], 1)} for r in res["vs"]]
    return rows


def verdict_ex4(res) -> tuple[str, str]:
    if any(r["regret"] < -1e-9 for r in res["by_n"]) or any(r["regret"] < -1e-9 for r in res["vs"]):
        return "error", "Das Bedauern ist negativ: Das ist ein Fehler in der Rechnung."
    ns = " / ".join(str(r["n"]) for r in res["by_n"])
    reg = " / ".join(de(r["regret"], 1) for r in res["by_n"])
    last = res["by_n"][-1]
    wald = [r for r in res["vs"] if r["matroid"] == "Wald"]
    card = [r for r in res["vs"] if r["matroid"] == "Kardinalität"]
    return "info", (f"Bei Kardinalität 3 und {ns} Armen (Lücke 0,2, T = 2 000): Bedauern **{reg}**; bei {last['n']} Armen liegt es nahe am höchstmöglichen Wert **{de(last['max'], 0)}**: T = 2 000 ist dort noch zu kurz. "
                    f"Wald und Kardinalität gleichen Rangs (10, 28, 66 Arme): Wald **{' / '.join(de(r['regret'], 1) for r in wald)}**, Kardinalität **{' / '.join(de(r['regret'], 1) for r in card)}**: Die Art des Matroids spielt kaum eine Rolle, die Armzahl und die Lücke schon.")


# Experiment 5: Die Konstante und ε-Greedy


E5_KEYS = tuple(f"omm{c}" for c in C.E5_CS) + ("eps",)


def _e5_name(key: str) -> str:
    return "ε-Greedy" if key == "eps" else f"OMM (c = {num(float(key[3:]))})"


def ex5_series() -> list[dict]:
    mat = _plan_mats()["Wald"]
    rows = []
    for delta in C.E5_DELTAS:
        mu = _two(mat, delta)
        for key in E5_KEYS:
            algo, c = ("eps", 1.5) if key == "eps" else ("omm", float(key[3:]))
            r = average(mat, mu, algo, C.E5_RUNS, C.SERIES_SEED % 1000 + 60, (C.E5_T,), c)
            rows.append({"delta": delta, "key": key, "mean": r["mean"][C.E5_T], "median": r["median"][C.E5_T], "q90": r["q90"][C.E5_T], "max": r["max"][C.E5_T], "ok": r["ok"], "runs": r["runs"]})
    return rows


def ex5_table(rows) -> list[dict]:
    return [{"Lücke Δ": num(r["delta"]), "Verfahren": _e5_name(r["key"]), "Bedauern (Mittel)": de(r["mean"], 1), "Median": de(r["median"], 1), "90 %-Quantil": de(r["q90"], 1), "Maximum": de(r["max"], 1),
             "beste Basis am Ende": f"{r['ok']} von {r['runs']}"} for r in rows]


def verdict_ex5(rows) -> tuple[str, str]:
    if any(r["mean"] < -1e-9 for r in rows):
        return "error", "Das Bedauern ist negativ: Das ist ein Fehler in der Rechnung."
    by = {(r["delta"], r["key"]): r for r in rows}
    a, b = by[(0.2, "omm1.5")], by[(0.2, "omm0.25")]
    e, f = by[(0.1, "eps")], by[(0.1, "omm0.25")]
    g, h = by[(0.05, "omm1.5")], by[(0.05, "omm0.25")]
    return "info", (f"Bei Δ = 0,2: OMM mit c = 1,5 **{de(a['mean'], 1)}**, mit c = 0,25 **{de(b['mean'], 1)}**, ε-Greedy **{de(by[(0.2, 'eps')]['mean'], 1)}**. "
                    f"Bei Δ = 0,1 hat ε-Greedy ein 90 %-Quantil von **{de(e['q90'], 1)}** und ein Maximum von **{de(e['max'], 1)}** (beste Basis am Ende bei **{e['ok']} von {e['runs']}** Läufen), OMM mit c = 0,25 **{de(f['q90'], 1)}**, **{de(f['max'], 1)}** und **{f['ok']} von {f['runs']}**. "
                    f"Bei Δ = 0,05 findet OMM mit c = 1,5 nur in **{g['ok']} von {g['runs']}** Läufen die beste Basis, mit c = 0,25 in **{h['ok']} von {h['runs']}**: Die Konstante ist ein Regler, kein Detail.")


# --- Spielwiese: Runde für Runde ------------------------------------------------------------------------------------------------------------------


def play_view(s: Settings, steps: int) -> dict:
    """OMM nach `steps` Runden (steps ≥ 0), deterministisch aus s.rseed: Wahl je Runde, geschätzte Mittel, Indizes der nächsten Runde und kumuliertes Bedauern."""
    b = build(s)
    if steps <= 0:
        counts, sums = [0] * b["mat"].n, [0.0] * b["mat"].n
        return {"b": b, "steps": 0, "regret": 0.0, "choices": [], "rewards": [], "pulls": counts, "means": [None] * b["mat"].n, "index": A.omm_index(counts, sums, 1, s.c), "last": [], "ok": False, "round_regret": [], "curve": []}
    r = A.simulate(b["mat"], b["mu"], "omm", steps, s.rseed, s.c, record=True)
    counts = r["pulls"]
    sums = [0.0 if m is None else m * counts[e] for e, m in enumerate(r["means"])]
    idx = A.omm_index(counts, sums, steps + 1, s.c)
    round_regret = [b["opt"] - sum(b["mu"][e] for e in basis) for basis in r["choices"]]
    return {"curve": r["curve"], "b": b, "steps": steps, "regret": r["regret"], "choices": r["choices"], "rewards": r["rewards"], "pulls": counts, "means": r["means"], "index": idx, "last": r["last"], "ok": r["ok"], "round_regret": round_regret}


def play_rows(p: dict) -> list[dict]:
    b = p["b"]
    ins = b["inst"]
    return [{"Leitung": ins.label(e), "wahres μ": de(b["mu"][e], 3), "Schätzung": "–" if p["means"][e] is None else de(p["means"][e], 3), "Züge": zahl(p["pulls"][e]),
             "Index (nächste Runde)": "∞" if p["index"][e] == float("inf") else de(p["index"][e], 3), "beste Basis": "ja" if e in b["best"] else ""} for e in range(ins.m)]


def play_round_rows(p: dict, last: int = 8) -> list[dict]:
    ins = p["b"]["inst"]
    start = max(0, p["steps"] - last)
    return [{"Runde": i + 1, "gewählte Basis": ", ".join(ins.label(e) for e in sorted(p["choices"][i])), "Erfolge": p["rewards"][i], "Bedauern der Runde": de(p["round_regret"][i], 2)} for i in range(p["steps"] - 1, start - 1, -1)]


def verdict_play(s: Settings, p: dict) -> tuple[str, str]:
    if p["steps"] == 0:
        return "info", "Noch keine Runde gespielt: Alle Arme haben den Index ∞ und werden zuerst ausprobiert. Spielen Sie Runden mit den Knöpfen."
    if p["regret"] < -1e-9:
        return "error", "Das Bedauern ist negativ: Das ist ein Fehler in der Rechnung."
    unseen = sum(1 for c in p["pulls"] if c == 0)
    wrong = sum(sum(1 for e in basis if e not in p["b"]["best"]) for basis in p["choices"])
    return "info", (f"Nach **{runden(p['steps'])}**: kumuliertes Bedauern **{de(p['regret'], 1)}**, **{zahl(wrong)}** Züge von Armen außerhalb der besten Basis, "
                    f"{'alle Arme mindestens einmal gezogen' if unseen == 0 else f'{unseen} Arme noch nie gezogen'}; die Basis der letzten Runde ist {'die beste' if p['ok'] else 'nicht die beste'}.")
