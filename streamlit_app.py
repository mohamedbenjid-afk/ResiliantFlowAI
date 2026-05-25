import streamlit as st
import numpy as np
import plotly.graph_objects as go

# 1. Configuration de la page
st.set_page_config(page_title="Pompe P-17 — Unité B", page_icon="🟢", layout="wide")

# CSS personnalisé pour obtenir les cartes de métriques blanches et épurées
st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        padding: 15px 20px !important;
        border-radius: 8px !important;
    }
    .stButton>button { border-radius: 6px !important; }
    </style>
""", unsafe_allow_html=True)

# 2. Initialisation des variables dans le Session State
if 'temp' not in st.session_state: st.session_state.temp = 64.0
if 'vib' not in st.session_state: st.session_state.vib = 1.0
if 'pres' not in st.session_state: st.session_state.pres = 4.8
if 'courant' not in st.session_state: st.session_state.courant = 21.0

# --- ENTÊTE DU DASHBOARD ---
top_left, top_right = st.columns([4, 1])
with top_left:
    st.markdown("## 🟢 Pompe P-17 — Unité B")
with top_right:
    col_b1, col_b2 = st.columns(2)
    col_b1.button("⏸️ En cours", use_container_width=True)
    if col_b2.button("🔄 Reset", use_container_width=True):
        st.session_state.temp, st.session_state.vib, st.session_state.pres, st.session_state.courant = 64.0, 1.0, 4.8, 21.0
        st.rerun()

# --- SECTION 1 : LES METRIQUES DU HAUT ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("TEMPÉRATURE", f"{st.session_state.temp:.0f} °C")
m2.metric("VIBRATION", f"{st.session_state.vib:.1f} mm/s")
m3.metric("PRESSION", f"{st.session_state.pres:.1f} bar")
m4.metric("COURANT", f"{st.session_state.courant:.1f} A")

st.markdown("---")

# --- INTERPOLATION DU CALCUL RUL (ÉVITE TOUTE ERREUR DE SYNTAXE) ---
v_t = max(0.0, min(1.0, (st.session_state.temp - 64.0) / (110.0 - 64.0 if col_b1 else 1.0)))
v_v = max(0.0, min(1.0, (st.session_state.vib - 1.0) / (4.5 - 1.0)))
v_p = max(0.0, min(1.0, (st.session_state.pres - 4.8) / (7.0 - 4.8)))
v_c = max(0.0, min(1.0, (st.session_state.courant - 21.0) / (28.0 - 21.0)))
stress = (v_t * 0.35) + (v_v * 0.30) + (v_p * 0.20) + (v_c * 0.15)
rul = max(0.0, 72.0 * (1.0 - (stress ** 0.6)))

# --- SECTION 2 : LA BARRE DE PROGRESSION DU RUL ---
status_text = "🟢 Nominal" if rul > 48 else ("游 Alerte" if rul > 24 else "🔴 Critique")
st.markdown(f"### Durée de vie résiduelle (RUL) : <span style='float:right;'><b>{rul:.0f} h</b> <small style='color:gray;'>{status_text}</small></span>", unsafe_allow_html=True)

bar_color = "#10b981" if rul > 48 else ("#f59e0b" if rul > 24 else "#ef4444")
pct = (rul / 72.0) * 100
st.markdown(f"""
    <div style="width:100%; background-color:#e2e8f0; height:16px; border-radius:8px; overflow:hidden;">
        <div style="width:{pct}%; background-color:{bar_color}; height:100%; transition: width 0.4s;"></div>
    </div>
    <div style="display:flex; justify-content:space-between; font-size:12px; color:#64748b; margin-top:4px; margin-bottom:20px;">
        <span>0h</span><span style="color:#ef4444; font-weight:600;">Seuil agent : 24h</span><span style="color:#f59e0b; font-weight:600;">Alerte : 48h</span><span>72h (nominal)</span>
    </div>
""", unsafe_allow_html=True)

# --- SECTION 3 : LES MULTI-GRAPHES PLOTLY (STYLE BLANC) ---
def build_chart(title, current, nominal, color):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(20)), y=np.linspace(nominal, current, 20), mode='lines', line=dict(color=color, width=2.5)))
    fig.update_layout(
        title=f"<b>{title}</b> <span style='float:right;'>{current}</span>", height=150,
        margin=dict(l=15, r=15, t=35, b=15), plot_bgcolor='white', paper_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#f1f5f9', showticklabels=False),
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9')
    )
    return fig

g1, g2 = st.columns(2)
with g1:
    st.plotly_chart(build_chart("Température (°C)", st.session_state.temp, 64.0, "#ef4444"), use_container_width=True)
    st.plotly_chart(build_chart("Pression (bar)", st.session_state.pres, 4.8, "#3b82f6"), use_container_width=True)
with g2:
    st.plotly_chart(build_chart("Vibration (mm/s)", st.session_state.vib, 1.0, "#f59e0b"), use_container_width=True)
    st.plotly_chart(build_chart("RUL (h)", round(rul, 1), 72.0, "#10b981"), use_container_width=True)

# --- SECTION 4 : INJECTION MANUELLE (CONTROLES SLIDERS) ---
st.markdown("   ")
with st.container(border=True):
    st.markdown("⚙️ **Injection manuelle — forcer des valeurs**")
    sc1, sc2 = st.columns(2)
    with sc1:
        st.session_state.temp = sc1.slider("Température <span style='color:red;'>seuil 110°C</span>", 50.0, 145.0, float(st.session_state.temp), 1.0, label_visibility="visible")
        st.session_state.pres = sc1.slider("Pression <span style='color:orange;'>seuil 7 bar</span>", 2.0, 11.0, float(st.session_state.pres), 0.1)
    with sc2:
        st.session_state.vib = sc2.slider("Vibration <span style='color:orange;'>seuil 4.5 mm/s</span>", 0.5, 9.0, float(st.session_state.vib), 0.1)
        st.session_state.courant = sc2.slider("Courant <span style='color:orange;'>seuil 28A</span>", 10.0, 40.0, float(st.session_state.courant), 0.5)

# --- SECTION 5 : BOUTONS DE SCÉNARIOS RAPIDES ---
st.markdown("### Scénarios rapides")
b1, b2, b3, b4, b5 = st.columns(5)
if b1.button("Nominal", use_container_width=True):
    st.session_state.temp, st.session_state.vib, st.session_state.pres, st.session_state.courant = 64.0, 1.0, 4.8, 21.0
    st.rerun()
if b2.button("Surchauffe moteur", use_container_width=True):
    st.session_state.temp, st.session_state.vib, st.session_state.pres, st.session_state.courant = 112.0, 1.4, 5.0, 23.0
    st.rerun()
if b3.button("Roulement dégradé", use_container_width=True):
    st.session_state.temp, st.session_state.vib, st.session_state.pres, st.session_state.courant = 78.0, 4.8, 4.9, 22
