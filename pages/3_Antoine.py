import streamlit as st
import plotly.graph_objects as go
import time
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from shared_state import init_session_state, update_sensors, COMMON_CSS

# ── CONFIG PAGE ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Antoine — Indicateurs Stratégiques", page_icon="📊", layout="wide")
st.markdown(COMMON_CSS, unsafe_allow_html=True)

# ── SESSION STATE & CAPTEURS ──────────────────────────────────────────────────
init_session_state()
c_temp, c_vib, c_pres, c_cur, c_rul, r_status, rul_percentage = update_sensors()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("""
    <div class="escp-banner">
        🎓 <b>Projet de Fin d'Études ESCP</b><br>
        ⚙️ <i>Maintenance Prescriptive & Industrie 4.0</i>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### ResilientFlow AI\n*Couche Prescriptive v1*")

if st.sidebar.button("⏸️ Pause / ▶️ Reprendre", use_container_width=True):
    st.session_state.running = not st.session_state.running

st.sidebar.caption("Statut machine : Pompe P-17 (Unité B)")
st.sidebar.caption("Horodatage système : t = " + str(st.session_state.tick))
st.sidebar.caption("RUL estimé : " + str(c_rul) + " heures")
st.sidebar.page_link("streamlit_app.py", label="⬅️ Retour à l'accueil")

# ── CONTENU PRINCIPAL ─────────────────────────────────────────────────────────
st.markdown("### 📊 Indicateurs Stratégiques et ROI Financement — Antoine")
st.markdown("*Suivi consolidé de la performance industrielle et aide à la décision d'investissement (CAPEX vs OPEX).*")

k1, k2, k3 = st.columns(3)
k1.metric("Pertes de production évitées", "312 000 €",  delta="+14 alertes anticipées")
k2.metric("Taux de Disponibilité (OEE)",  "96.4 %",     delta="+2.1 % vs Année N-1")
k3.metric("ROI Couche Prescriptive",      "7.6 x",      delta="Target CODIR dépassée")

st.markdown("---")
st.markdown("#### 🔮 Analyse prédictive du plan de renouvellement matériel (Pompe P-17)")
st.write(
    "En croisant la vitesse d'usure calculée par le modèle RUL et l'augmentation du coût des rechanges, "
    "l'agent simule la meilleure décision financière."
)

col_strat, col_graph = st.columns([1, 2])

with col_strat:
    mode_invest = st.selectbox(
        "Simuler un scénario budgétaire :",
        [
            "Conserver la pompe P-17 (Continuer en maintenance prescriptive)",
            "Investir dans le remplacement par la pompe neuve AlphaFlow-18",
        ]
    )
    st.info(
        "**Avis de l'agent AI :** Bien que la couche prescriptive repousse la panne de la P-17, "
        "l'équipement approche de sa limite de fatigue structurelle."
    )

with col_graph:
    timeline = ["Actuel", "Année +1", "Année +2", "Année +3"]
    fig_cap   = go.Figure()

    if "Conserver" in mode_invest:
        fig_cap.add_trace(go.Scatter(
            x=timeline, y=[12000, 29000, 55000, 89000],
            name="Coût Opex Cumulé (Pièces + Maintenance)",
            line=dict(color="#f59e0b", width=3)
        ))
        fig_cap.update_layout(
            title="Projection des dépenses cumulées (EUR)",
            height=200, margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig_cap, use_container_width=True)
        st.caption("🔴 **Alerte :** Explosion des coûts de rechange à partir de l'année +2 due à l'obsolescence.")
    else:
        fig_cap.add_trace(go.Scatter(
            x=timeline, y=[80000, 82000, 84000, 86000],
            name="Plan d'investissement Capex (Amorti)",
            line=dict(color="#10b981", width=3)
        ))
        fig_cap.update_layout(
            title="Frais d'acquisition et intégration (EUR)",
            height=200, margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig_cap, use_container_width=True)
        st.caption("Gains validés : Point mort financier atteint dès le 14ème mois grâce au zéro-panne.")

# ── AUTO-REFRESH ──────────────────────────────────────────────────────────────
if st.session_state.running:
    time.sleep(1)
    st.rerun()
