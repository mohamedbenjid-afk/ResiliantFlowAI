import streamlit as st
import numpy as np
import plotly.graph_objects as go

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

# ── Entête du Dashboard ──────────────────────────────────────────────────────
st.markdown("## 🟢 Pompe P-17 — Unité B")
st.markdown("---")

# ── Section 1 : Sélection du Scénario (Boutons Radio simples) ────────────────
st.markdown("### 🛠️ Sélectionner un scénario d'exploitation")
scenario = st.radio(
    "État actuel de la pompe :",
    ["Nominal (Tout va bien)", "Surchauffe moteur", "Roulement dégradé", "Pression instable", "🔥 Défaillance critique P-17"],
    horizontal=True
)

# ── Section 2 : Définition des valeurs selon le scénario choisi ──────────────
if scenario == "Nominal (Tout va bien)":
    temp, vib, pres, cur, rul_text, rul_days, color = 64.2, 1.02, 4.8, 21.0, "3.0 mois", 90.0, "#10b981"
elif scenario == "Surchauffe moteur":
    temp, vib, pres, cur, rul_text, rul_days, color = 92.5, 1.45, 5.1, 23.2, "1.8 mois", 54.0, "#f59e0b"
elif scenario == "Roulement dégradé":
    temp, vib, pres, cur, rul_text, rul_days, color = 72.1, 2.84, 4.9, 22.1, "24 jours", 24.0, "#f59e0b"
elif scenario == "Pression instable":
    temp, vib, pres, cur, rul_text, rul_days, color = 66.8, 1.81, 6.2, 21.5, "1.1 mois", 33.0, "#f59e0b"
else:  # Défaillance critique
    temp, vib, pres, cur, rul_text, rul_days, color = 125.4, 6.21, 7.8, 31.5, "14 heures (Critique !)", 0.5, "#ef4444"

# ── Section 3 : Métriques numériques du haut ─────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("TEMPÉRATURE", f"{temp} °C")
m2.metric("VIBRATION", f"{vib} mm/s")
m3.metric("PRESSION", f"{pres} bar")
m4.metric("COURANT", f"{cur} A")

# ── Section 4 : Barre de Progression du RUL ──────────────────────────────────
st.markdown("---")
st.markdown(f"#### Durée de vie résiduelle (RUL) <span style='float:right; color:{color};'><b>{rul_text}</b></span>", unsafe_allow_html=True)

# Barre de progression visuelle (0 à 90 jours)
pct = (rul_days / 90.0) * 100
st.markdown(f"""
    <div style="width:100%; background-color:#e2e8f0; height:14px; border-radius:7px; overflow:hidden;">
        <div style="width:{pct}%; background-color:{color}; height:100%;"></div>
    </div>
""",
