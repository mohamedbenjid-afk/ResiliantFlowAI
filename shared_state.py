# shared_state.py
# Module partagé : initialisation du session state, mise à jour capteurs, config GitHub
import streamlit as st
import numpy as np
import requests
import os

# ── SECRETS : lus depuis Streamlit Cloud ou variables d'environnement ─────────
# Ne jamais écrire les tokens directement dans le code !
def get_secret(key: str) -> str:
    """Lit un secret depuis st.secrets (Streamlit Cloud) ou os.environ (local)."""
    try:
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, "")

# ── CONFIGURATION GITHUB ─────────────────────────────────────────────────────
GITHUB_USER   = "VOTRE_NOM_UTILISATEUR_GITHUB"
GITHUB_REPO   = "maintenance-knowledge-base"
GITHUB_BRANCH = "main"


def get_github_file(path, is_json=False):
    url = (
        "https://raw.githubusercontent.com/"
        + GITHUB_USER + "/" + GITHUB_REPO + "/" + GITHUB_BRANCH + "/" + path
    )
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json() if is_json else response.text
        return None
    except Exception:
        return None


# ── DONNÉES DE CONTEXTE USINE ─────────────────────────────────────────────────
CONTEXTE_USINE = {
    "production": {
        "ordre_fabrication_actif": "OF-2026-89A",
        "ligne_concerne":          "Ligne 2",
        "cout_arret_heure":        6500,
    },
    "equipe": {
        "technicien_recommande":  "Lionel (Habilité Mécanique/Hydraulique - Charge : 32h/40h)",
        "technicien_secondaire":  "Marc D. (Habilité Électricité - Surcharge : 39h/40h)",
    },
    "stocks": {
        "pieces_disponibles": (
            "Joints d'étanchéité P17 (En stock : 2) | "
            "Roulements (Stock : 0 - Commande en cours)"
        ),
    },
}


# ── PALETTE COULEURS (light theme uniquement) ─────────────────────────────────
# Primaire  : #1a3a5c  (bleu marine profond)
# Accent    : #2563eb  (bleu électrique — boutons, liens)
# Fond page : #f4f7fb
# Fond carte: #ffffff
# Bordure   : #dde3ee
# Texte     : #1e293b  (principal)  /  #64748b (secondaire)
# Succès    : #15803d / bg #f0fdf4
# Alerte    : #d97706 / bg #fffbeb
# Danger    : #dc2626 / bg #fef2f2
# ESCP gold : #c9a227

COMMON_CSS = """
<style>
/* ── Fond général ── */
.stApp { background-color: #f4f7fb; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background-color: #1a3a5c !important;
}
section[data-testid="stSidebar"] * {
    color: #e8eef6 !important;
}
section[data-testid="stSidebar"] .stButton button {
    background-color: #2563eb !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background-color: #1d4ed8 !important;
}

/* ── Métriques ── */
div[data-testid="stMetric"] {
    background-color: #ffffff !important;
    border: 1px solid #dde3ee !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
}
div[data-testid="stMetricValue"] { color: #1a3a5c !important; font-weight: 700 !important; }
div[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.78rem !important; }

/* ── Bannière ESCP ── */
.escp-banner {
    background-color: #1a3a5c; color: #ffffff;
    padding: 10px 14px; border-radius: 6px; text-align: center;
    margin-bottom: 14px; font-size: 0.82rem; line-height: 1.5;
    border-left: 4px solid #c9a227;
}

/* ── Boîte doc / prescriptions ── */
.doc-box {
    background-color: #f0fdf4; border: 1px solid #86efac;
    padding: 15px; border-radius: 6px;
    margin-top: 10px; margin-bottom: 10px;
    color: #14532d;
}

/* ── Seuil rouge sliders ── */
.threshold-label {
    color: #dc2626; font-size: 0.73rem; font-weight: 600;
    display: block; margin-top: -8px; margin-bottom: 6px;
}

/* ── Cartes info ── */
div[data-testid="stInfo"]    { border-radius: 6px !important; }
div[data-testid="stSuccess"] { border-radius: 6px !important; }
div[data-testid="stWarning"] { border-radius: 6px !important; }
div[data-testid="stError"]   { border-radius: 6px !important; }

/* ── Onglets ── */
button[data-baseweb="tab"] { font-weight: 600 !important; }
button[data-baseweb="tab"][aria-selected="true"] {
    color: #2563eb !important;
    border-bottom-color: #2563eb !important;
}
</style>
"""


# ── INITIALISATION & MISE À JOUR DU SESSION STATE ────────────────────────────
def init_session_state():
    if "history" not in st.session_state:
        st.session_state.history = {
            "time": list(range(30)),
            "temp": [67.0] * 30,
            "vib":  [0.8]  * 30,
            "pres": [4.4]  * 30,
            "rul":  [72.0] * 30,
        }
    defaults = {
        "base_temp": 67.0,
        "base_vib":  0.8,
        "base_pres": 4.4,
        "base_cur":  20.7,
        "tick":      757,
        "running":   True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def update_sensors():
    """Met à jour les capteurs et retourne (c_temp, c_vib, c_pres, c_cur, c_rul, r_status, rul_pct)."""
    if st.session_state.running:
        st.session_state.tick += 1
        c_temp = st.session_state.base_temp + np.random.uniform(-0.5,  0.5)
        c_vib  = max(0.1, st.session_state.base_vib  + np.random.uniform(-0.05, 0.05))
        c_pres = max(0.1, st.session_state.base_pres + np.random.uniform(-0.05, 0.05))
        c_cur  = max(0.0, st.session_state.base_cur  + np.random.uniform(-0.2,  0.2))

        stress = max(0, (c_temp - 60) / 50 * 0.4 + (c_vib / 5) * 0.3 + (c_pres / 8) * 0.3)
        c_rul  = max(0, int(72 * (1 - stress ** 1.2)))

        for key, val in zip(["temp", "vib", "pres", "rul"], [c_temp, c_vib, c_pres, c_rul]):
            st.session_state.history[key].append(val)
        st.session_state.history["time"].append(st.session_state.tick)

        for k in st.session_state.history:
            if len(st.session_state.history[k]) > 30:
                st.session_state.history[k].pop(0)
    else:
        c_temp = st.session_state.history["temp"][-1]
        c_vib  = st.session_state.history["vib"][-1]
        c_pres = st.session_state.history["pres"][-1]
        c_cur  = st.session_state.base_cur
        c_rul  = st.session_state.history["rul"][-1]

    r_status = "Nominal" if c_rul > 48 else ("Alerte" if c_rul > 24 else "Critique")
    rul_pct  = float(max(0.0, min(1.0, c_rul / 72.0)))
    return c_temp, c_vib, c_pres, c_cur, c_rul, r_status, rul_pct
