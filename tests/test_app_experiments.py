"""AppTest: Hauptansicht, Experimente 1 bis 5, Spielwiese, Permalink und PDF (DEMO-PLAYBOOK §3, §5)."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import mbd_constants as C
import mbd_evaluation as ev
from mbd_pdf_export import build_pdf

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
PLAY = "plan_8_8_wald_3_zwei_0.2_1.5_1"


def _app(params=None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    for key, value in (params or {}).items():
        at.query_params[key] = value
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return [m.value for m in list(at.success) + list(at.info) + list(at.warning) + list(at.error)]


def _click_preset(at, name):
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]


def test_default_shows_the_metrics_and_the_verdicts():
    at = _app()
    assert [(m.label, m.value) for m in at.metric] == [("Optimistisches Greedy", "223,4"), ("ε-Greedy", "104,0"), ("Zufällige Basis", "1 390,2"), ("UCB über Basen", "1 360,0")]
    texts = _texts(at)
    assert any(t.startswith("Beste Basis bei bekannten Erfolgswahrscheinlichkeiten: **7 Leitungen**") for t in texts)
    assert any(t.startswith("Noch keine Runde gespielt") for t in texts)


def test_main_verdict_matches_each_preset():
    expected = {
        "Standardfall (Voreinstellung)": "OMM (c = 1,5) Bedauern **223,4**",
        "Kleine Konstante": "OMM (c = 0,25) Bedauern **49,8**",
        "Kleine Lücke": "Nach **5 000** Runden",
        "Viele Arme": "UCB über Basen ist hier nicht anwendbar (**61 917 364 224** Basen",
        "Ohne Struktur": "UCB über Basen **1 103,0** (144 Basen)",
    }
    at = _app()
    for name, needle in expected.items():
        _click_preset(at, name)
        assert any(needle in t for t in _texts(at)), name


def test_viele_arme_shows_a_dash_for_the_basis_bandit():
    at = _app()
    _click_preset(at, "Viele Arme")
    assert [m.value for m in at.metric][3] == "–"


def test_each_sidebar_widget_changes_the_run():
    at = _app()
    at.sidebar.select_slider(key="c_select").set_value(0.25).run()
    assert not at.exception and any("OMM (c = 0,25) Bedauern" in t for t in _texts(at))
    at.sidebar.select_slider(key="t_select").set_value(500).run()
    assert not at.exception and any("Nach **500** Runden" in t for t in _texts(at))
    at.sidebar.select_slider(key="delta_select").set_value(0.5).run()
    assert not at.exception
    at.sidebar.selectbox(key="mus_select").set_value("zufall").run()
    assert not at.exception and at.sidebar.select_slider(key="delta_select").value == 0.5
    at.toggle(key="show_best").set_value(True).run()
    assert not at.exception


def test_on_demand_series_appear_and_stay():
    at = _app()
    assert not any("Auf dem Wald des Plans" in t for t in _texts(at))
    at.button(key="ex1_run").click().run()
    assert not at.exception and any(t.startswith("Auf dem Wald des Plans nach 2 000 Runden (Lücke 0,2): OMM mit c = 1,5") for t in _texts(at))
    at.button(key="ex2_run").click().run()
    assert not at.exception and any(t.startswith("Zuwächse des Bedauerns bei den letzten beiden Verdopplungen von T") for t in _texts(at))
    at.button(key="ex3_run").click().run()
    assert not at.exception and any(t.startswith("Bei festem T = 2 000 ist das Bedauern **nicht monoton in der Lücke**") for t in _texts(at))
    at.button(key="ex4_run").click().run()
    assert not at.exception and any(t.startswith("Bei Kardinalität 3 und 10 / 20 / 40 / 80 Armen") for t in _texts(at))
    at.button(key="ex5_run").click().run()
    assert not at.exception and any(t.startswith("Bei Δ = 0,2: OMM mit c = 1,5") for t in _texts(at))
    _click_preset(at, "Ohne Struktur")
    assert any(t.startswith("Auf dem Wald des Plans") for t in _texts(at))                      # die Ergebnisse bleiben nach anderen Änderungen


def test_playground_rounds_and_reset():
    at = _app()
    at.button(key="play_1").click().run()
    assert not at.exception and at.session_state[f"play_rounds_{PLAY}"] == 1 and any(t.startswith("Nach **1 Runde**") for t in _texts(at))
    at.button(key="play_10").click().run()
    assert not at.exception and at.session_state[f"play_rounds_{PLAY}"] == 11
    at.button(key="play_100").click().run()
    assert not at.exception and at.session_state[f"play_rounds_{PLAY}"] == 111 and any(t.startswith("Nach **111 Runden**") for t in _texts(at))
    at.button(key="play_reset").click().run()
    assert not at.exception and at.session_state[f"play_rounds_{PLAY}"] == 0 and any(t.startswith("Noch keine Runde gespielt") for t in _texts(at))


def test_playground_state_belongs_to_the_configuration():
    at = _app()
    at.button(key="play_10").click().run()
    at.sidebar.select_slider(key="c_select").set_value(0.25).run()
    assert not at.exception and any(t.startswith("Noch keine Runde gespielt") for t in _texts(at))
    at.sidebar.select_slider(key="c_select").set_value(1.5).run()
    assert any(t.startswith("Nach **10 Runden**") for t in _texts(at))


def test_every_instance_constraint_and_size_runs_without_exception():
    at = _app()
    for inst in C.INSTANCES:
        for cons in C.CONSTRAINTS:
            at.sidebar.selectbox(key="inst_select").set_value(inst).run()
            at.sidebar.selectbox(key="cons_select").set_value(cons).run()
            assert not at.exception, (inst, cons, [str(e) for e in at.exception])
            assert any(t.startswith("Beste Basis bei bekannten") for t in _texts(at)), (inst, cons)
    for v in (C.V_MIN, C.V_MAX):
        at.sidebar.selectbox(key="inst_select").set_value("gross").run()
        at.sidebar.slider(key="v_slider").set_value(v).run()
        assert not at.exception, v


def test_permalink_loads_valid_values_and_ignores_invalid_choices():
    at = _app(dict(inst="gross", v="6", seed="3", cons="farbe", k="4", mus="zufall", delta="0.1", T="500", c="0.5", rseed="5"))
    sb = at.sidebar
    assert sb.selectbox(key="inst_select").value == "gross" and sb.slider(key="v_slider").value == 6 and sb.number_input(key="seed_input").value == 3
    assert sb.selectbox(key="cons_select").value == "farbe" and sb.slider(key="k_slider").value == 4 and sb.selectbox(key="mus_select").value == "zufall"
    assert sb.select_slider(key="delta_select").value == 0.1 and sb.select_slider(key="t_select").value == 500 and sb.select_slider(key="c_select").value == 0.5 and sb.number_input(key="rseed_input").value == 5
    bad = _app(dict(inst="nichts", v="99", seed="-4", cons="nichts", k="99", mus="nichts", delta="0.33", T="7", c="9", rseed="-1"))
    b = bad.sidebar
    assert b.selectbox(key="inst_select").value == "plan" and b.slider(key="v_slider").value == C.V_MAX and b.number_input(key="seed_input").value == 0
    assert b.selectbox(key="cons_select").value == "wald" and b.slider(key="k_slider").value == C.K_MAX and b.selectbox(key="mus_select").value == "zwei"
    assert b.select_slider(key="delta_select").value == C.DEFAULT_DELTA and b.select_slider(key="t_select").value == C.DEFAULT_T and b.select_slider(key="c_select").value == C.DEFAULT_C and b.number_input(key="rseed_input").value == 0


def test_address_line_mirrors_the_settings():
    at = _app(dict(cons="farbe"))
    assert str(at.query_params["cons"]) in ("farbe", "['farbe']")


def test_pdf_button_makes_a_download():
    at = _app()
    at.button(key="pdf_make").click().run()
    assert not at.exception and "pdf_made" in at.session_state and at.session_state["pdf_made"][1][:4] == b"%PDF"


def test_pdf_builds_for_every_instance_and_constraint():
    for inst in C.INSTANCES:
        for cons in C.CONSTRAINTS:
            assert build_pdf(ev.Settings(inst, 6, 2, cons, 3, "zwei", 0.2, 250, 1.5, 1))[:4] == b"%PDF", (inst, cons)
    assert build_pdf(ev.Settings(mus="zufall", T=250))[:4] == b"%PDF"
