import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time

# 1. Configuration de la page
st.set_page_config(page_title="Pompe P-17 — Unité B", layout="wide")

# Injection CSS pour obtenir des cartes de métriques blanches et épurées
st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        padding: 15px 20px !important;
        border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ── Constantes Échelle Long Terme ────────────────────────────────────────────
RUL_MAX = 2160         # 2160 heures = 3 mois
RUL_TRIGGER = 24       # Seuil critique = 1 jour
RUL_WARN = 720         # Seuil alerte = 1 mois
WEIGHTS = {"temp": 0.35, "vib": 0.30, "pres": 0.20, "cur": 0.15}

# ── Initialisation des Historiques dans le Session State ─────────────────────
if 'history' not in st.session_state:
    st.session_state.history = {
        "time": list(range(30)),
        "temp": [64.0] * 30,
        "vib": [1.0] * 30,
        "pres": [4.8] * 30,
        "rul": [RUL_MAX] * 30
    }
if 'base_temp' not in st.session_state: st.session_state.base_temp = 64.0
if 'base_vib' not in st.session_state: st.session_state.base_vib = 1.0
if 'base_pres' not in st.session_state: st.session_state.base_pres = 4.8
if 'base_cur' not in st.session_state: st.session_state.base_cur = 21.0
if 'tick' not in st.session_state: st.session_state.tick = 434
if 'running' not in st.session_state: st.session_state.running = True

# ── Entête du Dashboard ──────────────────────────────────────────────────────
top_left, top_mid, top_right = st.columns([3, 1, 2])
with top_left:
    st.markdown("## 🟢 Pompe P-17 — Unité B")
with top_mid:
    st.write(f"<p style='text-align:right; font-family:monospace; font-size:20px; margin-top:10px;'>t = {st.session_state.tick}</p>", unsafe_allow_html=True)
with top_right:
    col_b1, col_b2 = st.columns(2)
    if col_b1.button("⏸️ Pause" if st.session_state.running else "▶️ En cours", use_container_width=True):
        st.session_state.running = not st.session_state.running
    if col_b2.button("🔄 Reset", use_container_width=True):
        st.session_state.history = {"time": list(range(30)), "temp": [64.0]*30, "vib": [1.0]*30, "pres": [4.8]*30, "rul": [RUL_MAX]*30}
        st.session_state.base_temp, st.session_state.base_vib, st.session_state.base_pres, st.session_state.base_cur = 64.0, 1.0, 4.8, 21.0
        st.session_state.tick = 434
        st.rerun()

# ── Évolution des données en temps réel ──────────────────────────────────────
if st.session_state.running:
    st.session_state.tick += 1
    
    current_temp = float(st.session_state.base_temp + np.random.uniform(-0.8, 0.8))
    current_vib = float(max(0.1, st.session_state.base_vib + np.random.uniform(-0.15, 0.15)))
    current_pres = float(max(0.5, st.session_state.base_pres + np.random.uniform(-0.1, 0.1)))
    current_cur = float(max(0.0, st.session_state.base_cur + np.random.uniform(-0.3, 0.3)))
    
    dt = max(0.0, min(1.0, (current_temp - 64.0) / (125.0 - 64.0)))
    dv = max(0.0, min(1.0, (current_vib - 1.0) / (6.2 - 1.0)))
    dp = max(0.0, min(1.0, (current_pres - 4.8) / (7.8 - 4.8)))
    dc = max(0.0, min(1.0, (current_cur - 21.0) / (31.5 - 21.0)))
    stress = float(dt * WEIGHTS["temp"] + dv * WEIGHTS["vib"] + dp * WEIGHTS["pres"] + dc * WEIGHTS["cur"])
    
    if stress >= 0.92:
        current_rul = int(np.random.uniform(12, 20))
    else:
        current_rul = max(740, int(RUL_MAX * (1.0 - (stress ** 2) * 0.6)))

    st.session_state.history["time"].append(st.session_state.tick)
    st.session_state.history["temp"].append(current_temp)
    st.session_state.history["vib"].append(current_vib)
    st.session_state.history["pres"].append(current_pres)
    st.session_state.history["rul"].append(current_rul)
    
    for k in st.session_state.history:
        if len(st.session_state.history[k]) > 30: st.session_state.history[k].pop(0)
else:
    current_temp = st.session_state.history["temp"][-1]
    current_vib = st.session_state.history["vib"][-1]
    current_pres = st.session_state.history["pres"][-1]
    current_cur = st.session_state.base_cur
    current_rul = st.session_state.history["rul"][-1]

# ── Section 1 : Métriques numériques du haut ─────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("TEMPÉRATURE", f"{current_temp:.1f} °C")
m2.metric("VIBRATION", f"{current_vib:.2f} mm/s")
m3.metric("PRESSION", f"{current_pres:.2f} bar")
m4.metric("COURANT", f"{current_cur:.1f} A")

# ── Section 2 : Barre de Progression du RUL ──────────────────────────────────
st.markdown("---")
jours_restants = current_rul / 24.0

if current_rul <= RUL_TRIGGER:
    status_text = "Critique (Moins d'un jour restant !)"
    status_color = "#ef4444"
    display_rul = f"{current_rul} h"
elif current_rul <= RUL_WARN:
    status_text = "Alerte (Maintenance sous 1 mois)"
    status_color = "#f59e0b"
    display_rul = f"{jours_restants:.1f} jours"
else:
    status_text = "Nominal"
    status_color = "#10b981"
    display_rul = f"{jours_restants/30:.1f} mois"

st.markdown(f"#### Durée de vie résiduelle (RUL) <span
