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
    .stButton>button { border-radius: 6px !important; }
    </style>
""", unsafe_allow_html=True)

# ── Constantes Échelle Long Terme (En Heures) ────────────────────────────────
RUL_MAX = 2160         # 2160 heures = 90 jours (3 mois)
RUL_TRIGGER = 24       # Seuil critique de l'agent = 24 heures (1 jour)
RUL_WARN = 720         # Seuil alerte = 720 heures (1 mois)
WEIGHTS = {"temp": 0.35, "vib": 0.30, "pres": 0.20, "cur": 0.15}

# Contexte pour l'affichage de l'agent prescriptif
CONTEXT = {
    "of_actif": "OF-2847",
    "technicien_disponible": "Lionel"
}

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

# ── Entête du Dashboard (Alignement horizontal parfait) ─────────────────────
top_left, top_mid, top_right = st.columns([3, 1, 2])
with top_left:
    st.markdown("## 🟢 Pompe P-17 — Unité B")
with top_mid:
    st.write(f"<p style='text-align:right; font-family:monospace; font-size:20px; margin-top:10px;'>t = {st.session_state.tick}</p>", unsafe_allow_html=True)
with top_right:
    col_b1, col_b2 = st.columns(2)
    if col_b1.button("⏸️ Pause" if st.session_state.running else "▶️ En cours", use_container_width=True):
        st.session_state.running = not st.session_
