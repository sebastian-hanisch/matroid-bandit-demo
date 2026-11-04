"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import mbd_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=340):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _lines(inst, ids):
    xs, ys = [], []
    for e in ids:
        u, v = inst.edges[e]
        (x0, y0), (x1, y1) = inst.points[u], inst.points[v]
        xs += [x0, x1, None]
        ys += [y0, y1, None]
    return xs, ys


def build_map(inst, chosen=(), best=(), label_mu=None, height=430):
    """Leitungen (dünn grau), die beste Basis (orange unterlegt) und die zuletzt gewählte Basis (dick blaugrün). label_mu: Liste der wahren μ zum Beschriften (nur kleine Pläne)."""
    chosen = list(chosen)
    fig = go.Figure()
    rest = [e for e in range(inst.m) if e not in set(chosen)]
    if rest:
        xs, ys = _lines(inst, rest)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_OTHER, width=1.2), name="nicht gewählt", hoverinfo="skip"))
    if best:
        xs, ys = _lines(inst, list(best))
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_OPT, width=14), name="beste Basis", hoverinfo="skip"))
    if chosen:
        xs, ys = _lines(inst, chosen)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_CHOSEN, width=5), name="zuletzt gewählt", hoverinfo="skip"))
    if label_mu is not None:
        mids = [((inst.points[inst.edges[e][0]][0] + inst.points[inst.edges[e][1]][0]) / 2, (inst.points[inst.edges[e][0]][1] + inst.points[inst.edges[e][1]][1]) / 2) for e in range(inst.m)]
        fig.add_trace(go.Scatter(x=[p[0] for p in mids], y=[p[1] for p in mids], mode="text", text=[f"{label_mu[e]:.2f}".replace(".", ",") for e in range(inst.m)], textfont=dict(size=11), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=[p[0] for p in inst.points], y=[p[1] for p in inst.points], mode="markers+text", text=[inst.name(i) for i in range(inst.n)], textposition="top center", textfont=dict(size=13),
                             marker=dict(size=13, symbol="square", color=C.COLOR_NODE, line=dict(color="white", width=1.2)), hovertemplate="%{text}<extra></extra>", showlegend=False))
    fig.add_trace(go.Scatter(x=[-0.05, 1.05], y=[-0.05, 1.05], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False)
    return _base(fig, height)


def build_regret_curves(curves, height=340):
    """Kumuliertes Bedauern gegen die Runde; curves = [(Name, xs, ys, Farbe)]."""
    fig = go.Figure([go.Scatter(x=xs, y=ys, mode="lines", name=name, line=dict(color=color, width=2.5), hovertemplate="Runde %{x}: %{y:.1f}<extra>" + name + "</extra>") for name, xs, ys, color in curves])
    fig.update_xaxes(title_text="Runde")
    fig.update_yaxes(title_text="kumuliertes Bedauern")
    return _base(fig, height)


def build_arms(labels, mu, means, pulls, in_best, height=320):
    """Je Leitung (nach wahrem μ sortiert): wahres μ (Linie), Schätzung (Punkte) und Züge (Balken, rechte Achse); die Balken der besten Basis sind blaugrün."""
    order = sorted(range(len(labels)), key=lambda e: (-mu[e], e))
    xs = [labels[e] for e in order]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[pulls[e] for e in order], name="Züge", marker_color=["rgba(47,107,101,0.55)" if in_best[e] else "rgba(150,150,150,0.45)" for e in order], yaxis="y2", hovertemplate="%{x}: %{y} Züge<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[mu[e] for e in order], mode="lines+markers", name="wahres μ", line=dict(color="#d95f02", width=2), hovertemplate="%{x}: μ = %{y:.3f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[means[e] for e in order], mode="markers", name="Schätzung", marker=dict(size=9, color="#4c78a8", symbol="diamond"), hovertemplate="%{x}: Schätzung %{y:.3f}<extra></extra>"))
    fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Züge", fixedrange=True), barmode="overlay")
    fig.update_xaxes(type="category", title_text="Leitung (nach wahrem μ sortiert)")
    fig.update_yaxes(title_text="Erfolgswahrscheinlichkeit", range=[0, 1.02])
    return _base(fig, height)


def build_growth(rows, height=340):
    """Kumuliertes Bedauern gegen T (logarithmische Achse) je Lücke."""
    palette = ["#4c78a8", "#2F6B65", "#d95f02", "#7b4ea3"]
    fig = go.Figure()
    for i, r in enumerate(rows):
        fig.add_trace(go.Scatter(x=list(C.E2_CHECKPOINTS), y=r["values"], mode="lines+markers", name=f"Δ = {str(r['delta']).replace('.', ',')}", line=dict(color=palette[i % 4], width=2.5), hovertemplate="T = %{x}: %{y:.1f}<extra></extra>"))
    fig.update_xaxes(title_text="Runden T (logarithmisch)", type="log", tickvals=list(C.E2_CHECKPOINTS))
    fig.update_yaxes(title_text="Bedauern")
    return _base(fig, height)


def build_grouped_bars(categories, series, x_title, y_title, height=340):
    """Gruppierte Balken: series = [(Name, Werte, Farbe)]."""
    fig = go.Figure([go.Bar(name=name, x=list(categories), y=list(values), marker_color=color, hovertemplate=name + ": %{y:.1f}<extra></extra>") for name, values, color in series])
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text=x_title, type="category")
    fig.update_yaxes(title_text=y_title)
    return _base(fig, height)


def build_gap_lines(rows, height=340):
    """Bedauern bei festem T gegen die Lücke Δ; eine Linie je Nebenbedingung."""
    fig = go.Figure()
    for name, color in (("Wald", "#2F6B65"), ("Kardinalität 3", "#d95f02")):
        sub = [r for r in rows if r["matroid"] == name]
        fig.add_trace(go.Scatter(x=[r["delta"] for r in sub], y=[r["regret"] for r in sub], mode="lines+markers", name=name, line=dict(color=color, width=2.5), hovertemplate="Δ = %{x}: %{y:.1f}<extra>" + name + "</extra>"))
    fig.update_xaxes(title_text="Lücke Δ", type="log", tickvals=list(C.E3_DELTAS), ticktext=[str(d).replace(".", ",") for d in C.E3_DELTAS])
    fig.update_yaxes(title_text="Bedauern nach 2 000 Runden")
    return _base(fig, height)
