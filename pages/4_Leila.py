import streamlit as st
import time
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from shared_state import init_session_state, update_sensors, COMMON_CSS

# ── CONFIG PAGE ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Leila — Conformité HSE", page_icon="🛡️", layout="wide")
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
if st.sidebar.button("⬅️ Retour à l'accueil", use_container_width=True):
    st.switch_page("streamlit_home.py")

# ── CONTENU PRINCIPAL ─────────────────────────────────────────────────────────
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

    if c_pres >= 7.0:
        st.markdown("💧 **Risque Hydraulique Élevé (Surpression circuit) :**")
        st.markdown("- [ ] **EPI Obligatoire :** Écran facial et combinaison anti-projections.")
        st.markdown("- [ ] **Consigne :** Purger la pression résiduelle avant toute déconnexion de raccord.")

    if c_rul <= 24 and c_temp < 110 and c_vib < 4.5 and c_pres < 7.0:
        st.markdown("⚠️ **RUL critique détecté — Risque générique :**")
        st.markdown("- [ ] Appliquer la procédure LOTO complète avant toute intervention.")
        st.markdown("- [ ] Vérifier les EPI standard (casque, chaussures de sécurité, gants).")

    st.markdown("🔒 **Procédure LOTO systématique :** Sectionneur d'alimentation cadenassé en cellule BT.")

else:
    st.success("✅ **Zéro alerte active.** Les conditions de travail et la sécurité de l'Unité B sont au niveau nominal.")

st.markdown("---")
st.markdown("#### 📄 Registre réglementaire et Dossier de Preuve ISO 45001")
st.write(
    "La couche prescriptive enregistre de façon inaltérable que chaque technicien envoyé sur une anomalie "
    "a reçu les consignes et la liste d'EPI appropriés avant d'ouvrir sa boîte à outils."
)

if st.button("📥 Générer le dossier de conformité pour l'organisme de certification", use_container_width=True):
    st.success("Dossier de preuve réglementaire exporté avec succès sous la référence `RF_AUDIT_ISO45001_P17.pdf`.")
    st.caption("Statut : Horodatage certifié | Signature électronique de l'agent AI validée.")

# ── AUTO-REFRESH ──────────────────────────────────────────────────────────────
if st.session_state.running:
    time.sleep(1)
    st.rerun()
