import streamlit as st
from shared_state import COMMON_CSS

# ── CONFIG PAGE ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="ResilientFlow AI", page_icon="🏭", layout="wide")
st.markdown(COMMON_CSS, unsafe_allow_html=True)

# ── STYLES SPÉCIFIQUES À L'ACCUEIL ───────────────────────────────────────────
st.markdown("""
<style>
.hero-title {
    font-size: 2.4rem; font-weight: 800; color: #1a3a5c; margin-bottom: 4px;
}
.hero-subtitle {
    font-size: 1.05rem; color: #64748b; margin-bottom: 6px;
}
.status-badge {
    display: inline-block; background-color: #dcfce7; color: #15803d;
    border-radius: 20px; padding: 3px 16px; font-size: 0.78rem;
    font-weight: 600; border: 1px solid #86efac;
}
.agent-card {
    background: #ffffff; border: 1px solid #dde3ee;
    border-radius: 12px; padding: 28px 20px 20px; text-align: center;
}
.agent-icon  { font-size: 2.6rem; margin-bottom: 10px; }
.agent-name  { font-size: 1.1rem; font-weight: 700; color: #1a3a5c; margin-bottom: 3px; }
.agent-role  {
    font-size: 0.78rem; color: #2563eb; font-weight: 600;
    margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.05em;
}
.agent-desc  { font-size: 0.79rem; color: #475569; line-height: 1.55; margin-bottom: 4px; }
.stat-bar {
    background: #ffffff; border: 1px solid #dde3ee; border-radius: 10px;
    padding: 14px 28px; display: flex; gap: 40px; align-items: center;
    margin-bottom: 24px; flex-wrap: wrap;
}
.stat-val { font-size: 1.35rem; font-weight: 700; color: #1a3a5c; }
.stat-lbl { font-size: 0.70rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
</style>
""", unsafe_allow_html=True)

# ── BANNIÈRE ESCP ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="escp-banner">
    🎓 <b>Projet de Fin d'Études ESCP</b> &nbsp;·&nbsp;
    🏭 <i>Maintenance Prescriptive &amp; Industrie 4.0</i>
</div>
""", unsafe_allow_html=True)

# ── HERO ──────────────────────────────────────────────────────────────────────
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown('<div class="hero-title">🏭 ResilientFlow AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">Plateforme prescriptive · Pompe P-17, Unité B</div>',
        unsafe_allow_html=True,
    )
with col_status:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<span class="status-badge">✅ Système opérationnel</span>', unsafe_allow_html=True)

# ── BARRE DE STATS ────────────────────────────────────────────────────────────
st.markdown("""
<div class="stat-bar">
    <div><div class="stat-val">4</div><div class="stat-lbl">Agents IA actifs</div></div>
    <div><div class="stat-val">6</div><div class="stat-lbl">Bases Notion</div></div>
    <div><div class="stat-val">312 k€</div><div class="stat-lbl">Pertes évitées</div></div>
    <div><div class="stat-val">96,4 %</div><div class="stat-lbl">Disponibilité OEE</div></div>
    <div><div class="stat-val">7,6×</div><div class="stat-lbl">ROI prescriptif</div></div>
</div>
""", unsafe_allow_html=True)

st.markdown("### Sélectionnez votre espace de travail")
st.caption(
    "Chaque vue est adaptée à un métier — de l'intervention terrain jusqu'à la décision stratégique."
)
st.markdown("<br>", unsafe_allow_html=True)

# ── 4 CARTES AGENTS ───────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

agents = [
    (c1, "🛠️", "Lionel",  "Technicien Terrain",
     "Capteurs temps réel, RUL, courbes de tendance, scénarios de défaillance et procédures techniques.",
     "pages/1_Lionel.py", "Ouvrir le terminal terrain"),

    (c2, "🗂️", "Sophie",  "Manager Maintenance",
     "Arbitrage planification, gestion des ressources, stocks de pièces et ordonnancement.",
     "pages/2_Sophie.py", "Ouvrir l'espace d'arbitrage"),

    (c3, "📈", "Antoine", "Directeur Technique",
     "KPIs stratégiques, ROI prescriptif, simulation CAPEX vs OPEX et renouvellement de parc.",
     "pages/3_Antoine.py", "Ouvrir le tableau stratégique"),

    (c4, "🦺", "Leila",   "Responsable HSE",
     "Conformité ISO 45001, matrices de risques, EPI requis et génération des dossiers d'audit.",
     "pages/4_Leila.py", "Ouvrir l'espace HSE"),
]

for col, icon, name, role, desc, page_path, btn_label in agents:
    with col:
        st.markdown(f"""
        <div class="agent-card">
            <div class="agent-icon">{icon}</div>
            <div class="agent-name">{name}</div>
            <div class="agent-role">{role}</div>
            <div class="agent-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        st.page_link(page_path, label=f"➜ {btn_label}", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")
st.caption("ResilientFlow AI · Couche Prescriptive v1 · Machine surveillée : Pompe P-17 — Unité B")
