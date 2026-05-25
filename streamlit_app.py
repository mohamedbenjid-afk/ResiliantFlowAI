# Mettez ce bloc juste après la section "Data Update" de votre code actuel

# ── BARRE LATÉRALE : SÉLECTION DU PROFIL (Navigation) ───────────────────────
st.sidebar.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
st.sidebar.markdown("### ResilientFlow AI\n*Couche Prescriptive*")

profil = st.sidebar.selectbox(
    "👤 Connecté en tant que :",
    ["🔧 Lionel (Terrain)", "📋 Sophie (Manager)", "📊 Antoine (Directeur)", "🛡️ Leila (HSE)"]
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Statut pompe : P-17 (Unité B)")
st.sidebar.caption(f"RUL actuel : {c_rul} heures")

# ── PROFIL 1 : LIONEL (Votre code actuel) ───────────────────────────────────
if profil == "🔧 Lionel (Terrain)":
    # Mettez ici TOUT votre code actuel : 
    # Top Metrics, RUL Bar Section, Courbes de tendance, Injection manuelle et Scénarios.
    st.info("💡 Mode Lionel actif : Visualisation des alertes et accès aux manuels GitHub.")


# ── PROFIL 2 : SOPHIE (Manager Maintenance — US-S1, US-S2) ──────────────────
elif profil == "📋 Sophie (Manager)":
    st.markdown("### 📋 Espace Pilotage & Arbitrage — Sophie")
    st.markdown("*Arbitrage priorisé des équipes, des pièces et des fenêtres d'arrêt.*")
    
    # Rappel de l'état critique si RUL <= 24
    if c_rul <= 24:
        st.error(f"🚨 **Urgence sur P-17 :** RUL critique ({c_rul}h). Une décision d'arbitrage est requise.")
        
        # US-S1 : Simulation d'impact / Report
        st.markdown("#### 🔮 Simulateur d'impact de planification")
        action = st.radio("Option de planification :", [
            "🎯 Intervenir immédiatement (Arrêt planifié)",
            "⏳ Repousser l'intervention à la fin de la semaine"
        ])
        
        if action == "⏳ Repousser l'intervention à la fin de la semaine":
            st.warning("⚠️ **Risque de casse : 87%** | Le RUL (Durée de vie résiduelle) sera épuisé avant la fenêtre demandée.")
            st.error("📉 **Perte financière estimée : 47 000 €** (Calculé sur la base d'un arrêt subit en plein pic de production).")
        else:
            st.success("✅ **Impact maîtrisé :** Coût d'arrêt minimisé (Production basculée sur la ligne B2). Pertes évitées : 47 000 €.")
            
        # US-S2 : Affectation dynamique du technicien selon charge et habilitation
        st.markdown("#### 👥 Affectation du personnel disponible")
        # Données simulées issues de la US-02 (Contexte simulé)
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.info("**Lionel**\n\n• Habilitation : Mécanique / Hydraulique\n\n• Charge hebdo : 32h/40h\n\n✅ **Recommandé pour P-17**")
            if st.button("Assigner Lionel", use_container_width=True):
                st.success("Ordre de travail envoyé sur le terminal de Lionel avec accès au dépôt GitHub.")
        with col_t2:
            st.warning("**Marc D.**\n\n• Habilitation : Électricité / Automatisme\n\n• Charge hebdo : 39h/40h\n\n❌ Charge trop élevée")
    else:
        st.success("✅ Toutes les machines de l'Unité B sont nominales. Aucune alerte en attente d'arbitrage.")


# ── PROFIL 3 : ANTOINE (Directeur Technique — US-A0, US-A2) ─────────────────
elif profil == "📊 Antoine (Directeur)":
    st.markdown("### 📊 Tableau de Bord Direction & ROI — Antoine")
    st.markdown("*Vision consolidée des risques d'usine, du ROI de l'IA et des budgets d'investissement.*")
    
    # US-A0 : Les 5 KPIs financiers et industriels clés (Chiffres du PPTX)
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Pertes de production évitées", "312 000 €", delta="+14 alertes anticipées")
    kpi2.metric("Disponibilité Globale (OEE)", "96.4 %", delta="+2.1 % vs Année N-1")
    kpi3.metric("ROI Couche Prescriptive", "7.6 x", delta="Objectif target atteint")

    st.markdown("---")
    
    # US-A2 : Simulateur de remplacement de l'équipement (Capex vs Opex)
    st.markdown("#### 🔮 Analyse de cycle de vie et plan de remplacement (P-17)")
    st.caption("L'analyse prescriptive croise l'historique d'usure pour conseiller la Direction sur le remplacement de l'actif.")
    
    col_an1, col_an2 = st.columns([1, 2])
    with col_an1:
        st.metric("Nombre de défaillances évitées", "4", help="Sur les 12 derniers mois")
        st.markdown("**Diagnostic de l'actif :** La pompe P-17 arrive en fin de cycle technologique. Bien que l'IA prolonge sa vie, le coût des pièces augmente.")
        choix_strategie = st.selectbox("Simuler une stratégie :", ["Conserver (Maintenance prescriptive)", "Remplacer par Modèle AlphaFlow-18"])
    
    with col_an2:
        # Graphique dynamique pour le CODIR
        fig_roi = go.Figure()
        annees = ['En cours', 'Année +1', 'Année +2', 'Année +3']
        if choix_strategie == "Conserver (Maintenance prescriptive)":
            coûts = [10000, 25000, 48000, 75000]
            fig_roi.add_trace(go.Scatter(x=annees, y=coûts, name="Coût de maintenance cumulé (Opex)", line=dict(color='#f59e0b', width=3)))
            st.plotly_chart(fig_roi, use_container_width=True)
            st.caption("🔴 Tendance : Augmentation des coûts de pièces détachées à partir de l'année +2.")
        else:
            coûts_remplacement = [80000, 83000, 86000, 89000]
            fig_roi.add_trace(go.Scatter(x=annees, y=coûts_remplacement, name="Investissement Nouvel Équipement (Capex)", line=dict(color='#10b981', width=3)))
            st.plotly_chart(fig_roi, use_container_width=True)
            st.caption("🟢 Équilibre financier atteint en 18 mois grâce à la suppression totale des micro-arrêts.")


# ── PROFIL 4 : LEILA (Responsable HSE — US-L1, US-L2) ────────────────────────
elif profil == "🛡️ Leila (HSE)":
    st.markdown("### 🛡️ Conformité Réglementaire & Sécurité HSE — Leila")
    st.markdown("*Génération automatique des preuves de conformité, traçabilité des risques et audits ISO 45001.*")
    
    if c_rul <= 24:
        st.warning("⚡ **Protocole de Sécurité Automatique déclenché (Alerte RUL < 24h)**")
        
        # US-L1 : Affichage dynamique des consignes de sécurité selon la nature du défaut détecté
        st.markdown("#### 📋 Matrice des risques de l'intervention en cours")
        
        if c_temp >= 110:
            st.markdown("🔴 **Risque Thermique Détecté (Surchauffe) :**")
            st.markdown("- [ ] **EPI Obligatoire :** Gants isolants de catégorie III (norme EN 407).")
            st.markdown("- [ ] **Procédure :** Attendre un refroidissement complet sous 45°C avant ouverture du carter.")
        if c_vib >= 4.5:
            st.markdown("🟠 **Risque Mécanique Détecté (Vibrations fortes) :**")
            st.markdown("- [ ] **EPI Obligatoire :** Lunettes de protection anti-projections et protection acoustique.")
            st.markdown("- [ ] **Procédure :** Vérification du serrage des boulons d'ancrage.")
            
        st.markdown("- [ ] **Consignation Électrique (LOTO) :** Sectionneur cadenassé en cellule basse tension.")
    else:
        st.success("🤖 Système nominal. Aucune procédure d'urgence active à valider.")
        
    st.markdown("---")
    
    # US-L2 : Génération de dossier d'audit ISO 45001
    st.markdown("#### 📄 Registre de conformité et Rapport d'Audit ISO 45001")
    st.write("Le système ResilientFlow AI enregistre chaque action prescriptive, prouvant qu'aucun technicien n'est envoyé sur une machine en panne sans ses EPI réglementaires.")
    
    if st.button("📥 Exporter le dossier d'audit réglementaire (12 derniers mois)"):
        st.success("Le dossier de conformité `Rapport_ISO45001_Pompe_P17.pdf` a été généré avec succès. Horodatage blockchain d'usine validé.")
