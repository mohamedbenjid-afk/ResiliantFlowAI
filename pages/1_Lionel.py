import streamlit as st
import plotly.graph_objects as go
import requests

# Récupération des variables globales calculées par l'accueil 
c_temp = st.session_state.get('c_temp', 67.0)
c_vib = st.session_state.get('c_vib', 0.8)
c_pres = st.session_state.get('c_pres', 4.4)
c_cur = st.session_state.get('c_cur', 20.7)
c_rul = st.session_state.get('c_rul', 72)
r_status = "Nominal" if c_rul > 48 else ("Alerte" if c_rul > 24 else "Critique")
rul_percentage = float(max(0.0, min(1.0, c_rul / 72.0)))

GITHUB_USER = "VOTRE_NOM_UTILISATEUR_GITHUB"
GITHUB_REPO = "maintenance-knowledge-base"
GITHUB_BRANCH = "main"

def get_github_file(path, is_json=False):
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{path}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json() if is_json else response.text
    except: pass
    return None

st.markdown("### 🔧 Terminal Opérationnel de Terrain — Lionel")

m1, m2, m3, m4 = st.columns(4)
m1.metric("TEMPÉRATURE", "{:.1f} °C".format(c_temp))
m2.metric("VIBRATION", "{:.1f} mm/s".format(c_vib))
m3.metric("PRESSION", "{:.1f} bar".format(c_pres))
m4.metric("COURANT", "{:.1f} A".format(c_cur))

st.markdown("---")
col_l1, col_l2 = st.columns([3, 1])
col_l1.markdown("**Durée de vie résiduelle (RUL) calculée**")
col_l2.markdown(f"<p style='text-align: right; margin: 0;'><b>{c_rul} h</b> ({r_status})</p>", unsafe_allow_html=True)
st.progress(rul_percentage)

if c_rul <= 24:
    st.error("🚨 **ALERTE RESILIENTFLOW AI : INTERVENTION GUIDÉE DIRECTE (LIVE GITHUB)**")
    machine_info = get_github_file("data/POMPE_P17/info.json", is_json=True)
    if machine_info:
        st.caption(f"🤖 *Matériel identifié : {machine_info.get('modele')} | Zone : {machine_info.get('emplacement')}*")
    
    has_doc = False
    if c_temp >= 110:
        content = get_github_file("data/POMPE_P17/surchauffe.md")
        if content: st.markdown(f"<div class='doc-box'>{content}</div>", unsafe_allow_html=True); has_doc = True
    if not has_doc:
        st.warning("ℹ️ Extraction automatique des fiches manuels techniques en cours.")
else:
    st.success("🤖 **Agent AI** : Surveillance en cours. Aucune ligne de procédure d'urgence requise à l'écran.")

st.markdown("---")
main_col_charts, main_col_sliders, main_col_scenarios = st.columns([2, 1, 1])

with main_col_charts:
    st.markdown("##### 📈 Courbes de tendance")
    def plot_small(title, data, color, unit):
        fig = go.Figure(go.Scatter(x=st.session_state.history["time"], y=data, mode='lines', line=dict(color=color, width=2.5)))
        fig.update_layout(title=f"<b>{title}</b> ({data[-1]:.1f} {unit})", height=110, margin=dict(l=0,r=0,t=25,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, showticklabels=False), yaxis=dict(showgrid=True, gridcolor='#f1f1f1'))
        return fig
    st.plotly_chart(plot_small("Température", st.session_state.history["temp"], "#ef4444", "°C"), use_container_width=True)

with main_col_sliders:
    st.markdown("##### ⌨️ Injection manuelle")
    st.session_state.base_temp = st.slider("Température", 60, 140, int(st.session_state.base_temp), label_visibility="collapsed")
