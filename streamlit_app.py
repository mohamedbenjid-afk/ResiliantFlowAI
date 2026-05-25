import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time

# 1. Configuration de la page
st.set_page_config(page_title="Pompe P-17 — Unité B", layout="wide")

# Injection CSS pour les cartes de métriques blanches
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

# ── Constantes Échelle Long Terme (En Heures) ────────────────────────────────
RUL_MAX = 2160         # 2160 heures = 90 jours (3 mois)
RUL_TRIGGER = 24       # Seuil critique de l'agent = 24 heures (1 jour)
RUL_WARN = 720         # Seuil alerte = 720 heures (1 mois)
WEIGHTS = {"temp": 0.35, "vib": 0.30, "pres": 0.20, "cur": 0.15}

# ── Initialisation des Historiques (Session State) ───────────────────────────
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

# ── Entête avec bouton Pause/Play ────────────────────────────────────────────
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

# ── Évolution des données en temps réel (Lignes condensées pour éviter les SyntaxError) ──
if st.session_state.running:
    st.session_state.tick += 1
    
    current_temp = st.session_state.base_temp + np.random.uniform(-0.8
