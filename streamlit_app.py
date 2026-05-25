import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time, json
from datetime import datetime

st.set_page_config(page_title="ResilientFlow AI — P-17", layout="wide")

# ── Constantes ────────────────────────────────────────────────────────────────
RUL_MAX = 72
RUL_TRIGGER = 24   # Seuil déclenchement agent
RUL_WARN = 48      # Seuil alerte
WEIGHTS = {"temp": 0.35, "vib": 0.30, "pres": 0.20, "cur": 0.15}

# ── Contexte simulé (le JSON de Mohamed) ─────────────────────────────────────
CONTEXT = {
    "equipement": "Pompe P-17 — Unité B",
    "of_actif": "OF-2847",
    "duree_of_restante_h": 52,
    "equipe_dispo_dans_h": 48,
    "pieces_stock": ["Joint JM-220 (B-12)", "Roulement 6205-2RS"],
    "technicien_disponible": "Lionel"
}

# ── Calcul RUL ────────────────────────────────────────────────────────────────
def compute_rul(temp, vib, pres, cur):
    dt = max(0, (temp - 80) / (140 - 80))
    dv = max(0, (vib  - 2.0) / (8 - 2.0))
    dp = max(0, (pres - 5.5) / (10 - 5.5))
    dc = max(0, (cur  - 22) / (40 - 22))
    stress = (dt * WEIGHTS["temp"] + dv * WEIGHTS["vib"] +
              dp * WEIGHTS["pres"] + dc * WEIGHTS["cur"])
    return max(0, round(RUL_MAX * (1 - stress ** 0.6)))

# ── Prescriptions (moteur 3 scénarios) ───────────────────────────────────────
def get_prescriptions(rul, context):
    fenetre = context["equipe_dispo_dans_h"]
    return [
        {
            "action": "Réduire cadence 20 %",
            "rul_projete": min(RUL_MAX, round(rul * 2.8)),
            "impact_of": "OF non interrompu",
            "optimal": min(RUL_MAX, round(rul * 2.8)) >= fenetre
        },
        {
            "action": "Réduire pression 15 %",
            "rul_projete": min(RUL_MAX, round(rul * 1.9)),
            "impact_of": "Débit réduit 15 %",
            "optimal": False
        },
        {
            "action": "Arrêt immédiat",
            "rul_projete": 999,
            "impact_of": "Production interrompue",
            "optimal": False
        },
    ]

# ── UI ────────────────────────────────────────────────────────────────────────
st.title("🏭 ResilientFlow AI — Simulateur P-17")
st.caption("Couche prescriptive IoT/RUL — Use case fictif illustratif")

# Scénarios rapides
col_s = st.columns(5)
scenarios = {
    "Nominal":      (72,  1.2, 4.8, 18.2),
    "Surchauffe":   (118, 2.1, 5.1, 22.0),
    "Vibration":    (85,  5.8, 4.9, 20.5),
    "Pression":     (78,  1.8, 7.6, 19.0),
    "Critique P-17":(125, 6.2, 7.8, 31.5),
}
selected = None
for i, (name, vals) in enumerate(scenarios.items()):
    if col_s[i].button(name, use_container_width=True):
        selected = vals

# Sliders injection manuelle
with st.expander("Injection manuelle des valeurs capteurs", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    defaults = selected if selected else (
        st.session_state.get("temp", 72),
        st.session_state.get("vib", 1.2),
        st.session_state.get("pres", 4.8),
        st.session_state.get("cur", 18.2),
    )
    temp = c1.slider("Température (°C)  ⚠️ seuil 110°C",
                     60.0, 140.0, float(defaults[0]), 0.5)
    vib  = c2.slider("Vibration (mm/s)  ⚠️ seuil 4.5",
                     0.5, 8.0, float(defaults[1]), 0.1)
    pres = c3.slider("Pression (bar)  ⚠️ seuil 7.0",
                     1.0, 10.0, float(defaults[2]), 0.1)
    cur  = c4.slider("Courant (A)  ⚠️ seuil 28A",
                     10.0, 40.0, float(defaults[3]), 0.2)

# Calcul RUL
rul = compute_rul(temp, vib, pres, cur)

# KPIs
st.divider()
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Température", f"{temp:.0f} °C",
          delta="⚠️ SEUIL" if temp > 110 else None,
          delta_color="inverse")
k2.metric("Vibration",   f"{vib:.1f} mm/s",
          delta="⚠️ SEUIL" if vib > 4.5 else None,
          delta_color="inverse")
k3.metric("Pression",    f"{pres:.1f} bar",
          delta="⚠️" if pres > 7 else None,
          delta_color="inverse")
k4.metric("Courant",     f"{cur:.1f} A",
          delta="⚠️" if cur > 28 else None,
          delta_color="inverse")
k5.metric("RUL estimé",  f"{rul} h",
          delta="CRITIQUE" if rul <= RUL_TRIGGER else
                "Alerte"   if rul <= RUL_WARN    else "Nominal",
          delta_color="inverse" if rul <= RUL_WARN else "normal")

# Barre RUL
bar_color = "🔴" if rul <= RUL_TRIGGER else "🟡" if rul <= RUL_WARN else "🟢"
st.progress(rul / RUL_MAX,
            text=f"{bar_color} RUL = {rul}h / {RUL_MAX}h  "
                 f"— Seuil agent : {RUL_TRIGGER}h")

# ── Agent ─────────────────────────────────────────────────────────────────────
st.divider()
if rul <= RUL_TRIGGER:
    st.error(f"## 🚨 Agent déclenché — RUL = {rul}h")
    st.write(f"**Contexte :** OF `{CONTEXT['of_actif']}` actif encore "
             f"{CONTEXT['duree_of_restante_h']}h · "
             f"Équipe disponible dans {CONTEXT['equipe_dispo_dans_h']}h · "
             f"Pièces en stock : {', '.join(CONTEXT['pieces_stock'])}")

    st.write("**Prescriptions calculées :**")
    prescs = get_prescriptions(rul, CONTEXT)
    for p in prescs:
        icon = "✅" if p["optimal"] else ("⚠️" if p["rul_projete"] >= RUL_WARN else "🛑")
        label = " ← **Recommandé**" if p["optimal"] else ""
        st.write(f"{icon} **{p['action']}** → RUL projeté : **{p['rul_projete']}h** "
                 f"· {p['impact_of']}{label}")

    if st.button("✅ Valider la prescription optimale", type="primary"):
        st.success(f"Prescription validée par {CONTEXT['technicien_disponible']} "
                   f"à {datetime.now().strftime('%H:%M:%S')} — "
                   f"Ticket créé : OF-{CONTEXT['of_actif']}-MAINT")

elif rul <= RUL_WARN:
    st.warning(f"⚠️ Alerte — RUL = {rul}h — Surveillance renforcée "
               f"(seuil déclenchement : {RUL_TRIGGER}h)")
else:
    st.info("Agent en veille — RUL nominal")
