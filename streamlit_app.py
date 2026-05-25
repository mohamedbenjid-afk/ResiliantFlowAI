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
    c_cur = max(0.0, st.session_state.base_cur + np.random.uniform(-0.2, 0.2))

    # Algorithme prescriptif évaluant le stress cumulé des composants
    stress = max(0, (c_temp-60)/50 * 0.4 + (c_vib/5) * 0.3 + (c_pres/8) * 0.3)
    c_rul = max(0, int(72 * (1 - stress**1.2)))

    # Sauvegarde dans l'historique glissant
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

# Calcul du statut textuel associé au RUL
r_status = "Nominal" if c_rul > 48 else ("Alerte" if c_rul > 24 else "Critique")
rul_percentage = float(max(0.0, min(1.0, c_rul / 72.0)))

# ── BARRE LATÉRALE DE NAVIGATION (MULTI-PROFILS) ────────────────────────────
st.sidebar.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=50)
st.sidebar.markdown("### ResilientFlow AI\n*Couche Prescriptive v1*")

profil = st.sidebar.selectbox(
    "👤 Sélectionner le profil utilisateur :",
    ["🔧 Lionel (Terrain)", "📋 Sophie (Manager)", "📊 Antoine (Directeur)", "🛡️ Leila (HSE)"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Contrôle du Flux Live**")
if st.sidebar.button("⏸️ Pause / ▶️ Reprendre", use_container_width=True):
    st.session_state.running = not st.session_state.running

st.sidebar.caption("Statut machine : Pompe P-17 (Unité B)")
st.sidebar.caption("Horodatage système : t = " + str(st.session_state.tick))
st.sidebar.caption("RUL estimé : " + str(c_rul) + " heures")

# ────────────────────────────────────────────────────────────────────────────
# 🔧 PROFIL 1 : LIONEL (TECHNICIEN TERRAIN)
# ────────────────────────────────────────────────────────────────────────────
if profil == "🔧 Lionel (Terrain)":
    st.markdown("### 🔧 Terminal Opérationnel de Terrain — Lionel")
    
    # Métriques des capteurs
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TEMPÉRATURE", "{:.1f} °C".format(c_temp))
    m2.metric("VIBRATION", "{:.1f} mm/s".format(c_vib))
    m3.metric("PRESSION", "{:.1f} bar".format(c_pres))
    m4.metric("COURANT", "{:.1f} A".format(c_cur))
    
    st.markdown("---")
    
    # Barre de progression de RUL
    col_l1, col_l2 = st.columns([3, 1])
    col_l1.markdown("**Durée de vie résiduelle (RUL) calculée**")
    col_l2.markdown("<p style='text-align: right; margin: 0;'><b>" + str(c_rul) + " h</b> (" + r_status + ")</p>", unsafe_allow_html=True)
    st.progress(rul_percentage)
    
    lbl1, lbl2, lbl3, lbl4 = st.columns([1, 1, 1, 1])
    lbl1.caption("0h (Panne)")
    lbl2.caption("⚠️ Seuil Agent : 24h")
    lbl3.caption("🔔 Alerte Seuil : 48h")
    lbl4.markdown("<p style='text-align: right; font-size: 0.8rem; color: gray; margin: 0;'>72h (Nominal)</p>", unsafe_allow_html=True)
    
    # Bloc Agent intelligent connecté à GitHub (US-K2)
    if c
