"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

V_MIN, V_MAX, DEFAULT_V = 5, 12, 8             # Standorte des großen Plans (vollständiger Graph: v (v − 1) / 2 Leitungen = Arme, Rang v − 1)
PLAN_NODES, PLAN_EDGES = 8, 14                 # der Plan der Reihe
SEED_MAX, DEFAULT_SEED = 999999, 8
K_MIN, K_MAX, DEFAULT_K = 1, 20, 3             # Kardinalität: höchstens k Leitungen; Farben: k Kabelfarben
INSTANCES = ("plan", "gross")
INSTANCE_NAMES = {"plan": "Plan der Reihe (8 Standorte, 14 Leitungen)", "gross": "Großer Plan (vollständiger Graph, bis 12 Standorte)"}
CONSTRAINTS = ("card", "farbe", "wald")
CONSTRAINT_NAMES = {"card": "Kardinalität: höchstens k Leitungen", "farbe": "Farben: höchstens eine Leitung je Kabelfarbe (k Farben)", "wald": "Wald: keine geschlossenen Ringe"}
MEANS = ("zwei", "zufall")
MEANS_NAMES = {"zwei": "zwei Stufen (beste Basis 0,5 + Δ/2, alle anderen 0,5 − Δ/2)", "zufall": "zufällig (gleichverteilt 0,1 bis 0,9)"}
DELTAS = (0.5, 0.4, 0.3, 0.2, 0.1, 0.05, 0.02)
DEFAULT_DELTA = 0.2
T_CHOICES = (250, 500, 1000, 2000, 5000)
DEFAULT_T = 2000
C_CHOICES = (0.1, 0.25, 0.5, 1.0, 1.5)
DEFAULT_C = 1.5                                 # Konstante des Bonus in der Planung (nicht gegen den Primärtext geprüft)
DEFAULT_RSEED = 1
ALGOS = ("omm", "eps", "zufall", "ubas")
ALGO_NAMES = {"omm": "Optimistisches Greedy (OMM)", "eps": "ε-Greedy", "zufall": "Zufällige Basis", "ubas": "UCB über Basen (ohne Struktur)"}
CURVE_POINTS = 200                              # so viele Punkte hat eine gezeichnete Kurve höchstens

# Messreihen (alle deterministisch über feste Seeds)
SERIES_SEED = 20261124
E1_T, E1_CHECKPOINTS, E1_RUNS, E1_UBAS_RUNS = 2000, (100, 500, 2000), 20, 8
E2_CHECKPOINTS, E2_DELTAS, E2_RUNS = (250, 500, 1000, 2000, 4000, 8000), (0.4, 0.2, 0.1, 0.05), 20
E3_DELTAS, E3_T, E3_RUNS = (0.5, 0.4, 0.3, 0.2, 0.1, 0.05, 0.02), 2000, 20
E4_NS, E4_VS, E4_DELTA, E4_T, E4_RUNS = (10, 20, 40, 80), (5, 8, 12), 0.2, 2000, 20
E5_DELTAS, E5_CS, E5_T, E5_RUNS = (0.4, 0.2, 0.1, 0.05), (1.5, 0.5, 0.25), 2000, 30

COLOR_CHOSEN = "#2F6B65"
COLOR_OTHER = "rgba(150,150,150,0.55)"
COLOR_OPT = "rgba(217,95,2,0.45)"
COLOR_NODE = "#4c78a8"
COLORS = {"omm": "#2F6B65", "eps": "#d95f02", "zufall": "#b0b0b0", "ubas": "#7b4ea3"}

PRESETS = {
    "Standardfall (Voreinstellung)": {"inst": "plan", "v": 8, "seed": 8, "cons": "wald", "k": 3, "mus": "zwei", "delta": 0.2, "T": 2000, "c": 1.5, "rseed": 1},
    "Kleine Konstante": {"inst": "plan", "v": 8, "seed": 8, "cons": "wald", "k": 3, "mus": "zwei", "delta": 0.2, "T": 2000, "c": 0.25, "rseed": 1},
    "Kleine Lücke": {"inst": "plan", "v": 8, "seed": 8, "cons": "wald", "k": 3, "mus": "zwei", "delta": 0.05, "T": 5000, "c": 1.5, "rseed": 1},
    "Viele Arme": {"inst": "gross", "v": 12, "seed": 8, "cons": "wald", "k": 3, "mus": "zwei", "delta": 0.2, "T": 2000, "c": 1.5, "rseed": 1},
    "Ohne Struktur": {"inst": "plan", "v": 8, "seed": 8, "cons": "farbe", "k": 4, "mus": "zwei", "delta": 0.2, "T": 2000, "c": 1.5, "rseed": 1},
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "Plan der Reihe, Wald (1 049 Basen), Lücke 0,2, 2 000 Runden, Konstante 1,5: OMM 223 Bedauern, ε-Greedy 104, Zufall 1 390, UCB über Basen (ohne Struktur) 1 360. Die Struktur lernt, die Strukturlosigkeit nicht.",
    "Kleine Konstante": "Wie der Standardfall, aber Konstante 0,25: OMM erreicht 50 statt 223 und liegt unter ε-Greedy (104). Die Konstante ist ein Regler, kein Detail.",
    "Kleine Lücke": "Lücke 0,05, 5 000 Runden: OMM 441 gegen Zufall 870. Bei so kleiner Lücke kommt das Lernen kaum voran; das Wachstum ist noch nicht logarithmisch (Experiment 2).",
    "Viele Arme": "Großer Plan mit 12 Standorten (66 Leitungen, Wald): OMM 1 510, ε-Greedy 577, Zufall 3 652; UCB über Basen ist wegen 61 917 364 224 Basen nicht anwendbar. 2 000 Runden sind für 66 Arme noch zu kurz.",
    "Ohne Struktur": "4 Kabelfarben (144 Basen): OMM 276, UCB über Basen 1 103 bei Zufall 1 131: Wer nur die Summe jeder Basis sieht, lernt in 2 000 Runden praktisch nichts.",
}
