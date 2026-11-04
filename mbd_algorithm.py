"""Kern: Matroid-Orakel, Greedy nach Indizes und die Lernverfahren der Matroid-Bandits.

Matroid auf n Elementen (Armen) mit unbekannten Erfolgswahrscheinlichkeiten μ_e. In jeder Runde t wählt das Verfahren eine Basis (maximale unabhängige Menge), sieht je
gewähltem Element eine Bernoulli-Ziehung (Rückmeldung je Element) und will über viele Runden nahe an der besten Basis bleiben (Greedy nach μ). Bedauern einer Runde:
μ(B*) − μ(B_t), kumuliert; gemessen wird der Erwartungswert (aus μ), nicht die gezogenen Werte.
Verfahren:
  omm     Optimistisches Greedy: Greedy nach dem Index μ̂_e + sqrt(c · ln t / T_e) (T_e Beobachtungen; unbeobachtet: ∞);
  eps     ε-Greedy mit ε_t = min(1, n / t): zufällige Basis mit dieser Wahrscheinlichkeit, sonst Greedy nach den beobachteten Mitteln (Start 0,5);
  zufall  jede Runde eine zufällige Basis;
  ubas    UCB über alle Basen als Arme (nur die Summe der Basis als Rückmeldung, keine Struktur): nur bei höchstens BASES_LIMIT Basen.
Die Bezeichnungen sind die der Demo; die Konstante c = 1,5 ist die der Planung, nicht gegen den Primärtext geprüft."""

from __future__ import annotations

import itertools
import math
import random
from dataclasses import dataclass
from fractions import Fraction

BASES_LIMIT = 3000
WALD_ENUM_LIMIT = 20000          # so viele Kandidaten (C(n, r)) darf die Aufzählung der Basen im Wald höchstens prüfen


def _find(parent, x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


@dataclass(frozen=True)
class Matroid:
    """kind: 'card' (höchstens k), 'part' (Klasse cls[e], Kapazität cap), 'wald' (edges[e] = (u, v) auf nodes Knoten)."""

    kind: str
    n: int
    k: int = 0
    cls: tuple = ()
    cap: int = 1
    edges: tuple = ()
    nodes: int = 0

    # --- einfache Orakel (auch Gegenprobe für die schnelle Greedy-Fassung) -------------------------------------------------------------------------

    def independent(self, s) -> bool:
        s = list(s)
        if self.kind == "card":
            return len(s) <= self.k
        if self.kind == "part":
            counts: dict = {}
            for e in s:
                counts[self.cls[e]] = counts.get(self.cls[e], 0) + 1
            return all(c <= self.cap for c in counts.values())
        parent = list(range(self.nodes))
        for e in s:
            a, b = _find(parent, self.edges[e][0]), _find(parent, self.edges[e][1])
            if a == b:
                return False
            parent[a] = b
        return True

    def rank(self) -> int:
        chosen: list[int] = []
        for e in range(self.n):
            if self.independent(chosen + [e]):
                chosen.append(e)
        return len(chosen)

    def greedy_naive(self, w) -> list[int]:
        """Basis nach absteigendem w (Gleichstand: kleinere Nummer), mit dem einfachen Orakel."""
        chosen: list[int] = []
        for e in sorted(range(self.n), key=lambda i: (-w[i], i)):
            if self.independent(chosen + [e]):
                chosen.append(e)
        return chosen


def make_matroid(cons: str, n: int, k: int, edges=(), nodes: int = 0) -> Matroid:
    if cons == "card":
        return Matroid("card", n, k=k)
    if cons == "farbe":
        return Matroid("part", n, cls=tuple(e % k for e in range(n)), cap=1)
    if cons == "wald":
        return Matroid("wald", n, edges=tuple(edges), nodes=nodes)
    raise ValueError(f"Nebenbedingung {cons!r} unbekannt")


def greedy_basis(mat: Matroid, w, order=None) -> list[int]:
    """Schnelle Fassung: Greedy nach absteigendem w (Gleichstand: kleinere Nummer) mit mitgeführtem Zustand statt neuer Prüfung je Element."""
    chosen: list[int] = []
    rank = None
    if mat.kind == "card":
        rank = mat.k
    seq = order if order is not None else sorted(range(mat.n), key=lambda i: (-w[i], i))
    if mat.kind == "card":
        return list(seq[: mat.k])
    if mat.kind == "part":
        used: dict = {}
        for e in seq:
            c = mat.cls[e]
            if used.get(c, 0) < mat.cap:
                used[c] = used.get(c, 0) + 1
                chosen.append(e)
        return chosen
    parent = list(range(mat.nodes))
    for e in seq:
        a, b = _find(parent, mat.edges[e][0]), _find(parent, mat.edges[e][1])
        if a != b:
            parent[a] = b
            chosen.append(e)
            if len(chosen) == mat.nodes - 1:
                break
    return chosen


def best_basis(mat: Matroid, mu) -> tuple[list[int], float]:
    b = greedy_basis(mat, mu)
    return b, sum(mu[e] for e in b)


def gaps(mat: Matroid, mu) -> dict[int, float]:
    """Lücke Δ_e für jedes Element e außerhalb der besten Basis B*: kleinster Verlust eines Tauschs B* − f + e, also min über f im Kreis von B* + e von (μ_f − μ_e)."""
    best = greedy_basis(mat, mu)
    inb = set(best)
    out: dict[int, float] = {}
    for e in range(mat.n):
        if e in inb:
            continue
        circuit = [f for f in best if mat.independent([x for x in best if x != f] + [e])]
        out[e] = min(mu[f] - mu[e] for f in circuit) if circuit else float("inf")
    return out


# --- Basen zählen und aufzählen ---------------------------------------------------------------------------------------------------------------


def _det(rows):
    """Determinante einer Fraction-Matrix (Gauß)."""
    n = len(rows)
    a = [list(r) for r in rows]
    det = Fraction(1)
    for i in range(n):
        piv = next((r for r in range(i, n) if a[r][i] != 0), None)
        if piv is None:
            return Fraction(0)
        if piv != i:
            a[i], a[piv] = a[piv], a[i]
            det = -det
        det *= a[i][i]
        for r in range(i + 1, n):
            f = a[r][i] / a[i][i]
            if f:
                for c in range(i, n):
                    a[r][c] -= f * a[i][c]
    return det


def count_bases(mat: Matroid) -> int:
    """Zahl der Basen: C(n, k) bei Kardinalität, Produkt der Klassengrößen bei Farben (Kapazität 1), Spannbäume nach Kirchhoff im Wald (zusammenhängend vorausgesetzt)."""
    if mat.kind == "card":
        return math.comb(mat.n, min(mat.k, mat.n))
    if mat.kind == "part":
        sizes: dict = {}
        for c in mat.cls:
            sizes[c] = sizes.get(c, 0) + 1
        out = 1
        for s in sizes.values():
            out *= math.comb(s, min(mat.cap, s))
        return out
    v = mat.nodes
    lap = [[Fraction(0)] * v for _ in range(v)]
    for a, b in mat.edges:
        lap[a][a] += 1
        lap[b][b] += 1
        lap[a][b] -= 1
        lap[b][a] -= 1
    return int(_det([row[1:] for row in lap[1:]]))


def enumerate_bases(mat: Matroid, limit: int = BASES_LIMIT):
    """Alle Basen als Listen, oder None, wenn es mehr als limit gibt (oder die Aufzählung im Wald zu viele Kandidaten prüfen müsste)."""
    if mat.kind == "wald" and math.comb(mat.n, mat.nodes - 1) > WALD_ENUM_LIMIT:
        return None
    if count_bases(mat) > limit:
        return None
    if mat.kind == "card":
        return [list(c) for c in itertools.combinations(range(mat.n), min(mat.k, mat.n))]
    if mat.kind == "part":
        groups: dict = {}
        for e, c in enumerate(mat.cls):
            groups.setdefault(c, []).append(e)
        parts = [list(itertools.combinations(g, min(mat.cap, len(g)))) for g in groups.values()]
        return [[e for part in combo for e in part] for combo in itertools.product(*parts)]
    return [list(c) for c in itertools.combinations(range(mat.n), mat.nodes - 1) if mat.independent(c)]


# --- Verfahren ---------------------------------------------------------------------------------------------------------------------------------


def omm_index(counts, sums, t: int, c: float) -> list[float]:
    """Index μ̂_e + sqrt(c · ln t / T_e); unbeobachtete Elemente haben den Index ∞."""
    lt = math.log(t) if t > 1 else 0.0
    return [math.inf if counts[e] == 0 else sums[e] / counts[e] + math.sqrt(c * lt / counts[e]) for e in range(len(counts))]


def simulate(mat: Matroid, mu, algo: str, T: int, seed: int, c: float = 1.5, bases=None, record: bool = False) -> dict:
    """Ein Lauf von T Runden. Rückgabe: curve (kumuliertes Bedauern nach jeder Runde, Länge T), pulls (Züge je Element), bad (Züge von Elementen außerhalb der besten Basis),
    means (beobachtete Mittel), last (Basis der letzten Runde), ok (war sie optimal?), und bei record die Wahl je Runde (choices) und die Summe der Ziehungen (rewards)."""
    rng = random.Random(seed)
    n = mat.n
    best, opt = best_basis(mat, mu)
    best_set = set(best)
    counts, sums = [0] * n, [0.0] * n
    regret = 0.0
    curve: list[float] = []
    bad = [0] * n
    choices, rewards = [], []
    last: list[int] = []
    if algo == "ubas":
        if not bases:
            raise ValueError("ubas braucht die Liste der Basen")
        nb = len(bases)
        bcnt, bsum = [0] * nb, [0.0] * nb
        r = len(best)
        bconst = 2.0 * r * r
    for t in range(1, T + 1):
        if algo == "omm":
            basis = greedy_basis(mat, omm_index(counts, sums, t, c))
        elif algo == "eps":
            if rng.random() < min(1.0, n / t):
                basis = greedy_basis(mat, None, order=_random_order(rng, n))
            else:
                basis = greedy_basis(mat, [0.5 if counts[e] == 0 else sums[e] / counts[e] for e in range(n)])
        elif algo == "zufall":
            basis = greedy_basis(mat, None, order=_random_order(rng, n))
        elif algo == "ubas":
            lt = math.log(t) if t > 1 else 0.0
            pick = next((i for i in range(nb) if bcnt[i] == 0), None)
            if pick is None:
                pick = max(range(nb), key=lambda i: (bsum[i] / bcnt[i] + math.sqrt(bconst * lt / bcnt[i]), -i))
            basis = bases[pick]
        else:
            raise ValueError(f"Verfahren {algo!r} unbekannt")
        total = 0
        for e in basis:
            x = 1 if rng.random() < mu[e] else 0
            total += x
            counts[e] += 1
            sums[e] += x
            if e not in best_set:
                bad[e] += 1
        if algo == "ubas":
            bcnt[pick] += 1
            bsum[pick] += total
        regret += opt - sum(mu[e] for e in basis)
        curve.append(regret)
        last = list(basis)
        if record:
            choices.append(list(basis))
            rewards.append(total)
    means = [sums[e] / counts[e] if counts[e] else None for e in range(n)]
    out = {"curve": curve, "pulls": counts, "bad": bad, "means": means, "last": last, "ok": set(last) == best_set, "regret": regret}
    if record:
        out["choices"], out["rewards"] = choices, rewards
    return out


def _random_order(rng: random.Random, n: int) -> list[int]:
    order = list(range(n))
    rng.shuffle(order)
    return order
