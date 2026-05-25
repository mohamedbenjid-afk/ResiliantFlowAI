import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# ── Configuration de la page ─────────────────────────────────────────────────
st.set_page_config(page_title="Pompe P-17 — Unité B", layout="wide")

# Injection CSS pour coller au design épuré de la Photo 2 (Cartes blanches)
st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        padding: 15px 20px !important;
        border-radius: 8px !important;
    }
    .stButton>button { border-radius: 6px !important; }
    </style>
""", unsafe_allow_html=True)

# ── Constantes & Contextes ──────────────────────────────────────────────────
RUL_MAX = 72
RUL_TRIGGER = 24
RUL_WARN = 48
WEIGHTS = {"temp": 0.35, "vib": 0.30, "pres": 0.20, "cur": 0.15}

CONTEXT = {
    "equipement": "Pompe P-17 — Unité B",
    "of_actif": "OF-2847",
    "duree_of_restante_h": 52,
    "equipe_dispo_dans_h": 48,
    "pieces_stock": ["Joint JM-220 (B-12)", "Roulement 6205-2RS"],
    "technicien_disponible": "Lionel"
}

# ── Initialisation du Session State (Indispensable pour bloquer les valeurs) ──
if 'temp' not in st.session_state: st.session_state.temp = 64.0
if 'vib' not in st.session_state: st.session_state.vib = 1.0
if 'pres' not in st.session_state: st.session_state.pres = 4.8
if 'cur' not in st.session_state: st.session_state.cur = 21.0
if 'tick' not in st.session_state: st.session_state.tick = 434
if 'running' not in st.session_state: st.session_state.running = True

# ── Entête Dynamique (Alignement Photo 2) ───────────────────────────────────
top_left, top_mid, top_right = st.columns([3, 1, 2])
with top_left:
    st.markdown("## 🟢 Pompe P-17 — Unité B")
with top_mid:
    st.write(f"<p style='text-align:right; font-family:monospace; font-size:20px; margin-top:10px;'>t = {st.session_state.tick}</p>", unsafe_allow_html=True)
with top_right:
    col_b1, col_b2 = st.columns(2)
    if col_b1.button("⏸️ En cours" if st.session_state.running else "▶️ Pause", use_container_width=True):
        st.session_state.running = not st.session_state.running
    if col_b2.button("🔄 Reset", use_container_width=True):
        st.session_state.temp, st.session_state.vib, st.session_state.pres, st.session_state.cur = 64.0, 1.0, 4.8, 21.0
        st.session_state.tick = 434
        st.rerun()

if st.session_state.running:
    st.session_state.tick += 1

# ── Section Scénarios Rapides (Placée en haut ou bas selon préférence, ici intégrée fluidement) ──
scenarios = {
    "Nominal":       (64.0, 1.0, 4.8, 21.0),
    "Surchauffe moteur": (112.0, 1.4, 5.0, 23.0),
    "Roulement dégradé": (78.0, 4.8, 4.9, 22.0),
    "Pression instable": (66.0, 1.8, 7.4, 21.5),
    "🔥 Défaillance critique P-17": (125.0, 6.2, 7.8, 31.5),
}

# --- Calcul des valeurs actuelles (Sliders vs Boutons) ---
# Si un bouton est pressé, il met à jour le session_state immédiatement
# ──────────────────────────────────────────────────────────────────────────────

# ── Section 1 : KPI Métriques du haut ─────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("TEMPÉRATURE", f"{st.session_state.temp:.0f} °C")
m2.metric("VIBRATION", f"{st.session_state.vib:.1f} mm/s")
m3.metric("PRESSION", f"{st.session_state.pres:.1f} bar")
m4.metric("COURANT", f"{st.session_state.cur:.1f} A")

# ── Calcul du RUL Dynamique ──────────────────────────────────────────────────
dt = max(0.0, min(1.0, (st.session_state.temp - 64.0) / (140.0 - 64.0)))
dv = max(0.0, min(1.0, (st.session_state.vib - 1.0) / (8.0 - 1.0)))
dp = max(0.0, min(1.0, (st.session_state.pres - 4.8) / (10.0 - 4.8)))
dc = max(0.0, min(1.0, (st.session_state.cur - 21.0) / (40.0 - 21.0)))
stress = (dt * WEIGHTS["temp"] + dv * WEIGHTS["vib"] + dp * WEIGHTS["pres"] + dc * WEIGHTS["cur"])
rul = max(0, round(RUL_MAX * (1 - stress ** 0.6)))

# ── Section 2 : Barre de Progression Linéaire RUL (Style Photo 2) ─────────────
st.markdown("---")
status_text = "Nominal" if rul > RUL_WARN else ("Alerte" if rul > RUL_TRIGGER else "Critique")
status_color = "#10b981" if rul > RUL_WARN else ("#f59e0b" if rul > RUL_TRIGGER else "#ef4444")

st.markdown(f"#### Durée de vie résiduelle (RUL) <span style='float:right; color:{status_color};'><b>{rul} h</b> <small style='color:gray;'>{status_text}</small></span>", unsafe_allow_html=True)
pct = (rul / RUL_MAX) * 100

st.markdown(f"""
    <div style="width:100%; background-color:#e2e8f0; height:14px; border-radius:7px; overflow:hidden;">
        <div style="width:{pct}%; background-color:{status_color}; height:100%; transition: width 0.3s;"></div>
    </div>
    <div style="display:flex; justify-content:space-between; font-size:12px; color:#64748b; margin-top:4px; margin-bottom:25px;">
        <span>0h</span><span style="color:#ef4444; font-weight:600;">Seuil agent : 24h</span><span style="color:#f59e0b; font-weight:600;">Alerte : 48h</span><span>72h (nominal)</span>
    </div>
""", unsafe_allow_html=True)

# ── Section 3 : Les 4 Graphiques Temporels Alternés ───────────────────────────
def make_micro_chart(title, current, nominal, color):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(20)), y=np.linspace(nominal, current, 20) + np.random.normal(0, 0.1, 20), mode='lines', line=dict(color=color, width=2)))
    fig.update_layout(
        title=f"<b>{title}</b> <span style='float:right;'>{current}</span>", height=140,
        margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor='white', paper_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#f1f5f9', showticklabels=False),
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9')
    )
    return fig

g1, g2 = st.columns(2)
with g1:
    st.plotly_chart(make_micro_chart("Température (°C)", st.session_state.temp, 64.0, "#ef4444"), use_container_width=True)
    st.plotly_chart(make_micro_chart("Pression (bar)", st.session_state.pres, 4.8, "#3b82f6"), use_container_width=True)
with g2:
    st.plotly_chart(make_micro_chart("Vibration (mm/s)", st.session_state.vib, 1.0, "#f59e0b"), use_container_width=True)
    st.plotly_chart(make_micro_chart("RUL (h)", rul, 72.0, "#10b981"), use_container_width=True)

# ── Section 4 : Injection Manuelle Via Sliders ────────────────────────────────
with st.container(border=True):
    st.markdown("⚙️ **Injection manuelle — forcer des valeurs**")
    sc1, sc2 = st.columns(2)
    with sc1:
        st.session_state.temp = sc1.slider("Température (seuil 110°C)", 50.0, 145.0, float(st.session_state.temp), 1.0)
        st.session_state.pres = sc1.slider("Pression (seuil 7 bar)", 2.0, 11.0, float(st.session_state.pres), 0.1)
    with sc2:
        st.session_state.vib = sc2.slider("Vibration (seuil 4.5 mm/s)", 0.5, 9.0, float(st.session_state.vib), 0.1)
        st.session_state.cur = sc2.slider("Courant (seuil 28A)", 10.0, 40.0, float(st.session_state.cur), 0.5)

# ── Section 5 : Boutons de Scénarios en bas de page ───────────────────────────
st.markdown("### Scénarios rapides")
b1, b2, b3, b4, b5 = st.columns(5)
if b1.button("Nominal", use_container_width=True):
    st.session_state.temp, st.session_state.vib, st.session_state.pres, st.session_state.cur = scenarios["Nominal"]; st.rerun()
if b2.button("Surchauffe moteur", use_container_width=True):
    st.session_state.temp, st.session_state.vib, st.session_state.pres, st.session_state.cur = scenarios["Surchauffe moteur"]; st.rerun()
if b3.button("Roulement dégradé", use_container_width=True):
    st.session_state.temp, st.session_state.vib, st.session_state.pres, st.session_state.cur = scenarios["Roulement dégradé"]; st.rerun()
if b4.button("Pression instable", use_container_width=True):
    st.session_state.temp, st.session_state.vib, st.session_state.pres, st.session_state.cur = scenarios["Pression instable"]; st.rerun()
if b5.button("🔥 Défaillance critique P-17", type="primary", use_container_width=True):
    st.session_state.temp, st.session_state.vib, st.session_state.pres, st.session_state.cur = scenarios["Critique P-17"]; st.rerun()

# ── Prescriptions de l'Agent Automatique ──────────────────────────────────────
if rul <= RUL_TRIGGER:
    st.markdown("---")
    st.error("### 🤖 Actions requises par l'Agent Prescriptif")
    st.info(f"💡 **Scénario optimal conseillé : Réduire la cadence de 20%**\n\nPermet d'aligner la fin de l'OF `{CONTEXT['of_actif']}` avec l'arrivée de l'équipe de maintenance de **{CONTEXT['technicien_disponible']}**.")
