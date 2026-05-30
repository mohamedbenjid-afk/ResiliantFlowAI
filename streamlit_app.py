import streamlit as st
import numpy as np
import time

# Configuration de la page principale
st.set_page_config(page_title="ResilientFlow AI - Prescriptive Dashboard", layout="wide")

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
    .escp-banner {
        background-color: #002349;
        color: #ffffff;
        padding: 12px;
        border-radius: 4px;
        text-align: center;
        margin-top: 5px;
        margin-bottom: 15px;
        font-size: 0.85rem;
        border-left: 4px solid #d4af37;
    }
    </style>
""", unsafe_allow_html=True)

# ── INITIALISATION DU SESSION STATE (MOTEUR DE SIMULATION) ──────────────────
if 'history' not in st.session_state:
    st.session_state.history = {"time": list(range(30)), "temp": [67.0]*30, "vib": [0.8]*30, "pres": [4.4]*30, "rul": [72.0]*30}
if 'base_temp' not in st.session_state: st.session_state.base_temp = 67.0
if 'base_vib' not in st.session_state: st.session_state.base_vib = 0.8
if 'base_pres' not in st.session_state: st.session_state.base_pres = 4.4
if 'base_cur' not in st.session_state: st.session_state.base_cur = 20.7
if 'tick' not in st.session_state: st.session_state.tick = 757
if 'running' not in st.session_state: st.session_state.running = True

# ── MISE À JOUR DES CAPTEURS ET CALCUL DU RUL ───────────────────────────────
if st.session_state.running:
    st.session_state.tick += 1
    c_temp = st.session_state.base_temp + np.random.uniform(-0.5, 0.5)
    c_vib = max(0.1, st.session_state.base_vib + np.random.uniform(-0.05, 0.05))
    c_pres = max(0.1, st.session_state.base_pres + np.random.uniform(-0.05, 0.05))
    c_cur = max(0.0, st.session_state.base_cur + np.random.uniform(-0.2, 0.2))

    stress = max(0, (c_temp-60)/50 * 0.4 + (c_vib/5) * 0.3 + (c_pres/8) * 0.3)
    c_rul = max(0, int(72 * (1 - stress**1.2)))

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

# Stockage temporaire pour les autres pages
st.session_state.c_temp = c_temp
st.session_state.c_vib = c_vib
st.session_state.c_pres = c_pres
st.session_state.c_cur = c_cur
st.session_state.c_rul = c_rul

# Barre latérale commune pour le contrôle
st.sidebar.markdown("""
    <div class="escp-banner">
        🎓 <b>Projet de Fin d'Études ESCP</b><br>
        ⚙️ Sujet : <i>Maintenance Prescriptive & Industrie 4.0</i>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### ResilientFlow AI\n*Couche Prescriptive v1*")
if st.sidebar.button("⏸️ Pause / ▶️ Reprendre", use_container_width=True):
    st.session_state.running = not st.session_state.running

st.sidebar.caption(f"Statut machine : Pompe P-17 | RUL : {c_rul}h")

# Contenu de l'accueil
st.title("🚀 Bienvenue sur la plateforme ResilientFlow AI")
st.markdown("---")
st.markdown("### 🛠️ Mode d'emploi pour l'équipe de développement :")
st.info("""
1. **Ne touchez plus à ce fichier principal** (`streamlit_app.py`).
2. Allez dans le dossier `pages/` sur GitHub pour modifier uniquement votre interface.
3. Utilisez le menu de gauche pour naviguer d'une page à l'autre et tester vos changements.
""")

# Auto-refresh de l'accueil
if st.session_state.running:
    time.sleep(1)
    st.rerun()
