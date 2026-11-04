"""Matroid-Bandits - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 14 der Reihe „Matroide und Submodularität“ (Bereich Kombinatorik). Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import mbd_constants as C
from mbd_evaluation import (
    Settings,
    curve_points,
    de,
    element_rows,
    ex1_series,
    ex1_table,
    ex2_series,
    ex2_table,
    ex3_series,
    ex3_table,
    ex4_series,
    ex4_table,
    ex5_series,
    ex5_table,
    num,
    play_round_rows,
    play_rows,
    play_view,
    prozent,
    run_rows,
    run_view,
    verdict_ex1,
    verdict_ex2,
    verdict_ex3,
    verdict_ex4,
    verdict_ex5,
    verdict_play,
    verdict_run,
    zahl,
)
from mbd_layout import dunkles_design, kopf_css
from mbd_pdf_export import build_pdf
from mbd_presets import bounds, init_session_state_defaults, load_permalink_settings, randomize_rseed, randomize_seed, sidebar_presets, sync_query_params
from mbd_visualization import build_arms, build_gap_lines, build_grouped_bars, build_growth, build_map, build_regret_curves

st.set_page_config(page_title="Matroid-Bandits – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner="Die Verfahren spielen die Runden (bei vielen Basen einige Sekunden) …")
def _run(settings):
    return run_view(settings)


@st.cache_data(show_spinner="Experiment 1 rechnen (etwa eine Viertelminute) …")
def _ex1():
    return ex1_series()


@st.cache_data(show_spinner="Experiment 2 rechnen (einige Sekunden) …")
def _ex2():
    return ex2_series()


@st.cache_data(show_spinner="Experiment 3 rechnen (einige Sekunden) …")
def _ex3():
    return ex3_series()


@st.cache_data(show_spinner="Experiment 4 rechnen (einige Sekunden) …")
def _ex4():
    return ex4_series()


@st.cache_data(show_spinner="Experiment 5 rechnen (etwa eine Viertelminute) …")
def _ex5():
    return ex5_series()


def _add_rounds(key, n):
    st.session_state[key] = st.session_state.get(key, 0) + n


def _reset_rounds(key):
    st.session_state[key] = 0


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in mbd_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🎰 Matroid-Bandits – die beste Basis lernen")
st.markdown(
    """
In den Stücken davor waren die Nutzen der Leitungen bekannt oder kamen einzeln. Hier sind sie **unbekannt und verrauscht**: In jeder Runde wählt man eine **Basis** des Matroids (eine maximale zulässige Leitungsmenge), sieht für **jede gewählte Leitung** eine Ziehung (Erfolg oder Misserfolg mit unbekannter Wahrscheinlichkeit μ) und will über viele Runden nahe an der besten Basis bleiben. Gemessen wird das **Bedauern**: der entgangene erwartete Nutzen gegen die beste Basis, summiert über alle Runden. Vier Verfahren auf **derselben Instanz**: **optimistisches Greedy (OMM)**, das Greedy auf optimistisch geschätzten Nutzen wählt; **ε-Greedy**; die **zufällige Basis**; und **UCB über Basen**, das jede Basis als eigenen Arm behandelt und nur ihre Summe sieht, also **ohne Struktur**.

Dies ist das **vierzehnte Stück** der Reihe „Matroide und Submodularität“ (ein gelbes Stück). Weiter unten: fünf Experimente (🔬), eine **Spielwiese „Runde für Runde“**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**. Die Einzelarm-Fälle zeigen `bandit-demo` und `bandit-vs-ab-demo` (Kardinalität 1 ist der Sonderfall); hier geht es um mehrere Arme zugleich unter einer Matroidschranke.
"""
)

with st.expander("So hängt es zusammen", expanded=True):
    st.markdown(
        """
1. **Beste Basis:** Kennte man alle Erfolgswahrscheinlichkeiten, nähme man die Leitungen nach absteigendem μ und ließe weg, was die Unabhängigkeit verletzt (Greedy, Stück 1 und 5). Das Bedauern misst den Abstand dazu.
2. **Lücke Δ:** Für jede Leitung e außerhalb der besten Basis ist Δ_e der kleinste Verlust eines Tauschs B* − f + e: Je kleiner, desto schwerer ist e von der besten Basis zu unterscheiden.
3. **OMM:** Jede Leitung bekommt den Index μ̂_e + sqrt(c · ln t / T_e) (Mittelwert plus Bonus für Unsicherheit; unbeobachtete Leitungen: ∞). Dann wählt man die Basis mit Greedy nach dem Index. Rückmeldung je gewählter Leitung, also lernen alle Arme der Basis zugleich.
4. **ε-Greedy:** Mit Wahrscheinlichkeit min(1, n/t) eine zufällige Basis, sonst Greedy nach den beobachteten Mitteln.
5. **UCB über Basen:** Jede Basis ist ein Arm, beobachtet wird nur die Summe der Basis. Mit vielen Basen kommt man in kurzer Zeit nicht über das Ausprobieren hinaus (nur bei höchstens 3 000 Basen gerechnet).
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Instanz**")
    inst = st.selectbox("Instanz", C.INSTANCES, key="inst_select", format_func=C.INSTANCE_NAMES.get,
                        help="Der Plan der Reihe hat 8 Standorte und 14 Leitungen; der große Plan hat alle Leitungen zwischen den Standorten (bis 12 Standorte, 66 Leitungen).")
    v = st.slider("Standorte des großen Plans", *bounds("v_slider"), key="v_slider", help="Wie viele Standorte der große Plan hat; jede Leitung zwischen zwei Standorten ist ein Arm. Beim Plan der Reihe ohne Wirkung.")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1, help="Bestimmt Standorte, Leitungen und die Erfolgswahrscheinlichkeiten.")
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    st.markdown("**Nebenbedingung**")
    cons = st.selectbox("Was darf zusammen gewählt werden?", C.CONSTRAINTS, key="cons_select", format_func=C.CONSTRAINT_NAMES.get,
                        help="Kardinalität: höchstens k Leitungen. Farben: höchstens eine Leitung je Kabelfarbe (Partitionsmatroid). Wald: keine geschlossenen Ringe (graphisches Matroid).")
    k = st.slider("Zahl k", *bounds("k_slider"), key="k_slider", help="Kardinalität: höchstens k Leitungen; Farben: Zahl der Kabelfarben (Leitung e hat die Farbe e mod k). Beim Wald ohne Wirkung.")
    st.markdown("**Erfolgswahrscheinlichkeiten**")
    mus = st.selectbox("Verteilung der μ", C.MEANS, key="mus_select", format_func=C.MEANS_NAMES.get, help="Zwei Stufen: alle Lücken sind gleich Δ. Zufällig: gleichverteilt, die Lücken sind verschieden.")
    delta = st.select_slider("Lücke Δ (bei zwei Stufen)", options=list(C.DELTAS), key="delta_select", format_func=num, help="Wie weit die Arme der besten Basis über den anderen liegen. Je kleiner, desto schwerer.")
    st.markdown("**Lauf**")
    T = st.select_slider("Runden T", options=list(C.T_CHOICES), key="t_select", format_func=zahl)
    c = st.select_slider("Konstante c des Bonus", options=list(C.C_CHOICES), key="c_select", format_func=num, help="Größe des Bonus sqrt(c · ln t / T_e) bei OMM: groß heißt vorsichtig und viel Erkunden, klein heißt gierig. 1,5 ist die Konstante der Planung.")
    rseed = st.number_input("Seed der Läufe", *bounds("rseed_input"), key="rseed_input", step=1, help="Bestimmt die gezogenen Erfolge und die Zufallsbasen.")
    st.button("🎲 Neue Läufe", width="stretch", on_click=randomize_rseed)

sync_query_params({"inst_select": inst, "v_slider": int(v), "seed_input": int(seed), "cons_select": cons, "k_slider": int(k), "mus_select": mus, "delta_select": float(delta), "t_select": int(T), "c_select": float(c), "rseed_input": int(rseed)})

settings = Settings(inst, int(v), int(seed), cons, int(k), mus, float(delta), int(T), float(c), int(rseed))
play_id = f"{inst}_{settings.v}_{settings.seed}_{cons}_{settings.k}_{mus}_{settings.delta}_{settings.c}_{settings.rseed}"

# --- Ein Lauf -------------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ein Lauf: vier Verfahren, dieselbe Instanz")
rv = _run(settings)
b = rv["b"]
ins = b["inst"]
st.caption(f"{C.INSTANCE_NAMES[inst]}: {zahl(ins.m)} Leitungen (Arme), Rang {b['rank']}, {zahl(b['n_bases'])} Basen. Zulässig: {C.CONSTRAINT_NAMES[cons]}" + (f", k = {settings.k}" if cons != "wald" else "") + f". {zahl(settings.T)} Runden.")
mc = st.columns(4)
for col, a in zip(mc, C.ALGOS):
    if a in rv["runs"]:
        r = rv["runs"][a]
        col.metric(C.ALGO_NAMES[a].split(" (")[0], de(r["regret"], 1), delta=f"{prozent(r['regret'] / rv['runs']['zufall']['regret'], 0)} % des Zufalls" if rv["runs"]["zufall"]["regret"] else None, delta_color="off", help="Bedauern nach T Runden.")
    else:
        col.metric(C.ALGO_NAMES[a].split(" (")[0], "–", help=f"Nicht anwendbar: {zahl(b['n_bases'])} Basen, mehr als {zahl(3000)}.")
show_best = st.toggle("Beste Basis einblenden", value=False, key="show_best", help="Legt die beste Basis orange unter die Karte.")
col_a, col_b = st.columns([3, 2])
with col_a:
    st.plotly_chart(build_map(ins, rv["runs"]["omm"]["last"], b["best"] if show_best else (), label_mu=b["mu"] if ins.m <= 20 else None), width="stretch", key="map_run")
    st.caption("Dünn grau: mögliche Leitungen (beim kleinen Plan mit dem wahren μ beschriftet); dick blaugrün: die Basis, die OMM in der letzten Runde gewählt hat; orange unterlegt: die beste Basis.")
with col_b:
    st.markdown("**Die Verfahren nach T Runden**")
    st.dataframe(run_rows(settings, rv), hide_index=True, width="stretch")
curves = []
for a, r in rv["runs"].items():
    xs, ys = curve_points(r["curve"])
    curves.append((C.ALGO_NAMES[a].split(" (")[0], xs, ys, C.COLORS[a]))
st.markdown("**Kumuliertes Bedauern**")
st.plotly_chart(build_regret_curves(curves), width="stretch", key="curve_chart")
st.markdown("**Was OMM über die Leitungen gelernt hat**")
om = rv["runs"]["omm"]
st.plotly_chart(build_arms([ins.label(e) for e in range(ins.m)], b["mu"], [m if m is not None else float("nan") for m in om["means"]], om["pulls"], [e in set(b["best"]) for e in range(ins.m)]), width="stretch", key="arms_chart")
with st.expander("Tabelle der Leitungen"):
    st.dataframe(element_rows(rv), hide_index=True, width="stretch")

if st.button("📄 PDF des aktuellen Beispiels erstellen", key="pdf_make"):
    st.session_state["pdf_made"] = (settings, build_pdf(settings))
made = st.session_state.get("pdf_made")
if made and made[0] == settings:
    st.download_button("⬇️ PDF herunterladen", data=made[1], file_name="matroid-bandits.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie schnell lernt man die beste Basis, und was kostet das Lernen?")
kind_v, text_v = verdict_run(settings, rv)
getattr(st, kind_v)(text_v)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Verfahren und Zeit")
st.caption(f"Plan der Reihe (Seed {C.DEFAULT_SEED}), Lücke 0,2, drei Nebenbedingungen; Mittel über {C.E1_RUNS} Läufe je Zelle ({C.E1_UBAS_RUNS} bei UCB über Basen), ± Standardabweichung. OMM mit der Standardkonstante 1,5 und mit 0,25.")
if st.button("📊 Verfahren vergleichen", key="ex1_run"):
    st.session_state["ex1_done"] = True
if st.session_state.get("ex1_done"):
    r1 = _ex1()
    st.dataframe(ex1_table(r1), hide_index=True, width="stretch")
    cats = [f"{n} ({zahl(nb)} Basen)" for n, nb in dict.fromkeys((r["matroid"], r["n_bases"]) for r in r1)]
    keys = list(dict.fromkeys(r["algo"] for r in r1))
    cols = {"omm": C.COLORS["omm"], "omm025": "#6aa89f", "eps": C.COLORS["eps"], "zufall": C.COLORS["zufall"], "ubas": C.COLORS["ubas"]}
    names = {"omm": "OMM (c = 1,5)", "omm025": "OMM (c = 0,25)", "eps": "ε-Greedy", "zufall": "Zufällige Basis", "ubas": "UCB über Basen"}
    series = [(names[a], [next(r["mean"][C.E1_T] for r in r1 if r["algo"] == a and r["matroid"] == n.split(" (")[0]) for n in cats], cols[a]) for a in keys]
    st.plotly_chart(build_grouped_bars(cats, series, "Nebenbedingung", f"Bedauern nach {zahl(C.E1_T)} Runden"), width="stretch", key="ex1_chart")
    kind_v, text_v = verdict_ex1(r1)
    getattr(st, kind_v)(text_v)

st.subheader("🔬 Experiment 2: Wann wächst das Bedauern logarithmisch?")
st.caption("OMM (c = 1,5) auf dem Wald des Plans, vier Lücken, T verdoppelt von 250 bis 8 000; Mittel über 20 Läufe. Logarithmisches Wachstum heißt: **konstanter Zuwachs je Verdopplung von T**.")
if st.button("📊 Wachstum messen", key="ex2_run"):
    st.session_state["ex2_done"] = True
if st.session_state.get("ex2_done"):
    r2 = _ex2()
    st.plotly_chart(build_growth(r2), width="stretch", key="ex2_chart")
    st.dataframe(ex2_table(r2), hide_index=True, width="stretch")
    kind_v, text_v = verdict_ex2(r2)
    getattr(st, kind_v)(text_v)

st.subheader("🔬 Experiment 3: Bedauern gegen die Lücke")
st.caption("OMM (c = 1,5), T = 2 000, Wald und Kardinalität 3 auf dem Plan, sieben Lücken von 0,5 bis 0,02; Mittel über 20 Läufe.")
if st.button("📊 Lücken vergleichen", key="ex3_run"):
    st.session_state["ex3_done"] = True
if st.session_state.get("ex3_done"):
    r3 = _ex3()
    st.plotly_chart(build_gap_lines(r3), width="stretch", key="ex3_chart")
    st.dataframe(ex3_table(r3), hide_index=True, width="stretch")
    kind_v, text_v = verdict_ex3(r3)
    getattr(st, kind_v)(text_v)

st.subheader("🔬 Experiment 4: Armzahl und Art des Matroids")
st.caption("OMM (c = 1,5), Lücke 0,2, T = 2 000: Kardinalität 3 mit 10 bis 80 Armen, und Wald gegen Kardinalität gleichen Rangs auf vollständigen Graphen mit 5, 8 und 12 Standorten; Mittel über 20 Läufe.")
if st.button("📊 Armzahl und Matroid-Art messen", key="ex4_run"):
    st.session_state["ex4_done"] = True
if st.session_state.get("ex4_done"):
    r4 = _ex4()
    st.dataframe(ex4_table(r4), hide_index=True, width="stretch")
    kind_v, text_v = verdict_ex4(r4)
    getattr(st, kind_v)(text_v)

st.subheader("🔬 Experiment 5: Die Konstante und ε-Greedy")
st.caption("Wald auf dem Plan, vier Lücken, T = 2 000, 30 Läufe je Zeile: OMM mit c = 1,5, 0,5 und 0,25 gegen ε-Greedy. Mittel, Median, 90 %-Quantil, Maximum und die Zahl der Läufe, die am Ende die beste Basis wählen.")
if st.button("📊 Konstante und ε-Greedy messen", key="ex5_run"):
    st.session_state["ex5_done"] = True
if st.session_state.get("ex5_done"):
    r5 = _ex5()
    st.dataframe(ex5_table(r5), hide_index=True, width="stretch")
    kind_v, text_v = verdict_ex5(r5)
    getattr(st, kind_v)(text_v)

st.markdown("---")

# --- Spielwiese ----------------------------------------------------------------------------------------------------------------------------------

st.subheader("🛠️ Spielwiese: Runde für Runde")
st.caption("OMM mit den Einstellungen oben (Konstante, Instanz, Seed der Läufe) wird Runde für Runde gespielt. Sie sehen die geschätzten Mittel, die Indizes der nächsten Runde und die gewählten Basen; dieselben Einstellungen liefern immer dieselben Runden.")
play_key = f"play_rounds_{play_id}"
if play_key not in st.session_state:
    st.session_state[play_key] = 0
pc = st.columns(4)
pc[0].button("▶️ 1 Runde", key="play_1", width="stretch", on_click=_add_rounds, args=(play_key, 1))
pc[1].button("⏩ 10 Runden", key="play_10", width="stretch", on_click=_add_rounds, args=(play_key, 10))
pc[2].button("⏭️ 100 Runden", key="play_100", width="stretch", on_click=_add_rounds, args=(play_key, 100))
pc[3].button("↩️ Von vorn", key="play_reset", width="stretch", on_click=_reset_rounds, args=(play_key,))
pv = play_view(settings, st.session_state[play_key])
kind_v, text_v = verdict_play(settings, pv)
getattr(st, kind_v)(text_v)
if pv["steps"]:
    xs, ys = curve_points(pv["curve"])
    st.plotly_chart(build_regret_curves([("OMM", xs, ys, C.COLORS["omm"])], height=260), width="stretch", key="play_curve")
    st.markdown("**Die letzten Runden**")
    st.dataframe(play_round_rows(pv), hide_index=True, width="stretch", height=240)
st.markdown("**Die Leitungen: Schätzung und Index für die nächste Runde**")
st.dataframe(play_rows(pv), hide_index=True, width="stretch", height=260)
st.plotly_chart(build_map(ins, pv["last"], b["best"] if pv["steps"] else (), label_mu=b["mu"] if ins.m <= 20 else None, height=360), width="stretch", key="map_play")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist (wer setzt an) |
|---|---|
| **Rückmeldung je gewählter Leitung** | OMM nutzt, dass man den Erfolg jeder gewählten Leitung sieht. Sieht man nur die Summe der Basis, braucht man andere Verfahren; „UCB über Basen“ zeigt den strukturlosen Grenzfall. **(Stück 14, Experiment 1)** |
| **Feste, unabhängige Erfolgswahrscheinlichkeiten** | Die Erfolge werden unabhängig aus festen μ gezogen. Gegnerische oder sich ändernde Nutzen sind nicht gebaut. **(nicht in dieser Reihe)** |
| **Nur zwei Verteilungen der μ** | Zwei Stufen (alle Lücken gleich) und gleichverteilt; keine schweren Ränder, keine Gauß-Rauschen. **(nicht allgemein)** |
| **Die Konstante** | Die Bonus-Konstante c = 1,5 ist die der Planung (nicht gegen den Primärtext geprüft); kleinere Werte liefern im Kurzbereich viel weniger Bedauern (Experiment 5), ohne dass die Demo eine Garantie dafür nennt. **(nicht geprüft)** |
| **Logarithmisches Wachstum ist asymptotisch** | Es beginnt erst für T ≫ n/Δ² (Faustregel, nicht gemessen); bei kleiner Lücke und vielen Armen ist es in den gezeigten Zeiträumen noch nicht erreicht (Experiment 2 und 4). **(Literatur, hier gemessen)** |
| **Nur Kardinalität, Farben und Wald; Instanzen mit höchstens 66 Armen** | Die Art des Matroids spielt bei gleichem Rang und gleicher Armzahl in den Messungen kaum eine Rolle; für andere Matroide und größere Instanzen ist nichts gemessen. **(nicht allgemein)** |
| **UCB über Basen nur bei höchstens 3 000 Basen** | Darüber ist die Aufzählung zu groß; die Demo zeigt „nicht anwendbar“. Das Verfahren ist in Standardstärke gerechnet; abgestimmte Konstanten würden es verbessern. **(Messung)** |
| **Literaturschranken nicht genannt** | Die lückenabhängige Schranke ist in der Literatur auf Partitionsmatroiden scharf (Auszug, nicht gegen den Primärtext geprüft); die Demo nennt keine Formel. **(Literatur)** |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben** ein Matroid $M = (E, \mathcal I)$ mit Basen $\mathcal B$ und Rang $r$, unbekannte Erfolgswahrscheinlichkeiten $\mu : E \to (0, 1)$. In Runde $t = 1, \dots, T$ wählt das Verfahren eine Basis $B_t \in \mathcal B$ und beobachtet für jedes $e \in B_t$ eine unabhängige Ziehung $X_{e,t} \sim \mathrm{Bernoulli}(\mu_e)$.

**Beste Basis und Bedauern.** $B^* \in \arg\max_{B \in \mathcal B} \mu(B)$ (Greedy nach $\mu$, Rado–Edmonds); $R(T) = \sum_{t=1}^{T} \big(\mu(B^*) - \mu(B_t)\big)$ (Erwartungswert, nicht die gezogenen Werte).

**Lücke.** Für $e \notin B^*$ sei $C_e$ der Kreis in $B^* + e$; $\Delta_e = \min_{f \in C_e \setminus \{e\}} (\mu_f - \mu_e)$. Bei Kardinalität $k$ ist das der Abstand von $\mu_e$ zum $k$-ten Wert.

**OMM.** Mit $\hat\mu_e(t)$ dem Mittel und $T_e(t)$ der Zahl der Beobachtungen von $e$ vor Runde $t$: $u_e(t) = \hat\mu_e(t) + \sqrt{c \ln t / T_e(t)}$ ($u_e = \infty$, wenn $T_e = 0$); $B_t$ ist die Greedy-Basis nach $u$ (Gleichstand: kleinere Nummer). Hier $c = 1{,}5$ als Voreinstellung.

**ε-Greedy.** Mit Wahrscheinlichkeit $\min(1, n/t)$ eine zufällige Basis (Greedy nach zufälliger Reihenfolge), sonst Greedy nach $\hat\mu$ (Start 0,5).

**UCB über Basen.** Jede Basis $B \in \mathcal B$ ist ein Arm; Rückmeldung $\sum_{e \in B} X_{e,t}$; Index $\bar x_B + \sqrt{2 r^2 \ln t / N_B}$, anfangs jede Basis einmal. Die Zahl der Basen: $\binom{n}{k}$ bei Kardinalität, das Produkt der Klassengrößen bei Farben, die Zahl der Spannbäume (Kirchhoff, Determinante des Laplace-Minors) im Wald; bei vollständigem Graphen mit $v$ Knoten $v^{v-2}$.

**Logarithmisches Wachstum.** Wächst $R(T)$ wie $a \ln T$, ist $R(2T) - R(T) \approx a \ln 2$ konstant; das prüft Experiment 2.

**Literatur.** Matroid-Bandits mit Rückmeldung je Element und optimistischem Greedy (Kveton et al., UAI 2014; [arXiv 1403.5045](https://arxiv.org/pdf/1403.5045)) und spätere Arbeiten zu geringerer Rechenzeit bei gleichem Bedauern ([arXiv 2512.00605](https://arxiv.org/html/2512.00605v1)). Quelle: Websuche, Auszüge, nicht gegen die Primärtexte geprüft; die Form des Bonus und die Schranken sind hier nicht übernommen, nur gemessen.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
