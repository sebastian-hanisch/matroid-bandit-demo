"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mbd_algorithm as A  # noqa: E402


@pytest.fixture
def drei_arme():
    """Drei Arme mit μ = 0,9 / 0,5 / 0,1, höchstens einer (Kardinalität 1)."""
    return A.make_matroid("card", 3, 1), [0.9, 0.5, 0.1]


@pytest.fixture
def card2():
    """Vier Arme mit μ = 0,9 / 0,8 / 0,3 / 0,2, höchstens zwei. Beste Basis {0, 1}, Lücken 0,5 und 0,6."""
    return A.make_matroid("card", 4, 2), [0.9, 0.8, 0.3, 0.2]


@pytest.fixture
def dreieck():
    """Dreieck ab, bc, ac und Pendelkante cd (Knoten a bis d = 0 bis 3), μ = 0,9 / 0,6 / 0,4 / 0,1. Rang 3, drei Spannbäume, beste Basis {ab, bc, cd}."""
    return A.make_matroid("wald", 4, 0, [(0, 1), (1, 2), (0, 2), (2, 3)], 4), [0.9, 0.6, 0.4, 0.1]
