import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time

# Configuration de la page
st.set_page_config(
    page_title="ResilientFlow AI - Dashboard de Maintenance Prédictive",
    page_icon="🏭",
    layout="wide"
)

# Style CSS personnalisé pour donner un look moderne et industriel (comme la photo 2)
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    .prescription-box {
        background-color: #f0fdf4;
        border-left: 5px solid #16a34a;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .prescription-box.optimal {
        background-color: #eff6ff;
        border-left: 5px solid #2563eb;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏭 ResilientFlow AI — Simulateur C-MAPSS")
st.subheader("Suivi des indicateurs de dégradation et agent prescriptif en temps réel")

# Initialisation du Session State pour stocker les valeurs des capteurs
if 'temp' not in st.session_state:
    st.session_state.temp = 110.0
    st.session_state.vib = 1.2
    st.session_state.pres = 4.8
    st.session_state.courant = 18.2

# --- BARRE LATÉRALE DE CONTRÔLE & SIMULATION ---
st.sidebar.header("🕹️ Contrôle de la Simulation")

# Bouton de défaillance critique immédiate
if st.sidebar.button("🚨 Défaillance critique P-17", type="primary"):
    st.session_state.temp = 125.0
    st.session_state.vib = 6.2
    st.session_state.pres = 7.8
    st.session_state.courant = 31.5

st.sidebar.markdown("---")
st.sidebar.markdown("**Ajustement manuel des capteurs :**")
# Sliders pour ajuster manuellement en plus du mode automatique
t_slider = st.sidebar.slider("Température (°C)", 90.0, 140.0, float(st.session_state.temp), 0.5)
v_slider = st.sidebar.slider("Vibrations (mm/s)", 0.5, 8.0, float(st.session_state.vib), 0.1)
p_slider = st.sidebar.slider("Pression (bar)", 2.0, 10.0, float(st.session_state.pres), 0.1)
c_slider = st.sidebar.slider("Courant (A)", 10.0, 40.0, float(st.session_state.courant), 0.5)

# Prise en compte des valeurs ajustées
st.session_state.temp = t_slider
st.session_state.vib = v_slider
st.session_state.pres = p_slider
st.session_state.courant = c_slider

# --- LOGIQUE DU CALCUL DU RUL (Modèle non-linéaire) ---
# 1. Calcul des scores de dégradation normalisés (0 = nominal, 1 = critique)
def get_stress_score(val, nominal, critical):
    score = (val - nominal) / (critical - nominal)
    return max(0.0, min(float(score), 1.0)) # Reste coincé entre 0 et 1

s_temp = get_stress_score(st.session_state.temp, 110.0, 125.0)
s_vib = get_stress_score(st.session_state.vib, 1.2, 4.5)
s_pres = get_stress_score(st.session_state.pres, 4.8, 7.0)
s_cour = get_stress_score(st.session_state.courant, 18.2, 28.0)

# 2. Combinaison pondérée du stress
stress_total = (s_temp * 0.35) + (s_vib * 0.30) + (s_pres * 0.20) + (s_cour * 0.15)

# 3. Formule mathématique du RUL (Exposant 0.6 pour l'accélération de l'usure)
rul = 72.0 * (1.0 - (stress_total ** 0.6))
rul = max(0.0, rul) # Pas de RUL négatif

# --- AFFICHAGE PRINCIPAL (DASHBOARD) ---

# Section 1 : Les Cartes de Métriques (Capteurs)
col1, col2, col3, col4 = st.columns(4)

with col1:
    color = "normal" if st.session_state.temp < 120 else "inverse"
    st.metric("🌡️ Température", f"{st.session_state.temp:.1f} °C", delta=f"{st.session_state.temp - 110.0:.1f} °C vs nominal", delta_color=color)
with col2:
    color = "normal" if st.session_state.vib < 4.0 else "inverse"
    st.metric("🫨 Vibrations", f"{st.session_state.vib:.2f} mm/s", delta=f"{st.session_state.vib - 1.2:.2f} mm/s vs nominal", delta_color=color)
with col3:
    color = "normal" if st.session_state.pres < 6.5 else "inverse"
    st.metric("💧 Pression", f"{st.session_state.pres:.1f} bar", delta=f"{st.session_state.pres - 4.8:.1f} bar vs nominal", delta_color=color)
with col4:
    color = "normal" if st.session_state.courant < 25.0 else "inverse"
    st.metric("⚡ Courant", f"{st.session_state.courant:.1f} A", delta=f"{st.session_state.courant - 18.2:.1f} A vs nominal", delta_color=color)

st.markdown("---")

# Section 2 : Jauge du RUL et Graphique de Dégradation
left_col, right_col = st.columns([1, 2])

with left_col:
    st.subheader("⏱️ Durée de vie restante")
    
    # Couleur de la jauge selon l'urgence
    gauge_color = "#ef4444" if
