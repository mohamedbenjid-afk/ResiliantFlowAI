import streamlit as st
import plotly.graph_objects as go
import time
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from shared_state import (
    init_session_state, update_sensors, get_github_file, COMMON_CSS
)

# ── CONFIG PAGE ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Lionel — Terminal Terrain", page_icon="🔧", layout="wide")
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
st.markdown("### 🔧 Terminal Opérationnel de Terrain — Lionel")

m1, m2, m3, m4 = st.columns(4)
m1.metric("TEMPÉRATURE", "{:.1f} °C".format(c_temp))
m2.metric("VIBRATION",   "{:.1f} mm/s".format(c_vib))
m3.metric("PRESSION",    "{:.1f} bar".format(c_pres))
m4.metric("COURANT",     "{:.1f} A".format(c_cur))

st.markdown("---")

# ── BARRE RUL ─────────────────────────────────────────────────────────────────
col_l1, col_l2 = st.columns([3, 1])
col_l1.markdown("**Durée de vie résiduelle (RUL) calculée**")
col_l2.markdown(
    "<p style='text-align:right;margin:0;'><b>" + str(c_rul) + " h</b> (" + r_status + ")</p>",
    unsafe_allow_html=True
)
st.progress(rul_percentage)

lbl1, lbl2, lbl3, lbl4 = st.columns(4)
lbl1.caption("0h (Panne)")
lbl2.caption("⚠️ Seuil Agent : 24h")
lbl3.caption("🔔 Alerte Seuil : 48h")
lbl4.markdown(
    "<p style='text-align:right;font-size:0.8rem;color:gray;margin:0;'>72h (Nominal)</p>",
    unsafe_allow_html=True
)

# ── ALERTES & FICHES GITHUB ───────────────────────────────────────────────────
if c_rul <= 24:
    st.error("🚨 **ALERTE RESILIENTFLOW AI : INTERVENTION GUIDÉE DIRECTE (LIVE GITHUB)**")
    machine_info = get_github_file("data/POMPE_P17/info.json", is_json=True)
    if machine_info:
        st.caption(
            "🤖 *Matériel identifié : " + machine_info.get("modele", "?") +
            " | Zone : " + machine_info.get("emplacement", "?") + "*"
        )

    has_doc = False
    if c_temp >= 110:
        content = get_github_file("data/POMPE_P17/surchauffe.md")
        if content:
            st.markdown("<div class='doc-box'>" + content + "</div>", unsafe_allow_html=True)
            has_doc = True
    if c_vib >= 4.5:
        content = get_github_file("data/POMPE_P17/vibration.md")
        if content:
            st.markdown("<div class='doc-box'>" + content + "</div>", unsafe_allow_html=True)
            has_doc = True
    if c_pres >= 7.0:
        content = get_github_file("data/POMPE_P17/pression.md")
        if content:
            st.markdown("<div class='doc-box'>" + content + "</div>", unsafe_allow_html=True)
            has_doc = True
    if not has_doc:
        st.warning("ℹ️ Extraction automatique des fiches manuels techniques en cours "
                   "(ou dépôt distant non configuré).")
else:
    st.success("🤖 **Agent AI** : Surveillance en cours. Aucune ligne de procédure d'urgence requise.")

st.markdown("---")

# ── GRAPHIQUES + SLIDERS + SCÉNARIOS ─────────────────────────────────────────
main_col_charts, main_col_sliders, main_col_scenarios = st.columns([2, 1, 1])

with main_col_charts:
    st.markdown("##### 📈 Courbes de tendance")

    def plot_small(title, data, color, unit):
        fig = go.Figure(go.Scatter(
            x=st.session_state.history["time"], y=data,
            mode="lines", line=dict(color=color, width=2.5)
        ))
        fig.update_layout(
            title="<b>" + title + "</b> (" + "{:.1f}".format(data[-1]) + " " + unit + ")",
            height=110,
            margin=dict(l=0, r=0, t=25, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=True, gridcolor="#f1f1f1"),
        )
        return fig

    st.plotly_chart(plot_small("Température", st.session_state.history["temp"], "#ef4444", "°C"),   use_container_width=True)
    st.plotly_chart(plot_small("Vibration",   st.session_state.history["vib"],  "#f59e0b", "mm/s"), use_container_width=True)
    st.plotly_chart(plot_small("Pression",    st.session_state.history["pres"], "#3b82f6", "bar"),  use_container_width=True)

with main_col_sliders:
    st.markdown("##### ⌨️ Injection manuelle")
    st.session_state.base_temp = st.slider("Température (°C)", 60, 140, int(st.session_state.base_temp))
    st.markdown("<span class='threshold-label'>Seuil : 110°C</span>", unsafe_allow_html=True)
    st.session_state.base_vib  = st.slider("Vibration (mm/s)", 0.0, 8.0, float(st.session_state.base_vib))
    st.markdown("<span class='threshold-label'>Seuil : 4.5 mm/s</span>", unsafe_allow_html=True)
    st.session_state.base_pres = st.slider("Pression (bar)",   0.0, 10.0, float(st.session_state.base_pres))
    st.markdown("<span class='threshold-label'>Seuil : 7.0 bar</span>", unsafe_allow_html=True)

with main_col_scenarios:
    st.markdown("##### 🎭 Scénarios")
    if st.button("✅ Mode Nominal", use_container_width=True):
        st.session_state.base_temp, st.session_state.base_vib, st.session_state.base_pres, st.session_state.base_cur = 67.0, 0.8, 4.4, 21
    if st.button("🔥 Surchauffe Moteur", use_container_width=True):
        st.session_state.base_temp, st.session_state.base_vib, st.session_state.base_pres, st.session_state.base_cur = 115.0, 1.2, 4.5, 22
    if st.button("⚙️ Roulement Dégradé", use_container_width=True):
        st.session_state.base_temp, st.session_state.base_vib, st.session_state.base_pres, st.session_state.base_cur = 75.0, 5.2, 4.4, 21
    if st.button("💧 Pression Instable", use_container_width=True):
        st.session_state.base_temp, st.session_state.base_vib, st.session_state.base_pres, st.session_state.base_cur = 68.0, 1.0, 7.8, 21
    if st.button("⚠️ Défaillance P-17", type="primary", use_container_width=True):
        st.session_state.base_temp, st.session_state.base_vib, st.session_state.base_pres, st.session_state.base_cur = 125.0, 6.5, 8.5, 32

# ── AUTO-REFRESH ──────────────────────────────────────────────────────────────
if st.session_state.running:
    time.sleep(1)
    st.rerun()
