import streamlit as st

# ── CONFIGURATION DE LA PAGE D'ACCUEIL ──────────────────────────────────────
st.set_page_config(
    page_title="ResilientFlow AI - Accueil",
    page_icon="⚙️",
    layout="wide"
)

# ── STYLE CSS GLOBAL ─────────────────────────────────────────────────────────
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
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
    .profile-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 24px 20px;
        text-align: center;
        transition: box-shadow 0.2s;
        height: 100%;
    }
    .profile-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.10);
    }
    .profile-icon {
        font-size: 2.8rem;
        margin-bottom: 10px;
    }
    .profile-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 4px;
    }
    .profile-role {
        font-size: 0.82rem;
        color: #64748b;
        margin-bottom: 14px;
    }
    .profile-desc {
        font-size: 0.80rem;
        color: #475569;
        line-height: 1.5;
        margin-bottom: 16px;
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        color: #002349;
        margin-bottom: 4px;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 24px;
    }
    .status-badge {
        display: inline-block;
        background-color: #dcfce7;
        color: #166534;
        border-radius: 20px;
        padding: 3px 14px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# ── EN-TÊTE ──────────────────────────────────────────────────────────────────
st.markdown("""
    <div class="escp-banner">
        🎓 <b>Projet de Fin d'Études ESCP</b> &nbsp;|&nbsp;
        ⚙️ Sujet : <i>Maintenance Prescriptive & Industrie 4.0</i>
    </div>
""", unsafe_allow_html=True)

col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown('<div class="hero-title">⚙️ ResilientFlow AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Tableau de bord prescriptif — Couche IA v1 · Pompe P-17, Unité B</div>', unsafe_allow_html=True)
with col_status:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<span class="status-badge">✅ Système opérationnel</span>', unsafe_allow_html=True)

st.markdown("---")

# ── DESCRIPTION ──────────────────────────────────────────────────────────────
st.markdown("### Sélectionnez votre espace de travail")
st.markdown(
    "Cette plateforme fournit une **vue adaptée à chaque métier** : de l'intervention terrain "
    "jusqu'à la décision stratégique, en passant par la planification et la conformité HSE."
)

st.markdown("<br>", unsafe_allow_html=True)

# ── CARTES DE PROFIL ─────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("""
        <div class="profile-card">
            <div class="profile-icon">🔧</div>
            <div class="profile-title">Lionel</div>
            <div class="profile-role">Technicien Terrain</div>
            <div class="profile-desc">
                Accès temps réel aux capteurs, RUL, courbes de tendance,
                scénarios de défaillance et fiches d'intervention GitHub.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_Lionel.py", label="➜ Ouvrir le terminal terrain", use_container_width=True)

with c2:
    st.markdown("""
        <div class="profile-card">
            <div class="profile-icon">📋</div>
            <div class="profile-title">Sophie</div>
            <div class="profile-role">Manager Maintenance</div>
            <div class="profile-desc">
                Arbitrage planification, gestion des ressources humaines,
                stocks de pièces et ordonnancement des interventions.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_Sophie.py", label="➜ Ouvrir l'espace d'arbitrage", use_container_width=True)

with c3:
    st.markdown("""
        <div class="profile-card">
            <div class="profile-icon">📊</div>
            <div class="profile-title">Antoine</div>
            <div class="profile-role">Directeur Technique</div>
            <div class="profile-desc">
                KPIs stratégiques, ROI de la couche prescriptive,
                simulation CAPEX vs OPEX et plan de renouvellement matériel.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/3_Antoine.py", label="➜ Ouvrir le tableau stratégique", use_container_width=True)

with c4:
    st.markdown("""
        <div class="profile-card">
            <div class="profile-icon">🛡️</div>
            <div class="profile-title">Leila</div>
            <div class="profile-role">Responsable HSE</div>
            <div class="profile-desc">
                Conformité ISO 45001, matrices de risques, EPI requis
                et génération automatique des dossiers d'audit réglementaire.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/4_Leila.py", label="➜ Ouvrir l'espace HSE", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ── PIED DE PAGE ─────────────────────────────────────────────────────────────
st.caption("ResilientFlow AI · Couche Prescriptive v1 · Machine surveillée : Pompe P-17 — Unité B")
