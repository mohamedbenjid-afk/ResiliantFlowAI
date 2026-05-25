import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time
import requests

# 1. Configuration de la page principale
st.set_page_config(page_title="ResilientFlow AI - Prescriptive Dashboard", layout="wide")

# ── CONFIGURATION DU RÉPERTOIRE GITHUB ──────────────────────────────────────
GITHUB_USER = "VOTRE_NOM_UTILISATEUR_GITHUB"
GITHUB_REPO = "maintenance-knowledge-base"
GITHUB_BRANCH = "main"

def get_github_file(path, is_json=False):
    url = "https://raw.githubusercontent.com/" + GITHUB_USER + "/" + GITHUB_REPO + "/" + GITHUB_BRANCH + "/" + path
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json() if is_json else response.text
        else:
            return None
    except Exception:
        return None

# ── STYLE CSS GLOBAL & SÉCURISÉ ─────────────────────────────────────────────
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    div[data-testid="stMetric"] {
        background-color: #fcfcfc !important;
        border: 1px solid #eeeeee !important;
        padding: 8px 15px !important;
        border-radius: 5px !important;
    }
    .threshold-label { color: #ef4444; font-size: 0.75rem; font-weight: bold; display: block; margin-top: -10px; margin-bottom: 5px; }
    .doc-box {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        padding: 15px;
        border-radius: 5px;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    /* Style pour la bannière académique */
    .escp-banner {
        background-color: #002349;
        color: #ffffff;
        padding: 10px;
        border-radius: 4px;
        text-align: center;
        margin-bottom: 15px;
        font-size: 0.85rem;
        border-left: 4px solid #d4af37;
    }
    </style>
""", unsafe_allow_html=True)

# ── DONNÉES DE CONTEXTE SIMULÉES (US-02 du Backlog) ─────────────────────────
CONTEXTE_USINE = {
    "production": {
        "ordre_fabrication_actif": "OF-2026-89A",
        "ligne_concerne": "Ligne 2",
        "cout_arret_heure": 6500
    },
    "equipe": {
        "technicien_recommande": "Lionel (Habilité Mécanique/Hydraulique - Charge : 32h/40h)",
        "technicien_secondaire": "Marc D. (Habilité Électricité - Surcharge : 39h/40h)"
    },
    "stocks": {
        "pieces_disponibles": "Joints d'étanchéité P17 (En stock : 2) | Roulements (Stock : 0 - Commande en cours)"
    }
}

# ── INITIALISATION DU SESSION STATE (MOTEUR DE SIMULATION) ──────────────────
if 'history' not in st.session_state:
    st.session_state.history = {"time": list(range(30)), "temp": [67.0]*30, "vib": [0.8]*30, "pres": [4.4]*30, "rul": [72.0]*30}
if 'base_temp' not in st.session_state: st.session_state.base_temp = 67.0
if 'base_vib' not in st.session_state: st.session_state.base_vib = 0.8
if 'base_pres' not in st.session_state: st.session_state.base_pres = 4.4
if 'base_cur' not in st.session_state: st.session_state.base_cur = 20.7
if 'tick' not in st.session_state: st.session_state.tick = 757
if 'running' not in st.session_state: st.session_state.running = True

# ── MISE À JOUR DES CAPTEURS ET CALCUL DU RUL (MOTEUR US-03) ────────────────
if st.session_state.running:
    st.session_state.tick += 1
    c_temp = st.session_state.base_temp + np.random.uniform(-0.5, 0.5)
    c_vib = max(0.1, st.session_state.base_vib + np.random.uniform(-0.05, 0.05))
    c_pres = max(0.1, st.session_state.base_pres + np.random.uniform(-0.05, 0.05))
    c_cur = max(0.0, st.session_state.base_cur + np.random.uniform(-0.2, 0.2))

    stress = max(0, (c_temp-60)/50 * 0.4 + (c_vib/5) * 0.3 + (c_pres/8) * 0.3)
    c_rul = max(0, int(72 * (1 - stress**1.2)))

    st.session_state.history["temp"].append(c_temp)
    st.session_state.history["vib"].append(c_vib)
    st.session_state.history["pres"].append(c_pres)
    st.session_state.history["rul"].append(c_rul)
    st.session_state.history["time"].append(st.session_state.tick)
    for k in st.session_state.history:
        if len(st.session_state.history[k]) > 30: st.session_state.history[k].pop(0)
else:
    c_temp = st.session_state.history["temp"][-1]
    c_vib = st.session_state.history["vib"][-1]
    c_pres = st.session_state.history["pres"][-1]
    c_cur = st.session_state.base_cur
    c_rul = st.session_state.history["rul"][-1]

r_status = "Nominal" if c_rul > 48 else ("Alerte" if c_rul > 24 else "Critique")
rul_percentage = float(max(0.0, min(1.0, c_rul / 72.0)))

# ── BARRE LATÉRALE : IDENTITÉ ESCP & NAVIGATION ─────────────────────────────
# Ajout du logo officiel ESCP Business School
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/e/e0/Logo_ESCP_Business_School.png", use_container_width=True)

# Ajout de la bannière académique de sujet de maintenance
st.sidebar.markdown("""
    <div class="escp-banner">
        🎓 <b>Projet de Fin d'Études ESCP</b><br>
        ⚙️ Spécialisation : <i>Maintenance Prescriptive & Industrie 4.0</i>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### ResilientFlow AI\n*Couche Prescriptive v1*")

profil = st.sidebar.selectbox(
    "👤 Sélectionner le profil utilisateur :",
    ["🔧 Lionel (Terrain)", "📋 Sophie (Manager)", "📊 Antoine (Directeur)", "🛡️ Leila (HSE)"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Contrôle du Flux Live**")
if st.sidebar.button("⏸️ Pause / ▶️ Reprendre", use_container_width=True):
    st.session_state.running = not st.session_state.running

st.sidebar.caption("Statut machine : Pompe P-17 (Unité B)")
st.sidebar.caption("Horodatage système : t = " + str(st.session_state.tick))
st.sidebar.caption("RUL estimé : " + str(c_rul) + " heures")

# ────────────────────────────────────────────────────────────────────────────
# 🔧 PROFIL 1 : LIONEL (TECHNICIEN TERRAIN)
# ────────────────────────────────────────────────────────────────────────────
if profil == "🔧 Lionel (Terrain)":
    st.markdown("### 🔧 Terminal Opérationnel de Terrain — Lionel")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TEMPÉRATURE", "{:.1f} °C".format(c_temp))
    m2.metric("VIBRATION", "{:.1f} mm/s".format(c_vib))
    m3.metric("PRESSION", "{:.1f} bar".format(c_pres))
    m4.metric("COURANT", "{:.1f} A".format(c_cur))
    
    st.markdown("---")
    
    col_l1, col_l2 = st.columns([3, 1])
    col_l1.markdown("**Durée de vie résiduelle (RUL) calculée**")
    col_l2.markdown("<p style='text-align: right; margin: 0;'><b>" + str(c_rul) + " h</b> (" + r_status + ")</p>", unsafe_allow_html=True)
    st.progress(rul_percentage)
    
    lbl1, lbl2, lbl3, lbl4 = st.columns([1, 1, 1, 1])
    lbl1.caption("0h (Panne)")
    lbl2.caption("⚠️ Seuil Agent : 24h")
    lbl3.caption("🔔 Alerte Seuil : 48h")
    lbl4.markdown("<p style='text-align: right; font-size: 0.8rem; color: gray; margin: 0;'>72h (Nominal)</p>", unsafe_allow_html=True)
    
    if c_rul <= 24:
        st.error("🚨 **ALERTE RESILIENTFLOW AI : INTERVENTION GUIDÉE DIRECTE (LIVE GITHUB)**")
        machine_info = get_github_file("data/POMPE_P17/info.json", is_json=True)
        if machine_info:
            st.caption("🤖 *Matériel identifié : " + machine_info.get("modele") + " | Zone : " + machine_info.get("emplacement") + "*")
        
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
            st.warning("ℹ️ Extraction automatique des fiches manuels techniques en cours (ou dépôt distant non configuré).")
    else:
        st.success("🤖 **Agent AI** : Surveillance en cours. Aucune ligne de procédure d'urgence requise à l'écran.")
        
    st.markdown("---")
    
    main_col_charts, main_col_sliders, main_col_scenarios = st.columns([2, 1, 1])
    
    with main_col_charts:
        st.markdown("##### 📈 Courbes de tendance")
        def plot_small(title, data, color, unit):
            fig = go.Figure(go.Scatter(x=st.session_state.history["time"], y=data, mode='lines', line=dict(color=color, width=2.5)))
            title_text = "<b>" + title + "</b> (" + "{:.1f}".format(data[-1]) + " " + unit + ")"
            fig.update_layout(title=title_text, height=110, margin=dict(l=0,r=0,t=25,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, showticklabels=False), yaxis=dict(showgrid=True, gridcolor='#f1f1f1'))
            return fig
        st.plotly_chart(plot_small("Température", st.session_state.history["temp"], "#ef4444", "°C"), use_container_width=True)
        st.plotly_chart(plot_small("Vibration", st.session_state.history["vib"], "#f59e0b", "mm/s"), use_container_width=True)
        st.plotly_chart(plot_small("Pression", st.session_state.history["pres"], "#3b82f6", "bar"), use_container_width=True)
        
    with main_col_sliders:
        st.markdown("##### ⌨️ Injection manuelle")
        st.session_state.base_temp = st.slider("Température", 60, 140, int(st.session_state.base_temp), label_visibility="collapsed")
        st.markdown("<span class='threshold-label'>Seuil : 110°C</span>", unsafe_allow_html=True)
        st.session_state.base_vib = st.slider("Vibration", 0.0, 8.0, float(st.session_state.base_vib), label_visibility="collapsed")
        st.markdown("<span class='threshold-label'>Seuil : 4.5 mm/s</span>", unsafe_allow_html=True)
        st.session_state.base_pres = st.slider("Pression", 0.0, 10.0, float(st.session_state.base_pres), label_visibility="collapsed")
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

# ────────────────────────────────────────────────────────────────────────────
# 📋 PROFIL 2 : SOPHIE (MANAGER MAINTENANCE)
# ────────────────────────────────────────────────────────────────────────────
elif profil == "📋 Sophie (Manager)":
    st.markdown("### 📋 Espace d'Arbitrage et Pilotage des Ressources — Sophie")
    st.markdown("*Résolution des conflits de planification (Equipes, Pièces détachées, Fenêtres de production).*")
    
    if c_rul <= 24:
        st.error("🚨 **ALERTE CRITIQUE POMPE P-17 : Arbitrage requis immédiatement**")
        
        c_prod, c_stock = st.columns(2)
        with c_prod:
            st.info("**Contexte de Production Actif :**\n\n• Ordre en cours : " + CONTEXTE_USINE["production"]["ordre_fabrication_actif"] + "\n\n• Ligne impactée : " + CONTEXTE_USINE["production"]["ligne_concerne"] + "\n\n• Coût d'arrêt horaire : " + str(CONTEXTE_USINE["production"]["cout_arret_heure"]) + " €/h")
        with c_stock:
            st.warning("**Disponibilité Pièces en Magasin :**\n\n" + CONTEXTE_USINE["stocks"]["pieces_disponibles"])
            
        st.markdown("---")
        
        st.markdown("#### 🔮 Simulateur d'impact sur la planification")
        action_planif = st.radio("Sélectionner une option d'ordonnancement :", [
            "🎯 Intervenir immédiatement (Arrêt court coordonné avec la prod)",
            "⏳ Reporter la maintenance à la fin de la semaine prochaine"
        ])
        
        if action_planif == "⏳ Reporter la maintenance à la fin de la semaine prochaine":
            st.markdown("<div style='background-color:#fef2f2; border-left:5px solid #ef4444; padding:15px; border-radius:4px;'>"
                        "❌ **RISQUE DE CASSE EN EXPLOITATION DIRECTE : 87%**<br>"
                        "Le RUL calculé par l'agent AI s'épuisera avant la date visée.<br>"
                        "<b>Perte de marge sèche projetée : 45 500 €</b> (7 heures d'arrêt non maîtrisé en plein pic de charge).</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background-color:#f0fdf4; border-left:5px solid #10b981; padding:15px; border-radius:4px;'>"
                        "✅ **STRATÉGIE SÉCURISÉE (Arbitrage validé par l'IA)**<br>"
                        "Arrêt planifié en période creuse. La production bascule automatiquement sur la ligne de secours.<br>"
                        "<b>Coût financier maîtrisé : 0 € de pénalités.</b></div>", unsafe_allow_html=True)
                        
        st.markdown("---")
        
        st.markdown("#### 👥 Gestion de la charge et assignation d'équipe")
        st.write("L'agent analyse les profils pour recommander le technicien disponible possédant le bon niveau d'accréditation.")
        st.success("👉 **Affectation optimale trouvée :** " + CONTEXTE_USINE["equipe"]["technicien_recommande"])
        st.caption("Alternative non retenue : " + CONTEXTE_USINE["equipe"]["technicien_secondaire"])
        
        if st.button("Confirmer l'affectation et envoyer l'ordre de travail", use_container_width=True):
            st.success("Ordre d'intervention généré. Fiche technique GitHub poussée sur le terminal terrain de Lionel.")
    else:
        st.success("✅ **Unité B nominale.** L'agent IA n'a détecté aucun goulot d'étranglement ni besoin d'arbitrage en urgence.")

# ────────────────────────────────────────────────────────────────────────────
# 📊 PROFIL 3 : ANTOINE (DIRECTEUR TECHNIQUE)
# ────────────────────────────────────────────────────────────────────────────
elif profil == "📊 Antoine (Directeur)":
    st.markdown("### 📊 Indicateurs Stratégiques et ROI Financement — Antoine")
    st.markdown("*Suivi consolidé de la performance industrielle et aide à la décision d'investissement (CAPEX vs OPEX).*")
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Pertes de production évitées", "312 000 €", delta="+14 alertes anticipées")
    k2.metric("Taux de Disponibilité (OEE)", "96.4 %", delta="+2.1 % vs Année N-1")
    k3.metric("ROI Couche Prescriptive", "7.6 x", delta="Target CODIR dépassée")
    
    st.markdown("---")
    
    st.markdown("#### 🔮 Analyse prédictive du plan de renouvellement matériel (Pompe P-17)")
    st.write("En croisant la vitesse d'usure calculée par le modèle RUL et l'augmentation de coût des rechanges, l'agent simule la meilleure décision financière.")
    
    col_strat, col_graph = st.columns([1, 2])
    with col_strat:
        mode_invest = st.selectbox("Simuler un scénario budgétaire :", [
            "Conserver la pompe P-17 (Continuer en maintenance prescriptive)",
            "Investir dans le remplacement par la pompe neuve AlphaFlow-18"
        ])
        st.info("**Avis de l'agent AI :** Bien que la couche prescriptive repousse la panne de la P-17, l'équipement approche de sa limite de fatigue structurelle.")
    
    with col_graph:
        fig_cap = go.Figure()
        timeline = ['Actuel', 'Année +1', 'Année +2', 'Année +3']
        if "Conserver" in mode_invest:
            fig_cap.add_trace(go.Scatter(x=timeline, y=[12000, 29000, 55000, 89000], name="Coût Opex Cumulé (Pièces + Maintenance)", line=dict(color='#f59e0b', width=3)))
            fig_cap.update_layout(title="Projection des dépenses cumulées (Subies en EUR)", height=200, margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig_cap, use_container_width=True)
            st.caption("🔴 **Alerte :** Explosion des coûts de rechange à partir de l'année +2 due à l'obsolescence.")
        else:
            fig_cap.add_trace(go.Scatter(x=timeline, y=[80000, 82000, 84000, 86000], name="Plan d'investissement Capex (Amorti)", line=dict(color='#10b981', width=3)))
            fig_cap.update_layout(title="Frais d'acquisition et intégration (EUR)", height=200, margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig_cap, use_container_width=True)
            st.caption("Gains validés : Point mort financier atteint dès le 14ème mois grâce au zéro-panne.")

# ────────────────────────────────────────────────────────────────────────────
# 🛡️ PROFIL 4 : LEILA (RESPONSABLE HSE)
# ────────────────────────────────────────────────────────────────────────────
elif profil == "🛡️ Leila (HSE)":
    st.markdown("### 🛡️ Conformité Réglementaire, Sécurité & Audit HSE — Leila")
    st.markdown("*Intégration native de la sécurité au cœur des interventions critiques et génération automatique de preuves d'audits.*")
    
    if c_rul <= 24:
        st.warning("⚡ **Protocole de Sécurité Automatique activé (Norme ISO 45001)**")
        st.markdown("#### 📋 Matrice des risques et dotation réglementaire requise")
        st.write("L'agent AI a analysé la signature de l'anomalie en cours et pousse automatiquement les exigences de sécurité adaptées :")
        
        if c_temp >= 110:
            st.markdown("🧱 **Risque Thermique Élevé (Surchauffe Stator) :**")
            st.markdown("- [ ] **EPI Obligatoire :** Gants isolants Haute Température (Norme EN 407).")
            st.markdown("- [ ] **Consigne :** Attendre le message de confirmation de baisse sous 45°C avant ouverture.")
        if c_vib >= 4.5:
            st.markdown("⚙️ **Risque Mécanique Élevé (Défaut Palier) :**")
            st.markdown("- [ ] **EPI Obligatoire :** Protection oculaire renforcée et casque anti-bruit (Vibrations acoustiques).")
            st.markdown("- [ ] **Consigne :** Vérifier l'ancrage et l'absence de micro-fissures sur le châssis.")
            
        st.markdown("🔒 **Procédure LOTO systématique :** Sectionneur d'alimentation cadenassé en cellule BT.")
    else:
        st.success("✅ **Zéro alerte active.** Les conditions de travail et la sécurité de l'Unité B sont au niveau nominal.")
        
    st.markdown("---")
    
    st.markdown("#### 📄 Registre réglementaire et Dossier de Preuve ISO 45001")
    st.write("La couche prescriptive enregistre de façon inaltérable que chaque technicien envoyé sur une anomalie a reçu les consignes et la liste d'EPI appropriés avant d'ouvrir sa boîte à outils.")
    
    if st.button("📥 Générer le dossier de conformité pour l'organisme de certification", use_container_width=True):
        st.success("Dossier de preuve réglementaire exporté avec succès sous la référence `RF_AUDIT_ISO45001_P17.pdf`.")
        st.caption("Statut : Horodatage certifié | Signature électronique de l'agent AI validée.")

# ── AUTO-REFRESH DE L'APPLICATION STREAMLIT ─────────────────────────────────
if st.session_state.running:
    time.sleep(1)
    st.rerun()
