import streamlit as st

c_rul = st.session_state.get('c_rul', 72)
c_temp = st.session_state.get('c_temp', 67.0)

st.markdown("### 🛡️ Conformité Réglementaire, Sécurité & Audit HSE — Leila")

if c_rul <= 24:
    st.warning("⚡ **Protocole de Sécurité Automatique activé (Norme ISO 45001)**")
    if c_temp >= 110:
        st.markdown("🧱 **Risque Thermique Élevé (Surchauffe) :**")
        st.markdown("- [ ] **EPI Obligatoire :** Gants isolants (Norme EN 407).")
else:
    st.success("✅ **Zéro alerte active.** Conditions de travail conformes.")
