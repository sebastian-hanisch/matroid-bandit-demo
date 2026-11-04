"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, und jedes Preset zeigt den Effekt, den sein Hilfetext verspricht."""

import mbd_constants as C
import mbd_evaluation as ev
import mbd_presets as P


def _view(name):
    s = ev.Settings(**C.PRESETS[name])
    return s, ev.run_view(s)


def _r(v, algo):
    return round(v["runs"][algo]["regret"])


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name] and "Gerüst" not in C.PRESET_HELP[name]


def test_preset_values_are_inside_the_bounds_and_choices():
    for p in C.PRESETS.values():
        assert p["inst"] in C.INSTANCES and C.V_MIN <= p["v"] <= C.V_MAX and 0 <= p["seed"] <= C.SEED_MAX and p["cons"] in C.CONSTRAINTS and C.K_MIN <= p["k"] <= C.K_MAX
        assert p["mus"] in C.MEANS and p["delta"] in C.DELTAS and p["T"] in C.T_CHOICES and p["c"] in C.C_CHOICES and 0 <= p["rseed"] <= C.SEED_MAX


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings()
    d = ev.Settings()
    keys = ("inst_select", "v_slider", "seed_input", "cons_select", "k_slider", "mus_select", "delta_select", "t_select", "c_select", "rseed_input")
    assert [P.SETTING_SPECS[key].default for key in keys] == [d.inst, d.v, d.seed, d.cons, d.k, d.mus, d.delta, d.T, d.c, d.rseed]


def test_setting_specs_cover_every_preset_key_and_have_valid_defaults():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    for spec in P.SETTING_SPECS.values():
        assert spec.choices is None or (spec.default in spec.choices and spec.lo in spec.choices and spec.hi in spec.choices)


def test_no_single_regler_change_of_the_default_lands_on_another_preset():
    """Das Layout setzt jeden Regler auf seinen Höchstwert (oder Tiefstwert): das darf kein Preset treffen, sonst bliebe ein Preset markiert."""
    default = dict(C.PRESETS["Standardfall (Voreinstellung)"])
    for state_key, spec in P.SETTING_SPECS.items():
        key = next(k for k, v in P.PRESET_KEYS.items() if v == state_key)
        for value in (spec.hi, spec.lo):
            if value == default[key]:
                continue
            variant = {**default, key: value}
            assert all(variant != preset for preset in C.PRESETS.values()), (state_key, value)


def test_preset_numbers_in_the_help_texts_hold():
    h = C.PRESET_HELP
    s, v = _view("Standardfall (Voreinstellung)")
    assert (_r(v, "omm"), _r(v, "eps"), _r(v, "zufall"), _r(v, "ubas"), v["b"]["n_bases"]) == (223, 104, 1390, 1360, 1049)
    assert all(x in h["Standardfall (Voreinstellung)"] for x in ("223", "104", "1 390", "1 360", "1 049"))
    s, v = _view("Kleine Konstante")
    assert (_r(v, "omm"), _r(v, "eps")) == (50, 104) and "50 statt 223" in h["Kleine Konstante"] and "(104)" in h["Kleine Konstante"]
    s, v = _view("Kleine Lücke")
    assert (_r(v, "omm"), _r(v, "zufall")) == (441, 870) and "OMM 441 gegen Zufall 870" in h["Kleine Lücke"]
    s, v = _view("Viele Arme")
    assert (_r(v, "omm"), _r(v, "eps"), _r(v, "zufall"), v["b"]["n_bases"], "ubas" in v["runs"]) == (1510, 577, 3652, 61917364224, False)
    assert all(x in h["Viele Arme"] for x in ("1 510", "577", "3 652", "61 917 364 224"))
    s, v = _view("Ohne Struktur")
    assert (_r(v, "omm"), _r(v, "ubas"), _r(v, "zufall"), v["b"]["n_bases"]) == (276, 1103, 1131, 144) and all(x in h["Ohne Struktur"] for x in ("276", "1 103", "1 131"))


def test_presets_use_the_setting_they_describe():
    assert ev.Settings(**C.PRESETS["Kleine Konstante"]).c == 0.25 and ev.Settings(**C.PRESETS["Kleine Lücke"]).delta == 0.05 and ev.Settings(**C.PRESETS["Viele Arme"]).inst == "gross"
    assert ev.Settings(**C.PRESETS["Ohne Struktur"]).cons == "farbe"
