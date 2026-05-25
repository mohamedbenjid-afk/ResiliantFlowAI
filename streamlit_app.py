import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime

# 1. Configuration de la page
st.set_page_config(page_title="Pompe P-17 — Unité B", layout="wide")

# Injection CSS pour les cartes de métriques et le rapport d'agent
st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        padding: 15px 20px !important;
        border-radius: 8px !important;
    }
    .agent-box {
        background-color: #fff5f5;
        border-left: 5px solid #e53e3e;
        padding: 20px;
        border-radius: 4px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ── Constantes ───────────────────────────────────────────────────────────────
RUL_MAX = 72
RUL_TRIGGER = 24
WEIGHTS = {"temp": 0.35, "vib": 0.30, "pres": 0.20, "cur": 0.15}

# ── Initialisation des Historiques (Session State) ───────────────────────────
if 'history' not in st.session_state:
    st.session_state.history = {
        "time": list(range(30)),
        "temp": [64.0] * 30,
        "vib": [1.0] * 30,
        "pres": [4.8] * 30,
        "rul": [72.0] * 30
    }
if 'base_temp' not in st.session_state: st.session_state.base_temp = 64.0
if 'base_vib' not in st.session_state: st.session_state.base_vib = 1.0
if 'base_pres' not in st.session_state: st.session_state.base_pres = 4.8
if 'base_cur' not in st.session_state: st.session_state.base_cur = 21.0
if 'tick' not in st.session_state: st.session_state.tick = 434
if 'running' not in st.session_state: st.session_state.running = True

# NOUVEAU: Stockage du rapport de l'agent pour éviter la régénération à chaque frame
if 'agent_report' not in st.session_state: st.session_state.agent_report = None
if 'agent_triggered_at' not in st.session_state: st.session_state.agent_triggered_at = None

# ── Fonction de l'Agent de Diagnostic ────────────────────────────────────────
def run_diagnostic_agent(temp, vib, pres, cur, rul):
    """Simule un agent d'IA analysant les causes de la dégradation de la RUL"""
    triggers = []
    actions = []
    
    if temp > 90:
        triggers.append(f"Surchauffe thermique critique ({temp:.1f}°C)")
        actions.append("- Vérifier le circuit de refroidissement de la pompe.\n- Contrôler la lubrification des paliers.")
    if vib > 3.5:
        triggers.append(f"Vibrations anormales sévères ({vib:.2f} mm/s)")
        actions.append("- Inspecter d'urgence l'alignement de l'arbre.\n- Planifier une analyse fréquentielle des roulements.")
    if pres > 6.5:
        triggers.append(f"Surpression hydraulique ({pres:.2f} bar)")
        actions.append("- Inspecter les vannes de refoulement.\n- Vérifier l'absence d'obstruction sur la ligne.")
    if cur > 26.0:
        triggers.append(f"Surcharge électrique du moteur ({cur:.1f} A)")
        actions.append("- Contrôler l'isolation des enroulements moteurs.")

    if not triggers:
        triggers.append("Dégradation cumulative lente des paramètres physiques généraux.")
        actions.append("- Planifier une inspection visuelle lors du prochain arrêt de maintenance.")

    report = f"""
    ### 🤖 Rapport Automatique de l'Agent de Maintenance
    **Statut :** 🚨 Défaillance Imminente Suspectée (RUL < {RUL_TRIGGER}h)  
    **Date de l'analyse :** `t = {st.session_state.tick}` | **RUL Diagnostiquée :** `{rul} heures`
    
    #### 🔍 Facteurs Déclencheurs Identifiés :
    {"".join([f'* ' + t + '  \n' for t in triggers])}
    
    #### 🛠️ Plan d'Action Recommandé (Prioritaire) :
    {"".join([a + '  \n' for a in actions])}
    """
    return report

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
        st.session_state.history = {"time": list(range(30)), "temp": [64.0]*30, "vib": [1.0]*30, "pres": [4.8]*30, "rul": [72.0]*30}
        st.session_state.base_temp, st.session_state.base_vib, st.session_state.base_pres, st.session_state.base_cur = 64.0, 1.0, 4.8, 21.0
        st.session_state.tick = 434
        st.session_state.agent_report = None
        st.session_state.agent_triggered_at = None
        st.rerun()

# ── Évolution des données en temps réel ──────────────────────────────────────
if st.session_state.running:
    st.session_state.tick += 1
    
    # Ajout de bruit aléatoire
    current_temp = st.session_state.base_temp + np.random.uniform(-0.8, 0.8)
    current_vib = max(0.1, st.session_state.base_vib + np.random.uniform(-0.15, 0.15))
    current_pres = max(0.5, st.session_state.base_pres + np.random.uniform(-0.1, 0.1))
    current_cur = max(0.0, st.session_state.base_cur + np.random.uniform(-0.3, 0.3))
    
    # Calcul du RUL instantané
    dt = max(0.0, min(1.0, (current_temp - 64.0) / (140.0 - 64.0)))
    dv = max(0.0, min(1.0, (current_vib - 1.0) / (8.0 - 1.0)))
    dp = max(0.0, min(1.0, (current_pres - 4.8) / (10.0 - 4.8)))
    dc = max(0.0, min(1.0, (current_cur - 21.0) / (40.0 - 21.0)))
    stress = (dt * WEIGHTS["temp"] + dv * WEIGHTS["vib"] + dp * WEIGHTS["pres"] + dc * WEIGHTS["cur"])
    current_rul = max(0, round(RUL_MAX * (1 - stress ** 0.6)))

    # Mise à jour de l'historique
    st.session_state.history["time"].append(st.session_state.tick)
    st.session_state.history["temp"].append(current_temp)
    st.session_state.history["vib"].append(current_vib)
    st.session_state.history["pres"].append(current_pres)
    st.session_state.history["rul"].append(current_rul)
    
    for k in st.session_state.history:
        if len(st.session_state.history[k]) > 30:
            st.session_state.history[k].pop(0)
else:
    current_temp = st.session_state.history["temp"][-1]
    current_vib = st.session_state.history["vib"][-1]
    current_pres = st.session_state.history["pres"][-1]
    current_cur = st.session_state.base_cur
    current_rul = st.session_state.history["rul"][-1]

# NOUVEAU: Déclenchement automatique de l'agent si RUL critique
if current_rul <= RUL_TRIGGER:
    # On génère le rapport si on change d'état critique ou s'il n'existe pas encore
    if st.session_state.agent_report is None:
        st.session_state.agent_report = run_diagnostic_agent(current_temp, current_vib, current_pres, current_cur, current_rul)
        st.session_state.agent_triggered_at = st.session_state.tick
else:
    # Si le RUL redevient normal (ex: clic sur Nominal), on efface le rapport de l'agent
    st.session_state.agent_report = None
    st.session_state.agent_triggered_at = None


# ── Section 1 : Métriques du haut ────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("TEMPÉRATURE", f"{current_temp:.1f} °C")
m2.metric("VIBRATION", f"{current_vib:.2f} mm/s")
m3.metric("PRESSION", f"{current_pres:.2f} bar")
m4.metric("COURANT", f"{current_cur:.1f} A")

# ── Section 2 : Barre RUL ────────────────────────────────────────────────────
st.markdown("---")
status_text = "Nominal" if current_rul > 48 else ("Alerte" if current_rul > RUL_TRIGGER else "Critique")
status_color = "#10b981" if current_rul > 48 else ("#f59e0b" if current_rul > RUL_TRIGGER else "#ef4444")
pct = (current_rul / RUL_MAX) * 100

st.markdown(f"#### Durée de vie résiduelle (RUL) <span style='float:right; color:{status_color};'><b>{current_rul} h</b> <small style='color:gray;'>{status_text}</small></span>", unsafe_allow_html=True)
st.markdown(f"""
    <div style="width:100%; background-color:#e2e8f0; height:14px; border-radius:7px; overflow:hidden;">
        <div style="width:{pct}%; background-color:{status_color}; height:100%; transition: width 0.3s;"></div>
    </div>
""", unsafe_allow_html=True)

# ── Section NOUVEAU : Affichage du Rapport de l'Agent ─────────────────────────
if st.session_state.agent_report is not None:
    st.markdown(" ")
    with st.container():
        # Encadré visuel pour le rapport
        st.markdown(f'<div class="agent-box">', unsafe_allow_html=True)
        
        # Organisation du rapport avec un bouton de rafraîchissement manuel au cas où
        rep_col, btn_col = st.columns([5, 1])
        with rep_col:
            st.markdown(st.session_state.agent_report)
        with btn_col:
            if st.button("🔄 Ré-analyser", use_container_width=True):
                st.session_state.agent_report = run_diagnostic_agent(current_temp, current_vib, current_pres, current_cur, current_rul)
                st.rerun()
                
        st.markdown('</div>', unsafe_allow_html=True)

# ── Section 3 : Graphiques Temporels VIVANTS ──────────────────────────────────
def make_live_chart(title, y_data, color, suffix=""):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=st.session_state.history["time"], y=y_data, mode='lines+markers', line=dict(color=color, width=2.5)))
    fig.update_layout(
        title=f"<b>{title}</b> — {y_data[-1]:.1f}{suffix}", height=150,
        margin=dict(l=15, r=15, t=35, b=15), plot_bgcolor='white', paper_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#f1f5f9', showticklabels=False),
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9')
    )
    return fig

g1, g2 = st.columns(2)
with g1:
    st.plotly_chart(make_live_chart("Température", st.session_state.history["temp"], "#ef4444", "°C"), use_container_width=True)
    st.plotly_chart(make_live_chart("Pression", st.session_state.history["pres"], "#3b82f6", " bar"), use_container_width=True)
with g2:
    st.plotly_chart(make_live_chart("Vibration", st.session_state.history["vib"], "#f59e0b", " mm/s"), use_container_width=True)
    st.plotly_chart(make_live_chart("RUL (h)", st.session_state.history["rul"], "#10b981", "h"), use_container_width=True)

# ── Section 4 : Scénarios rapides ────────────────────────────────────────────
st.markdown("### Scénarios rapides")
b1, b2, b3, b4, b5 = st.columns(5)
if b1.button("Nominal", use_container_width=True):
    st.session_state.base_temp, st.session_state.base_vib, st.session_state.base_pres, st.session_state.base_cur = 64.0, 1.0, 4.8, 21.0
if b2.button("Surchauffe moteur", use_container_width=True):
    st.session_state.base_temp, st.session_state.base_vib, st.session_state.base_pres, st.session_state.base_cur = 112.0, 1.4, 5.0, 23.0
if b3.button("Roulement dégradé", use_container_width=True):
    st.session_state.base_temp, st.session_state.base_vib, st.session_state.base_pres, st.session_state.base_cur = 78.0, 4.8, 4.9, 22.0
if b4.button("Pression instable", use_container_width=True):
    st.session_state.base_temp, st.session_state.base_vib, st.session_state.base_pres, st.session_state.base_cur = 66.0, 1.8, 7.4, 21.5
if b5.button("🔥 Défaillance critique P-17", type="primary", use_container_width=True):
    st.session_state.base_temp, st.session_state.base_vib, st.session_state.base_pres, st.session_state.base_cur = 125.0, 6.2, 7.8, 31.5

# ── Boucle de rafraîchissement automatique ────────────────────────────────────
if st.session_state.running:
    time.sleep(1) 
    st.rerun()
