import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd

# 1. Configuration de la page
st.set_page_config(
    page_title="Pompe P-17 — Unité B",
    page_icon="🟢",
    layout="wide"
)

# Style CSS pour calquer le design épuré, les cartes blanches et les espacements
st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 15px 20px;
        border-radius: 8px;
    }
    .stButton>button {
        border-radius: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Gestion de l'état (Session State) pour l'historique et les compteurs
if 'tick' not in st.session_state:
    st.session_state.tick = 434
if 'running' not in st.session_state:
    st.session_state.running = True

# Initialisation des valeurs de base des capteurs
defaults = {"temp": 64.0, "vib": 1.0, "pres": 4.8, "courant": 21.0}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- ENTÊTE DE L'APPLICATION ---
top_col1, top_col2, top_col3 = st.columns([3, 1, 1])
with top_col1:
    st.title("🟢 Pompe P-17 — Unité B")
with top_col2:
    st.write(f"<p style='text-align:right; font-family:monospace; font-size:18px; margin-top:15px;'>t = {st.session_state.tick}</p>", unsafe_allow_html=True)
with top_col3:
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("⏸️ En cours" if st.session_state.running else "▶️ Pause", use_container_width=True):
            st.session_state.running = not st.session_state.running
    with btn_col2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.tick = 434
            for key, val in defaults.items():
                st.session_state[key] = val
            st.rerun()

# Avancement du temps simulé si l'app tourne
if st.session_state.running:
    st.session_state.tick += 1

# --- SECTION 1 : LES GRANDES METRIQUES TOP ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("TEMPÉRATURE", f"{st.session_state.temp:.0f} °C")
m2.metric("VIBRATION", f"{st.session_state.vib:.1f} mm/s")
m3.metric("PRESSION", f"{st.session_state.pres:.1f} bar")
m4.metric("COURANT", f"{st.session_state.courant:.1f} A")

st.markdown("---")

# --- CALCUL DU RUL (LOGIQUE CMAPSS) ---
def get_stress(val, nominal, critical):
    if val <= nominal:
        return 0.0
    score = (val - nominal) / (critical - nominal)
    return min(float(score), 1.0)

s_t = get_stress(st
