import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time

# 1. Configuration de la page
st.set_page_config(page_title="Dashboard Pompe P-17", layout="wide")

# ── Style CSS pour coller à l'image ──────────────────────────────────────────
st.markdown("""
    <style>
    /* Global Background */
    .stApp { background-color: #ffffff; }
    
    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: #fcfcfc !important;
        border: 1px solid #eeeeee !important;
        padding: 10px 20px !important;
        border-radius: 5px !important;
    }
    
    /* Slider Threshold Labels */
    .threshold-label { color: #ef4444; font-size: 0.8rem; font-weight: bold; }
    
    /* Agent Box at bottom */
    .agent-status-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 15px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
 # ── RUL Bar Section ─────────────────────────────────────────────────────────
st.markdown("---")
r_color = "#10b981" if c_rul > 48 else ("#f59e0b" if c_rul > 24 else "#ef4444")
r_status = "Nominal" if c_rul > 48 else ("Alerte" if c_rul > 24 else "Critique")

# On calcule le pourcentage en amont
rul_percentage = int((c_rul / 72) * 100)

# Doublement des accolades {{ }} pour le CSS natif afin de bloquer l'interprétation Python
st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: baseline;">
        <span style="font-weight: bold; font-size: 1.2rem;">Durée de vie résiduelle (RUL)</span>
        <span><b style="font-size: 1.5rem;">{c_rul} h</b> <span style="color:{r_color}; font-weight:bold;">{r_status}</span></span>
    </div>
    <div class="rul-container">
        <div class="rul-marker" style="left: 0%%;">0h</div>
        <div class="rul-marker" style="left: 33.3%%; color:#ef4444;">Seuil agent : 24h</div>
        <div class="rul-marker" style="left: 66.6%%; color:#f59e0b;">Alerte : 48h</div>
        <div class="rul-marker" style="right: 0%%; color:#10b981;">72h</div>
        <div class="rul-bar" style="width: {rul_percentage}%%; background-color: {r_color};"></div>
    </div>
""", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

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
h1, h2, h3 = st.columns([3, 1, 1.5])
with h1: st.markdown("### Pompe P-17 — Unité B")
with h2: st.markdown(f"<p style='color:gray; padding-top:10px;'>t = {st.session_state.tick}</p>", unsafe_allow_html=True)
with h3: 
    if st.button("⏸️ Pause" if st.session_state.running else "▶️ En cours", use_container_width=True):
        st.session_state.running = not st.session_state.running

# ── Data Update ─────────────────────────────────────────────────────────────
if st.session_state.running:
    st.session_state.tick += 1
    # On utilise les valeurs de base (modifiables par les sliders)
    c_temp = st.session_state.base_temp + np.random.uniform(-0.5, 0.5)
    c_vib = max(0.1, st.session_state.base_vib + np.random.uniform(-0.05, 0.05))
    c_pres = max(0.1, st.session_state.base_pres + np.random.uniform(-0.05, 0.05))
    c_cur = max(0.0, st.session_state.base_cur + np.random.uniform(-0.2, 0.2))

    # Calcul RUL (Logique simplifiée basée sur les seuils de l'image)
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
    c_temp, c_vib, c_pres, c_cur, c_rul = st.session_state.history["temp"][-1], st.session_state.history["vib"][-1], st.session_state.history["pres"][-1], st.session_state.base_cur, st.session_state.history["rul"][-1]

# ── Top Metrics ─────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("TEMPÉRATURE", f"{c_temp:.1f} °C")
m2.metric("VIBRATION", f"{c_vib:.1f} mm/s")
m3.metric("PRESSION", f"{c_pres:.1f} bar")
m4.metric("COURANT", f"{c_cur:.1f} A")
