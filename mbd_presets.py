"""Permalink (Begrenzen), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio)."""

import random
from dataclasses import dataclass

import streamlit as st

import mbd_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: object
    default: object
    lo: object | None = None
    hi: object | None = None
    choices: tuple | None = None   # erlaubte Werte einer Auswahl; andere Werte aus der Adresszeile werden ignoriert (dann entfällt das Begrenzen)


SETTING_SPECS = {
    "inst_select": SettingSpec("inst", str, "plan", C.INSTANCES[0], C.INSTANCES[-1], C.INSTANCES),
    "v_slider": SettingSpec("v", int, C.DEFAULT_V, C.V_MIN, C.V_MAX),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
    "cons_select": SettingSpec("cons", str, "wald", C.CONSTRAINTS[0], C.CONSTRAINTS[-1], C.CONSTRAINTS),
    "k_slider": SettingSpec("k", int, C.DEFAULT_K, C.K_MIN, C.K_MAX),
    "mus_select": SettingSpec("mus", str, "zwei", C.MEANS[0], C.MEANS[-1], C.MEANS),
    "delta_select": SettingSpec("delta", float, C.DEFAULT_DELTA, C.DELTAS[0], C.DELTAS[-1], C.DELTAS),
    "t_select": SettingSpec("T", int, C.DEFAULT_T, C.T_CHOICES[0], C.T_CHOICES[-1], C.T_CHOICES),
    "c_select": SettingSpec("c", float, C.DEFAULT_C, C.C_CHOICES[0], C.C_CHOICES[-1], C.C_CHOICES),
    "rseed_input": SettingSpec("rseed", int, C.DEFAULT_RSEED, 0, C.SEED_MAX),
}
PRESET_KEYS = {"inst": "inst_select", "v": "v_slider", "seed": "seed_input", "cons": "cons_select", "k": "k_slider", "mus": "mus_select", "delta": "delta_select", "T": "t_select", "c": "c_select", "rseed": "rseed_input"}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, Zahlen auf die Reglergrenzen begrenzt, Auswahlwerte nur, wenn erlaubt."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
            except (ValueError, TypeError):
                continue
            if spec.choices is not None:
                if value not in spec.choices:
                    continue
            else:
                if spec.lo is not None:
                    value = max(spec.lo, value)
                if spec.hi is not None:
                    value = min(spec.hi, value)
            st.session_state[state_key] = value
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        if key in C.PRESETS[name]:
            st.session_state[state_key] = C.PRESETS[name][key]


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None.

    Zustandslos: verglichen wird jeder Regler aus SETTING_SPECS (ein Preset ohne Eintrag für einen Regler meint dessen
    Standardwert) mit dem Session State. Ein später ergänzter Regler braucht nur seinen Eintrag in SETTING_SPECS,
    dann hebt auch seine Änderung die Markierung auf (tests/test_layout.py prüft das für jeden Regler)."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        if all(
            st.session_state.get(state_key, spec.default) == preset.get(preset_key_of.get(state_key), spec.default)
            for state_key, spec in SETTING_SPECS.items()
        ):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)


def randomize_rseed():
    st.session_state["rseed_input"] = random.randint(0, C.SEED_MAX)
