import streamlit as st

c_rul = st.session_state.get('c_rul', 72)

CONTEXTE_USINE = {
    "production": {"ordre_fabrication_actif": "OF-2026-89A", "ligne_concerne": "Ligne 2", "cout_arret_heure": 6500},
    "equipe": {"technicien_recommande": "Lionel (Habilité Mécanique/Hydraulique)", "technicien_secondaire": "Marc D."},
    "stocks": {"pieces_disponibles": "Joints d'étanchéité P17 (En stock : 2)"}
}

st.markdown("### 📋 Espace d'Arbitrage et Pilotage des Ressources — Sophie")

if c_rul <= 24:
    st.error("🚨 **ALERTE CRITIQUE POMPE P-17 : Arbitrage requis immédiatement**")
    c_prod, c_stock = st.columns(2)
    with c_prod:
        st.info(f"**Contexte de Production Actif :**\n\n• Ordre : {CONTEXTE_USINE['production']['ordre_fabrication_actif']}\n\n• Coût d'arrêt : {CONTEXTE_USINE['production']['cout_arret_heure']} €/h")
    with c_stock:
        st.warning(f"**Disponibilité Pièces :**\n\n{CONTEXTE_USINE['stocks']['pieces_disponibles']}")
else:
    st.success("✅ **Unité B nominale.** Aucun arbitrage requis.")
