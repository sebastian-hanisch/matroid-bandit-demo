# Matroid-Bandits – die beste Basis lernen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-matroid-bandit-demo.streamlit.app/)** -->

Vierzehntes Stück der Reihe **Matroide und Submodularität** (Bereich Kombinatorik; ein **gelbes** Stück, einzeln nach Stück 13 entschieden) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. In den Stücken davor waren die Nutzen der Leitungen bekannt oder kamen einzeln. Hier sind sie **unbekannt und verrauscht**: In jeder Runde wählt man eine **Basis** des Matroids (eine maximale zulässige Leitungsmenge), sieht für **jede gewählte Leitung** eine Ziehung (Erfolg oder Misserfolg mit unbekannter Wahrscheinlichkeit μ) und will über viele Runden nahe an der besten Basis bleiben. Gemessen wird das **Bedauern**: der entgangene erwartete Nutzen gegen die beste Basis, summiert über alle Runden. Vier Verfahren auf derselben Instanz: **optimistisches Greedy (OMM)**, **ε-Greedy**, die **zufällige Basis** und **UCB über Basen** (jede Basis ein Arm, nur ihre Summe als Rückmeldung, also ohne Struktur).

**Einordnung in die Reihe:** Nachfolger von [matroid-sekretaer-demo](../matroid-sekretaer-demo) (Stück 13), [ueber-greedy-demo](../ueber-greedy-demo) (Stück 12) und [greedy-optimalitaet-demo](../greedy-optimalitaet-demo) (Stück 5). **Abgrenzung:** `bandit-demo` (Reinforcement-Learning-Linie) und `bandit-vs-ab-demo` (Experimente-Linie) zeigen K Einzelarme, einen Arm je Runde; Kardinalität 1 ist hier der Sonderfall. Hier ist der Zug eine **Basis** (mehrere Arme zugleich unter einer Matroidschranke) mit Rückmeldung je Element.

## Warum dieses Problem

Wer die besten Leitungen nicht kennt, muss sie beim Verlegen lernen und zahlt dafür mit schlechteren Runden. Offen ist, wie viel das kostet, wovon es abhängt (Lücke zwischen den besten und den übrigen Leitungen, Armzahl, Bonuskonstante) und ob es hilft, die Struktur des Matroids zu nutzen.

## Befunde und Korrekturen gegenüber dem Plan

- **Logarithmisch ja, aber spät.** Das Wachstum ist erst für T ≫ n/Δ² logarithmisch (konstanter Zuwachs je Verdopplung von T); bei kleiner Lücke ist es in 8 000 Runden noch nicht erreicht. „Bedauern / ln T“ zeigt das nicht, der Zuwachs je Verdopplung schon.
- **Die Konstante entscheidet im Kurzbereich.** OMM mit c = 0,25 statt 1,5 hat bei Lücke 0,2 und 2 000 Runden etwa ein Drittel des Bedauerns. Die Konstante 1,5 ist die der Planung (nicht gegen den Primärtext geprüft).
- **ε-Greedy ist im Mittel stark, aber riskant:** gutes Mittel, aber schwere Ränder und am Ende nicht immer die beste Basis.
- **„Findet die beste Basis“ gilt nicht in jedem Lauf** (Standardkonstante, Lücke 0,05, 2 000 Runden: nur wenige von 30 Läufen).
- **Ohne Struktur** (jede Basis ein Arm, nur die Summe) lernt das Verfahren bei 144 bis 1 049 Basen in 2 000 Runden praktisch nichts.
- **Die Art des Matroids spielt kaum eine Rolle** (Wald gegen Kardinalität bei gleicher Armzahl und gleicher Lücke); die Armzahl und die Lücke schon.
- **Bei festem T ist das Bedauern nicht monoton in der Lücke:** bei sehr kleiner Lücke kostet jeder falsche Zug fast nichts.
- **Die Zahlen der App weichen von Phase 0 leicht ab** (andere Instanzen und Seeds, 20 statt 30 Läufe in Experiment 2 und 3): Das Muster ist gleich; bei Lücke 0,2 ist der Zuwachs je Verdopplung in der App am Ende noch leicht wachsend (nicht konstant).
- **Port 9354;** Repo `matroid-bandit-demo`, Präfix `mbd_`; nur Streamlit, Plotly und fpdf2 zur Laufzeit (reine Python-Arithmetik, kein numpy).

## Modell

**Leitungsnetz mit unbekannten Erfolgswahrscheinlichkeiten:** Standorte im Einheitsquadrat, jede mögliche Leitung ist ein Arm mit fester Erfolgswahrscheinlichkeit μ (Bernoulli). **Zwei Instanzen:** der **Plan der Reihe** (8 Standorte, 14 zufällige Leitungen, zusammenhängend) und der **große Plan** (alle Leitungen zwischen 5 bis 12 Standorten, bis 66 Arme). **Nebenbedingung:** Kardinalität (höchstens k), Farben (höchstens eine Leitung je Kabelfarbe; Leitung e hat die Farbe e mod k) oder Wald (keine geschlossenen Ringe). **Erfolgswahrscheinlichkeiten:** zwei Stufen (die Arme einer festen Basis 0,5 + Δ/2, alle anderen 0,5 − Δ/2, also alle Lücken gleich Δ) oder gleichverteilt in 0,1 bis 0,9. **Bedauern:** kumulierter Erwartungswert μ(B*) − μ(B_t), nicht die gezogenen Werte. Formeln: Expander „📐 Mathematische Formulierung“ in der App.

## Methodik

- **Beste Basis:** `best_basis` (Greedy nach μ, Rado–Edmonds); **Lücke:** `gaps` (kleinster Verlust eines Tauschs B* − f + e, über den Kreis von B* + e).
- **OMM:** `omm_index` (Mittel plus Bonus sqrt(c · ln t / T_e), unbeobachtet ∞) und Greedy nach dem Index (`greedy_basis`, schnell mit mitgeführtem Zustand).
- **ε-Greedy:** ε_t = min(1, n/t), sonst Greedy nach den beobachteten Mitteln (Start 0,5); **Zufall:** Greedy nach zufälliger Reihenfolge.
- **UCB über Basen:** `enumerate_bases` (nur bis 3 000 Basen) und `simulate(…, "ubas")`: jede Basis einmal, dann Index mittlere Summe plus sqrt(2 r² ln t / N_B); `count_bases` zählt Basen (Binomialkoeffizient, Produkt der Klassengrößen, Spannbäume nach Kirchhoff).
- **Messreihen:** `average` mittelt über Läufe (feste Seeds, kein Löser, plattformunabhängig); Bedauern bei Stützstellen als Mittel, Standardabweichung, 90 %-Quantil und Maximum, dazu der Anteil der Läufe mit bester Basis am Ende.
- **Spielwiese:** OMM wird Runde für Runde gespielt; die Runden sind deterministisch aus den Einstellungen (Präfix-konsistent).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py` und werden dort mit den Funktionen der App nachgerechnet. Bedauern nach T Runden, Läufe mit festem Seed 1.

| Beispiel | Arme | Basen | OMM | ε-Greedy | Zufall | UCB über Basen |
|---|---|---|---|---|---|---|
| Standardfall (Plan, Wald, Lücke 0,2, 2 000 Runden, c = 1,5) | 14 | 1 049 | 223,4 | 104,0 | 1 390,2 | 1 360,0 |
| Kleine Konstante (c = 0,25) | 14 | 1 049 | 49,8 | 104,0 | 1 390,2 | 1 360,0 |
| Kleine Lücke (Lücke 0,05, 5 000 Runden) | 14 | 1 049 | 440,9 | 540,7 | 870,0 | 850,8 |
| Viele Arme (12 Standorte, Wald) | 66 | 61 917 364 224 | 1 510,4 | 577,0 | 3 652,2 | nicht anwendbar |
| Ohne Struktur (4 Farben) | 14 | 144 | 276,2 | 87,8 | 1 130,8 | 1 103,0 |

| Frage | Befund |
|---|---|
| **Experiment 1: Verfahren und Zeit** (Plan, Lücke 0,2, Mittel über 20 Läufe, UCB über Basen 8) | **Wald** (1 049 Basen), nach 2 000 Runden: OMM c = 1,5 **217,1**, OMM c = 0,25 **71,1**, ε-Greedy **90,3** (± 44,5), Zufall **1 380,0**, UCB über Basen **1 358,8**. **Kardinalität 3** (364 Basen): **327,8** / **79,6** / **139,2** (± 142,4) / 943,8 / 929,9. **4 Farben** (144 Basen): **279,8** / **79,9** / **81,0** (± 81,2) / 1 132,8 / **1 101,9**. |
| **Experiment 2: logarithmische Phase** (OMM c = 1,5, Wald, 20 Läufe, T = 250 bis 8 000) | Zuwächse je Verdopplung von T: Lücke 0,4: 22,8 / 22,8 / 25,4 / 23,9 / **26,0** (konstant); 0,2: 37,9 / 50,0 / 55,7 / 57,4 / **67,3**; 0,1: 38,2 / 64,3 / 87,1 / 105,1 / **123,4**; 0,05: 31,7 / 56,9 / 92,0 / 143,6 / **204,9** (noch wachsend). |
| **Experiment 3: Lücke** (OMM, T = 2 000, 20 Läufe) | Wald, Lücke 0,5 / 0,4 / 0,3 / 0,2 / 0,1 / 0,05 / 0,02: **125,8 / 144,7 / 177,2 / 215,1 / 249,2 / 211,5 / 119,1**; Kardinalität 3: **195,1 / 227,9 / 268,2 / 314,5 / 297,9 / 201,8 / 91,2**. Maximum bei 0,1 beziehungsweise 0,2. |
| **Experiment 4: Armzahl und Art des Matroids** (OMM, Lücke 0,2, T = 2 000) | Kardinalität 3 mit 10 / 20 / 40 / 80 Armen: **205,1 / 462,0 / 781,3 / 1 047,5** (höchstmöglich 1 200). Wald gegen Kardinalität gleichen Rangs (10 / 28 / 66 Arme): **186,3 / 611,9 / 1 511,1** gegen **184,2 / 638,8 / 1 508,1**. |
| **Experiment 5: Konstante und ε-Greedy** (Wald, T = 2 000, 30 Läufe; Mittel, 90 %-Quantil, Maximum, beste Basis am Ende) | Lücke 0,2: c = 1,5 **212,4**; c = 0,5 93,6; c = 0,25 **77,9** (24 / 29 / 28 von 30); ε-Greedy 101,4 (Maximum **693,0**). Lücke 0,1: c = 1,5 249,6 (**10 von 30**); c = 0,25 104,9 (27 von 30); ε-Greedy 208,6, 90 %-Quantil **416,1**, Maximum **439,9**, **14 von 30**. Lücke 0,05: c = 1,5 **2 von 30**, c = 0,25 **15 von 30**, ε-Greedy 2 von 30. |
| **Handbeispiel** (3 Arme, μ = 0,9 / 0,5 / 0,1, höchstens einer, ohne Rauschen) | Gewählte Arme für t = 1 bis 12: **0, 1, 2, 0, 1, 0, 0, 2, 0, 1, 0, 0**; Züge **7 / 3 / 2**; Bedauern **2,8**. Bei t = 5 liegt Arm 1 vor Arm 0 (Index 2,054 gegen 1,999). Lücken bei Kardinalität 2 und μ = 0,9 / 0,8 / 0,3 / 0,2: **0,5** und **0,6**. Das Dreieck mit Pendelkante hat **3** Spannbäume, der vollständige Graph mit 5 Knoten **125**. |

## Ehrliche Grenzen

- **Rückmeldung je gewählter Leitung.** OMM nutzt sie; „UCB über Basen“ zeigt den strukturlosen Grenzfall (nur die Summe). Verfahren für die Summe als einzige Rückmeldung sind nicht gebaut.
- **Feste, unabhängige Erfolgswahrscheinlichkeiten.** Gegnerische oder sich ändernde Nutzen sind nicht gebaut; nur zwei Verteilungen der μ (zwei Stufen, gleichverteilt), kein anderes Rauschen.
- **Die Konstante** c = 1,5 ist die der Planung, nicht gegen den Primärtext geprüft; kleinere Werte liefern im Kurzbereich viel weniger Bedauern, ohne dass die Demo eine Garantie dafür nennt.
- **Logarithmisches Wachstum ist asymptotisch.** Bei kleiner Lücke und vielen Armen ist es in den gezeigten Zeiträumen nicht erreicht.
- **UCB über Basen** nur bei höchstens 3 000 Basen und nur in Standardstärke gerechnet; abgestimmte Konstanten verbessern es (in der Planung gemessen, hier nicht gebaut).
- **Nur Kardinalität, Farben und Wald; höchstens 66 Arme.** Die Matroid-Art spielt in diesen Messungen kaum eine Rolle; für andere Matroide und größere Instanzen ist nichts gemessen.
- **Kein Thompson-Sampling, kein KL-Index, keine Zeitmessung;** die Schranken der Literatur sind nicht genannt.
- **Quellen nur als Auszüge** (arXiv 1403.5045 zu Matroid-Bandits, arXiv 2512.00605 zu späteren Verbesserungen; Websuche): Form des Bonus, Konstante und Schranken sind nicht übernommen und nicht gegen die Primärtexte geprüft.

## Verifikation

- **Kern:** Greedy, Lücken, Index, Basen zählen und aufzählen, Läufe und das Protokoll gegen Handrechnung (`tests/conftest.py`, `tests/test_algorithm.py`); Randfälle: ein Arm, k > n, gleiche Mittel, eine Farbe, Basis ohne Außenarme, UCB über Basen über der Grenze, Reglerecken, Spielwiese (`tests/test_edge_cases.py`).
- **Orakel** (`tests/test_oracle_bandit.py`): schnelles Greedy gegen die einfache Fassung (auch bei vielen Gleichständen); beste Basis gegen alle Basen; Lücken als Verlust der besten Basis mit dem Arm gegen die Kreisformel; Basenzahl gegen Aufzählung, Kirchhoff gegen v^(v−2); Bedauern aus der Wahlfolge neu berechnet.
- **Eigenschaften** (`tests/test_properties.py`): Bedauern nie negativ und die Kurve nie fallend; OMM zieht jeden Arm früh; größere Konstante erkundet mehr; Zufall linear; OMM findet die beste Basis bei großer Lücke; Zuwachs je Verdopplung ebnet sich bei großer Lücke ein, bei kleiner nicht; Art des Matroids gleichgültig; Bedauern nicht monoton in der Lücke; strukturloser Vergleich lernt nicht.
- **Verdikte und Presets:** jeder Zweig und jede Zahl der Verdikte; jedes Preset zeigt den versprochenen Effekt; kein einzelner Reglerwechsel trifft ein anderes Preset.
- **Zahlen aus dieser README:** `tests/test_claims.py`.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an den Grenzen), Hauptansicht, fünf Experimente, Spielwiese (Runden, Zurücksetzen, Zustand je Konfiguration), Permalink, PDF; Layout (Kopf, Schnellstart, Hervorhebung) und Footer.
- **Umfang:** siehe `pytest --collect-only -q tests`.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche: ein Lauf, Kernfrage, fünf Experimente, Spielwiese, Grenzen, Formeln |
| `mbd_constants.py` | Reglergrenzen, Auswahlwerte, Messgrößen, Farben, Presets |
| `mbd_scenario.py` | Plan, Leitungen, Erfolgswahrscheinlichkeiten |
| `mbd_algorithm.py` | Matroid-Orakel, Greedy, Lücken, Basen, die vier Verfahren |
| `mbd_evaluation.py` | Kennzahlen, Messreihen der Experimente, Spielwiese, Verdikte |
| `mbd_visualization.py` | Karte, Bedauern-Kurven, Arme, Wachstum, Balken |
| `mbd_presets.py` | Permalink, Presets, Zufalls-Seeds |
| `mbd_layout.py` | fester Kopf |
| `mbd_pdf_export.py` | PDF des aktuellen Beispiels |
| `tests/` | Kern, Orakel, Eigenschaften, Verdikte, Presets, Claims, Randfälle, Oberfläche, Layout, Footer, Importe |

## Bewusst nicht umgesetzt

- Beweise der Schranken; Thompson-Sampling und KL-Index; kombinatorische Bandits allgemein (Pfade, Matchings); Rückmeldung nur der Summe in OMM; Kontext; gegnerische Nutzen; Zeit- und Batchverfahren.
- Abgestimmte Konstanten für UCB über Basen und eine längere Laufzeit als 5 000 Runden in der Hauptansicht.
- Erklärseite „verständlich erklärt“ und Website-Einbindung (erst mit der vollständigen Linie).

## Lokal ausführen

```bash
pip install -r requirements.txt
streamlit run app.py
```

Tests: `pip install -r requirements-dev.txt`, dann `python -m pytest tests -q`. Die CI läuft mit Python 3.12 (`.github/workflows/tests.yml`); die in Streamlit Cloud eingestellte Python-Version ist beim Deploy zu nennen.

Gebaut mit Streamlit, Plotly und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
