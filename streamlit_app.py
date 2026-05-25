import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time
import requests

# 1. Configuration de la page principale
st.set_page_config(page_title="ResilientFlow AI - Prescriptive Dashboard", layout="wide")

# ── CONFIGURATION DU RÉPERTOIRE GITHUB ──────────────────────────────────────
# Modifiez ces variables avec vos propres informations de dépôt si nécessaire
GITHUB_USER = "VOTRE_NOM_UTILISATEUR_GITHUB"
GITHUB_REPO = "maintenance-knowledge-base"
GITHUB_BRANCH = "main"

def get_github_file(path, is_json=False):
    url = "https://raw.githubusercontent.com/" + GITHUB_USER + "/" + GITHUB_REPO + "/" + GITHUB_BRANCH + "/" + path
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json() if is_json else response.text
        else:
            return None
    except Exception:
        return None

# ── STYLE CSS GLOBAL & SÉCURISÉ ─────────────────────────────────────────────
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
    .doc-box {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        padding: 15px;
        border-radius: 5px;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ── DONNÉES DE CONTEXTE SIMULÉES (US-02 du Backlog) ─────────────────────────
CONTEXTE_USINE = {
    "production": {
        "ordre_fabrication_actif": "OF-2026-89A",
        "ligne_concerne": "Ligne 2",
        "cout_arret_heure": 6500
    },
    "equipe": {
        "technicien_recommande": "Lionel (Habilité Mécanique/Hydraulique - Charge : 32h/40h)",
        "technicien_secondaire": "Marc D. (Habilité Électricité - Surcharge : 39h/40h)"
    },
    "stocks": {
        "pieces_disponibles": "Joints d'étanchéité P17 (En stock : 2) | Roulements (Stock : 0 - Commande en cours)"
    }
}

# ── INITIALISATION DU SESSION STATE (MOTEUR DE SIMULATION) ──────────────────
if 'history' not in st.session_state:
    st.session_state.history = {"time": list(range(30)), "temp": [67.0]*30, "vib": [0.8]*30, "pres": [4.4]*30, "rul": [72.0]*30}
if 'base_temp' not in st.session_state: st.session_state.base_temp = 67.0
if 'base_vib' not in st.session_state: st.session_state.base_vib = 0.8
if 'base_pres' not in st.session_state: st.session_state.base_pres = 4.4
if 'base_cur' not in st.session_state: st.session_state.base_cur = 20.7
if 'tick' not in st.session_state: st.session_state.tick = 757
if 'running' not in st.session_state: st.session_state.running = True

# ── MISE À JOUR DES CAPTEURS ET CALCUL DU RUL (MOTEUR US-03) ────────────────
if st.session_state.running:
    st.session_state.tick += 1
    c_temp = st.session_state.base_temp + np.random.uniform(-0.5, 0.5)
    c_vib = max(0.1, st.session_state.base_vib + np.random.uniform(-0.05, 0.05))
    c_pres = max(0.1, st.session_state.base_pres + np.random.uniform(-0.05, 0.05))
    c_cur = max(0.0, st.session_state.base
