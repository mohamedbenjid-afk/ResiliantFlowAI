import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time

# 1. Configuration de la page
st.set_page_config(page_title="Dashboard Pompe P-17", layout="wide")

# ── Style CSS épuré et ajustements de compacité ──────────────────────────────
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    div[data-testid="stMetric"] {
        background-color: #fcfcfc !important;
        border: 1px solid #eeeeee !important;
        padding: 8px 15px !important;
        border-radius: 5px !important;
    }
    .threshold-label { color: #ef4444; font-size: 0.75rem; font-weight: bold; display: block; margin-top: -10px; margin-bottom: 5px; }
    div.stButton > button { margin-bottom: 5px !important; }
    </style>
""", unsafe_allow_html=True)

# ── Base de Connaissances ──────────────────────────────────────────────────
KNOWLEDGE_BASE = {
    "failures": {
        "temp": {"label": "Surchauffe Moteur", "threshold": 110, "task": "PM-ELEC-04: Vérifier circuit de refroidissement."},
        "vib": {"label": "Défaut Roulement", "threshold": 4.5, "task": "PM-MECH-12: Analyse vibratoire et graissage."},
        "pres": {"label": "Cavitation", "threshold": 7.0, "task": "PM-HYD-08: Purge et vérification des vannes."},
        "cur": {"label": "Surcharge Électrique", "threshold": 28, "task": "PM-ELEC-01: Contrôle intensité et isolement."}
    }
}

# ── Initialisation Session State ───────────────────────────────────────────
if 'history' not in st.session_state:
    st.session_state.history = {"time": list(range(30)), "temp": [67.0]*30, "vib": [0.8]*30, "pres": [4.4]*30, "rul": [72.0]*30}
if 'base_temp' not in st.session_state: st.session_state.base_temp = 67.0
if 'base_vib' not in st.session_state: st.session_state.base_vib = 0.8
if 'base_pres' not in st.session_state: st.session_state.base_pres = 4.4
if 'base_cur' not in st.session_state: st.session_state.base_cur = 20.7
if 'tick' not in st.session_state: st.session_state.tick = 757
if 'running' not in st.session_state: st.session_state.running = True

# ── Header ──────────────────────────────────────────────────────────────────
h1, h2, h3 = st.columns([3, 1, 1])
with h1: st.markdown("### Pompe P-17 — Unité B")
with h2: st.markdown(f"<p style='color:gray; padding-top:10px; font-family:monospace;'>t = {st.session_state.tick}</p>", unsafe_allow_html=True)
with h3: 
    if st.button("⏸️ Pause" if st.session_state.running else "▶️ En cours", use_container_width=True):
        st.session_state.running = not st.session_state.running

# ── Data Update ─────────────────────────────────────────────────────────────
if st.session_state.running:
    st.session_state.tick += 1
    c_temp = st.session_state.base_temp + np.random.uniform(-0.5, 0.5)
    c_vib = max(0.1, st.session_state.base_vib + np.random.uniform(-0.05, 0.05))
    c_pres = max(0.1, st.session_state.base_pres + np.random.uniform(-0.05, 0.05))
    c_cur = max(0.0, st.session_state.base_cur + np.random.uniform(-0.2, 0.2))

    # Calcul RUL
    stress = max(0, (c_temp-60)/50 * 0.4 + (c_vib/5) * 0.3 + (c_pres/8) * 0.3)
    c_rul = max(0, int(72 * (1 - stress**1.2)))

    # Update History
    st.session_state.history["temp"].append(c_temp)
    st.session_state.history["vib"].append(c_vib)
    st.session_state.history["pres"].append(c_pres)
    st.session_state.history["rul"].append(c_rul)
    st.session_state.history["time"].append(st.session_state.tick)
    for k in st.session_state.history:
        if len(st.session_state.history[k]) > 30: st.session_state.history[k].pop(0)
else:
    c_temp = st.session_state.history["temp"][-1]
    c_vib = st.session_state.history["vib"][-1]
    c_pres = st.session_state.history["pres"][-1]
    c_cur = st.session_state.base_cur
    c_rul = st.session_state.history["rul"][-1]

# ── Top Metrics ─────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("TEMPÉRATURE", f"{c_temp:.1f} °C")
m2.metric("VIBRATION", f"{c_vib:.1f} mm/s")
m3.metric("PRESSION", f"{c_pres:.1f} bar")
m4.metric("COURANT", f"{c_cur:.1f} A")

# ── RUL Bar Section ─────────────────────────────────────────────────────────
st.markdown("---")
r_status = "Nominal" if c_rul > 48 else ("Alerte" if c_rul > 24 else "Critique")

col_left, col_right = st.columns([2, 1])
with col_left:
    st.markdown("**Durée de vie résiduelle (RUL)**")
with col_right:
    st.markdown(f"<p style='text-align: right; margin: 0;'><b>{c_rul} h</b> ({r_status})</p>", unsafe_allow_html=True)

rul_percentage = float(max(0.0, min(1.0, c_rul / 72.0)))
st.progress(rul_percentage)

lbl1, lbl2, lbl3, lbl4 = st.columns([1, 1, 1, 1])
lbl1.caption("0h")
lbl2.caption("⚠️ Seuil agent : 24h")
lbl3.caption("🔔 Alerte : 48h")
lbl4.markdown("<p style='text-align: right; font-size: 0.8rem; color: gray; margin: 0;'>72h</p>", unsafe_allow_html=True)

# ── NOTIFICATION AGENT (Placée en haut, ultra-visible) ──────────────────────
if c_rul <= 24:
    st.error("🚨 **ALERTE RESILIENTFLOW AI : DÉFAILLANCE CRITIQUE EN COURS**")
    diag = []
    if c_temp >= 110: diag.append(KNOWLEDGE_BASE["failures"]["temp"]["task"])
    if c_vib >= 4.5: diag.append(KNOWLEDGE_BASE["failures"]["vib"]["task"])
    if c_pres >= 7.0: diag.append(KNOWLEDGE_BASE["failures"]["pres"]["task"])
    
    if diag:
        for d in diag: st.markdown(f"👉 **Plan requis :** {d}")
    else:
        st.markdown("👉 **Plan requis :** Usure combinée complexe. Inspection générale immédiate.")
else:
    st.success("🤖 **Agent ResilientFlow AI** : Surveillance active — Système nominal.")

st.markdown("---")

# ── Architecture en 3 Colonnes (Évite d'avoir à scroller) ───────────────────
main_col_charts, main_col_sliders, main_col_scenarios = st.columns([2, 1, 1])

# --- COLONNE 1 : Les Graphiques (Condensés) ---
with main_col_charts:
    st.markdown("##### 📈 Courbes de tendance")
    def plot_small(title, data, color, unit):
        fig = go.Figure(go.Scatter(x=st.session_state.history["time"], y=data, mode='lines', line=dict(color=color, width=2.5)))
        fig.update_layout(title=f"<b>{title}</b> ({data[-1]:.1f} {unit})", height=110, margin=dict(l=0,r=0,t=25,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, showticklabels=False), yaxis=dict(showgrid=True, gridcolor='#f1f1f1'))
        return fig

    st.plotly_chart(plot_small("Température", st.session_state.history["temp"], "#ef4444", "°C"), use_container_width=True)
    st.plotly_chart(plot_small("Vibration", st.session_state.history["vib"], "#f59e0b", "mm/s"), use_container_width=True)
    st.plotly_chart(plot_small("Pression", st.session_state.history["pres"], "#3b82f6", "bar"), use_container_width=True)

# --- COLONNE 2 : Injection Manuelle (Alignement Vertical) ---
with main_col_sliders:
    st.markdown("##### ⌨️ Injection manuelle")
    st.session_state.base_temp = st.slider("Température (°C)", 60, 140, int(st.session_state.base_temp), label_visibility="collapsed")
    st.markdown("<span class='threshold-label'>Seuil : 110°C</span>", unsafe_allow_html=True)
    
    st.session_state.base_vib = st.slider("Vibration (mm/s)", 0.0, 8.0, float(st.session_state.base_vib), label_visibility="collapsed")
    st.markdown("<span class='threshold-label'>Seuil : 4.5 mm/s</span>", unsafe_allow_html=True)
    
    st.session_state.base_pres = st.slider("Pression (bar)", 0.0, 10.0, float(st.session_state.base_pres), label_visibility="collapsed")
    st.markdown("<span class='threshold-label'>Seuil : 7.0 bar</span>", unsafe_allow_html=True)

# --- COLONNE 3 : Scénarios Rapides (Empilés Verticalement) ---
with main_col_scenarios:
    st.markdown("##### 🎭 Scénarios")
    if st.button("✅ Mode Nominal", use_container_width=True): 
        st.session_state.base_temp, st.session_state.base_vib, st.session_state.base_pres, st.session_state.base_cur = 67.0, 0.8, 4.4, 21
    if st.button("🔥 Surchauffe Moteur", use_container_width=True): 
        st.session_state.base_temp, st.session_state.base_vib, st.session_state.base_pres, st.session_state.base_cur = 115.0, 1.2, 4.5, 22
    if st.button("⚙️ Roulement Dégradé", use_container_width=True): 
        st.session_state.base_temp, st.session_state.base_vib, st.session_state.base_pres, st.session_state.base_cur = 75.0, 5.2, 4.4, 21
    if st.button("💧 Pression Instable", use_container_width=True): 
        st.session_state.base_temp, st.session_state.base_vib, st.session_state.base_pres, st.session_state.base_cur = 68.0, 1.0, 7.8, 21
    if st.button("⚠️ Défaillance P-17", type="primary", use_container_width=True): 
        st.session_state.base_temp, st.session_state.base_vib, st.session_state.base_pres, st.session_state.base_cur = 125.0, 6.5, 8.5, 32

# Auto-refresh
if st.session_state.running:
    time.sleep(1)
    st.rerun()
