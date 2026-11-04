"""Szenario: ein Leitungsnetz. Standorte auf einem Plan, mögliche Leitungen (Arme) mit unbekannter Erfolgswahrscheinlichkeit μ."""

import random
from dataclasses import dataclass

import mbd_algorithm as A
import mbd_constants as C

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@dataclass(frozen=True)
class Instance:
    points: tuple[tuple[float, float], ...]
    edges: tuple[tuple[int, int], ...]     # (u, v), u < v, geordnet nach (u, v); der Kantenindex ist die Position

    @property
    def n(self) -> int:                    # Zahl der Standorte
        return len(self.points)

    @property
    def m(self) -> int:                    # Zahl der Leitungen (= Arme)
        return len(self.edges)

    def name(self, v: int) -> str:
        return LETTERS[v]

    def label(self, e: int) -> str:
        u, v = self.edges[e]
        return f"{self.name(u)}–{self.name(v)}"


def complete_edges(v: int) -> list[tuple[int, int]]:
    return [(a, b) for a in range(v) for b in range(a + 1, v)]


def connected(v: int, edges) -> bool:
    parent = list(range(v))
    for a, b in edges:
        parent[A._find(parent, a)] = A._find(parent, b)
    return len({A._find(parent, i) for i in range(v)}) == 1


def make_instance(inst: str, v: int, seed: int) -> Instance:
    """Deterministisch aus (inst, v, seed). plan: 8 Standorte und 14 zufällige Leitungen, zusammenhängend; gross: vollständiger Graph auf v Standorten."""
    rng = random.Random(seed)
    nodes = C.PLAN_NODES if inst == "plan" else v
    if not 2 <= nodes <= len(LETTERS):
        raise ValueError(f"{nodes} Standorte außerhalb von 2 bis {len(LETTERS)}")
    points = tuple((rng.uniform(0.05, 0.95), rng.uniform(0.05, 0.95)) for _ in range(nodes))
    allp = complete_edges(nodes)
    if inst == "plan":
        while True:
            edges = sorted(rng.sample(allp, C.PLAN_EDGES))
            if connected(nodes, edges):
                break
    else:
        edges = allp
    return Instance(points, tuple(edges))


def make_means(mat: A.Matroid, kind: str, delta: float, seed: int) -> tuple[float, ...]:
    """Erfolgswahrscheinlichkeiten je Arm. zwei: die Arme einer festen (zufälligen) Basis haben 0,5 + Δ/2, alle anderen 0,5 − Δ/2, also sind alle Lücken gleich Δ; zufall: gleichverteilt 0,1 bis 0,9."""
    if kind == "zwei":
        rng = random.Random(seed * 7919 + 1)
        b0 = set(A.greedy_basis(mat, [rng.random() for _ in range(mat.n)]))
        return tuple(0.5 + delta / 2 if e in b0 else 0.5 - delta / 2 for e in range(mat.n))
    if kind == "zufall":
        rng = random.Random(seed * 7919 + 2)
        return tuple(rng.uniform(0.1, 0.9) for _ in range(mat.n))
    raise ValueError(f"Nutzenart {kind!r} unbekannt")
