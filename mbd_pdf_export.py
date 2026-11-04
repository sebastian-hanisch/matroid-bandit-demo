"""PDF-Export des aktuellen Beispiels (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import mbd_constants as C
from mbd_evaluation import Settings, num, run_rows, run_view, verdict_run

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "€": "EUR", "„": '"', "“": '"', "×": "x", "≈": "~", "½": "1/2", "μ": "mu", "Δ": "Delta", "ε": "eps", "∞": "inf"}


def _s(text) -> str:
    out = str(text).replace("**", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings) -> bytes:
    v = run_view(s)
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Matroid-Bandits"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    place = "Plan der Reihe (8 Standorte, 14 Leitungen)" if s.inst == "plan" else f"Vollständiger Graph mit {s.v} Standorten"
    means = f"zwei Stufen (Lücke {num(s.delta)})" if s.mus == "zwei" else "zufällige Erfolgswahrscheinlichkeiten"
    pdf.multi_cell(0, 5, _s(f"{place}, Seed {s.seed}. Zulässig: {C.CONSTRAINT_NAMES[s.cons]}" + (f", k = {s.k}" if s.cons != "wald" else "") + f". Erfolgswahrscheinlichkeiten: {means}. {s.T} Runden, Konstante c = {num(s.c)}, Seed der Läufe {s.rseed}."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, _s("Die Verfahren"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for row in run_rows(s, v):
        pdf.multi_cell(0, 5, _s(" | ".join(f"{k}: {val}" for k, val in row.items())), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.multi_cell(0, 5, _s(verdict_run(s, v)[1]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Quelle: matroid-bandit-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
