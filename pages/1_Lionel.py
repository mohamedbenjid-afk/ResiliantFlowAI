# pages/1_Lionel.py
# Agent Lionel — Technicien Terrain
# K0 Surveillance · K1 Briefing · K2 Procédure · K3 Post-intervention · K4 Arbitrage

import time
import datetime

import plotly.graph_objects as go
import streamlit as st

import notion_client as nc
from agents.agent_lionel import run_agent_lionel
from shared_state import COMMON_CSS, init_session_state, update_sensors

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Lionel — Terrain", page_icon="🔧", layout="wide")
st.markdown(COMMON_CSS, unsafe_allow_html=True)

# ── BANNIÈRE ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="escp-banner">
    🎓 <b>Projet de Fin d'Études ESCP</b> &nbsp;|&nbsp;
    ⚙️ Sujet : <i>Maintenance Prescriptive &amp; Industrie 4.0</i>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.page_link("streamlit_home.py", label="← Retour à l'accueil", use_container_width=True)
    st.markdown("---")
    st.markdown("### 🔧 Lionel — Technicien Terrain")
    st.caption("Machine surveillée : **Pompe P-17** — Unité B")
    st.markdown("---")

    init_session_state()
    running_label = "⏸ Pause simulation" if st.session_state.running else "▶ Reprendre"
    if st.button(running_label, use_container_width=True):
        st.session_state.running = not st.session_state.running
        st.rerun()

    st.markdown("---")
    st.markdown("**Paramètres de simulation**")
    st.session_state.base_temp = st.slider("Température de base (°C)", 55.0, 85.0,
                                           float(st.session_state.base_temp), 0.5)
    st.session_state.base_vib  = st.slider("Vibration de base (mm/s)", 0.1, 4.0,
                                           float(st.session_state.base_vib), 0.05)
    st.session_state.base_pres = st.slider("Pression de base (bar)", 0.5, 7.0,
                                           float(st.session_state.base_pres), 0.1)

    st.markdown("---")
    st.markdown("**Scénarios**")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("🔥 Surchauffe", use_container_width=True):
            st.session_state.base_temp = 82.0
            st.session_state.base_vib  = 3.5
    with col_s2:
        if st.button("✅ Normal", use_container_width=True):
            st.session_state.base_temp = 67.0
            st.session_state.base_vib  = 0.8
            st.session_state.base_pres = 4.4

# ── SENSOR DATA ───────────────────────────────────────────────────────────────
c_temp, c_vib, c_pres, c_cur, c_rul, r_status, rul_pct = update_sensors()

STATUS_COLOR = {"Nominal": "#166534", "Alerte": "#b45309", "Critique": "#b91c1c"}
STATUS_BG    = {"Nominal": "#dcfce7", "Alerte": "#fef3c7", "Critique": "#fee2e2"}

# ── TABS ──────────────────────────────────────────────────────────────────────
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "📡 K0 — Surveillance",
    "📋 K1 — Briefing",
    "📘 K2 — Procédure",
    "📝 K3 — Post-intervention",
    "⚖️ K4 — Arbitrage",
])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 0 — K0 SURVEILLANCE
# ════════════════════════════════════════════════════════════════════════════════
with tab0:
    st.markdown("## 📡 Surveillance temps réel — Pompe P-17")

    # KPI metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🌡 Température", f"{c_temp:.1f} °C",
              delta=f"{c_temp - 67:.1f}",
              delta_color="inverse" if c_temp > 75 else "normal")
    m2.metric("📳 Vibration", f"{c_vib:.2f} mm/s",
              delta=f"{c_vib - 0.8:.2f}",
              delta_color="inverse" if c_vib > 2.5 else "normal")
    m3.metric("💧 Pression", f"{c_pres:.2f} bar",
              delta=f"{c_pres - 4.4:.2f}")
    m4.metric("⚡ Courant", f"{c_cur:.1f} A")

    # RUL
    st.markdown("---")
    rul_col, status_col = st.columns([3, 1])
    with rul_col:
        st.markdown(f"### ⏱ RUL estimé : **{c_rul} jours**")
        st.progress(rul_pct)
        if c_rul <= 60:
            st.markdown(
                f'<span class="threshold-label">⚠️ Seuil opérationnel franchi — intervention recommandée</span>',
                unsafe_allow_html=True,
            )
    with status_col:
        st.markdown(
            f'<div style="background:{STATUS_BG[r_status]};color:{STATUS_COLOR[r_status]};'
            f'border-radius:8px;padding:16px;text-align:center;font-weight:700;font-size:1.1rem;">'
            f'{r_status}</div>',
            unsafe_allow_html=True,
        )

    # AI agent when critical (RUL ≤ 5 j = scénario surchauffe)
    # L'agent est appelé UNE SEULE FOIS à l'entrée en état critique, puis mis en cache
    if c_rul <= 5:
        if st.session_state.get("_agent_status") != "Critique":
            with st.spinner("🤖 Analyse IA en cours..."):
                st.session_state["_agent_reco"] = run_agent_lionel(c_temp, c_vib, c_pres, c_rul)
            st.session_state["_agent_status"] = "Critique"

        with st.expander("🤖 Recommandation IA — Agent Lionel", expanded=True):
            st.markdown(st.session_state.get("_agent_reco", ""))
            if st.button("🔄 Nouvelle analyse", key="btn_refresh_agent"):
                with st.spinner("Analyse en cours..."):
                    st.session_state["_agent_reco"] = run_agent_lionel(c_temp, c_vib, c_pres, c_rul)
                st.rerun()
    else:
        # Réinitialise le cache quand on quitte l'état critique
        st.session_state.pop("_agent_status", None)
        st.session_state.pop("_agent_reco", None)

    # Trend charts
    st.markdown("---")
    st.markdown("### 📈 Tendances (30 dernières mesures)")
    hist = st.session_state.history

    ch1, ch2, ch3 = st.columns(3)
    for col, key, label, color, fill_color, unit in [
        (ch1, "temp", "Température", "#ef4444", "rgba(239,68,68,0.15)",   "°C"),
        (ch2, "vib",  "Vibration",   "#f59e0b", "rgba(245,158,11,0.15)",  "mm/s"),
        (ch3, "rul",  "RUL",         "#3b82f6", "rgba(59,130,246,0.15)",  "j"),
    ]:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(hist["time"]), y=list(hist[key]),
            mode="lines", line=dict(color=color, width=2), fill="tozeroy",
            fillcolor=fill_color,
        ))
        fig.update_layout(
            title=dict(text=f"{label} ({unit})", font=dict(size=13)),
            margin=dict(l=0, r=0, t=30, b=0),
            height=180,
            xaxis=dict(showticklabels=False),
            paper_bgcolor="white", plot_bgcolor="white",
        )
        col.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — K1 BRIEFING
# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## 📋 Briefing du quart")

    # Machines en alerte
    st.markdown("### 🚨 État du parc machines")
    try:
        machines = nc.get_machines()
        if machines:
            for m in machines:
                nom   = m.get("nom", "?")
                mid   = m.get("id", "")
                # Pour P-17 : utilise le RUL et statut du simulateur (K0) pour cohérence
                if "P-17" in mid or "P-17" in nom:
                    rul    = c_rul
                    statut = r_status
                else:
                    rul    = m.get("rul_jours") or 0
                    statut = m.get("statut") or "Inconnu"
                # Couleurs selon statuts ESCP réels
                if statut == "Critique" or rul <= 2:
                    bg, border, icon = "#fee2e2", "#ef4444", "🔴"
                elif statut == "Alerte" or rul <= 20:
                    bg, border, icon = "#fef3c7", "#f59e0b", "🟠"
                elif statut == "Hors service":
                    bg, border, icon = "#f3f4f6", "#6b7280", "⚫"
                else:
                    bg, border, icon = "#f0fdf4", "#86efac", "🟢"
                st.markdown(
                    f'<div style="background:{bg};border-left:4px solid {border};'
                    f'border-radius:6px;padding:12px;margin-bottom:8px;">'
                    f'{icon} <b>{nom}</b> ({mid}) — '
                    f'RUL : <b>{rul} j</b> &nbsp;|&nbsp; Statut : <b>{statut}</b>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("Aucune machine trouvée dans Notion.")
    except Exception as e:
        st.warning(f"Impossible de charger les machines : {e}")
        # Fallback data
        st.markdown("""
        | Machine | RUL | Statut |
        |---|---|---|
        | Pompe P-17 | 18 j | 🔴 Alerte critique |
        | Compresseur C-03 | 45 j | 🟡 Alerte |
        | Convoyeur CV-01 | 72 j | 🟢 Nominal |
        """)

    # Interventions planifiées
    st.markdown("---")
    st.markdown("### 🗓 Interventions planifiées")
    try:
        planifiees = nc.get_historique(statut="Planifiée")
        if planifiees:
            for i in planifiees:
                st.markdown(
                    f'<div class="doc-box"><b>{i["titre"]}</b><br>'
                    f'Machine : {i["machine"]} &nbsp;|&nbsp; Date : {i["date"] or "TBD"} &nbsp;|&nbsp; '
                    f'Technicien : {i["technicien"]}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("Aucune intervention planifiée.")
    except Exception:
        st.warning("Données Notion indisponibles — affichage de secours.")
        st.markdown("""
        | Titre | Machine | Date | Technicien |
        |---|---|---|---|
        | Remplacement joint P-17 | Pompe P-17 | 2026-06-18 | Lionel |
        | Inspection C-03 | Compresseur C-03 | 2026-06-20 | Marc D. |
        """)

    # Équipe & disponibilité
    col_e, col_p = st.columns(2)
    with col_e:
        st.markdown("### 👥 Équipe disponible")
        try:
            equipe = nc.get_equipe()
            if equipe:
                for tech in equipe:
                    dispo = tech.get("disponibilite") or "Inconnu"
                    color = "#166534" if dispo == "Disponible" else (
                            "#b45309" if dispo == "Partiellement disponible" else "#b91c1c")
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:10px;'
                        f'padding:8px;border-radius:6px;background:#f8fafc;margin-bottom:6px;">'
                        f'<span style="color:{color};font-size:1.2rem;">●</span>'
                        f'<span><b>{tech.get("prenom","")} {tech.get("nom","")}</b><br>'
                        f'<small>{tech.get("role","")} — {tech.get("heures_restantes") or "?"} h restantes</small>'
                        f'</span></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("Aucun technicien trouvé.")
        except Exception:
            st.warning("Données équipe indisponibles.")
            data_equipe = [
                ("Lionel B.", "Mécanique/Hydraulique", "8h", "Disponible", "#166534"),
                ("Marc D.", "Électricité", "1h", "Chargé", "#b91c1c"),
                ("Fatima R.", "Automatisme", "5h", "Disponible", "#166534"),
            ]
            for nom, spec, h, dispo, color in data_equipe:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px;padding:8px;'
                    f'border-radius:6px;background:#f8fafc;margin-bottom:6px;">'
                    f'<span style="color:{color};font-size:1.2rem;">●</span>'
                    f'<span><b>{nom}</b> — {spec}<br><small>{dispo} — {h} restantes</small>'
                    f'</span></div>',
                    unsafe_allow_html=True,
                )

    with col_p:
        st.markdown("### 🔩 Stock pièces P-17")
        try:
            pieces = nc.get_pieces(machine_id="P-17")
            if pieces:
                for p in pieces:
                    stock = p.get("stock_actuel") or 0
                    mini  = p.get("stock_minimum") or 1
                    statut_s = p.get("statut_stock") or ("En stock" if stock >= mini else "Rupture")
                    color = "#166534" if stock >= mini else "#b91c1c"
                    icon  = "✅" if stock >= mini else "❌"
                    st.markdown(
                        f'{icon} **{p.get("designation","?")}** — '
                        f'<span style="color:{color}">Stock : {stock}</span> '
                        f'(min {mini})',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("Aucune pièce P-17 trouvée.")
        except Exception:
            st.warning("Stock indisponible.")
            pieces_fallback = [
                ("Joints d'étanchéité P17", 2, 1, True),
                ("Roulements 6205-2RS",     0, 2, False),
                ("Garnitures mécaniques",   3, 1, True),
                ("Filtre hydraulique FH-17", 1, 1, True),
            ]
            for nom, stock, mini, ok in pieces_fallback:
                icon = "✅" if ok else "❌"
                color = "#166534" if ok else "#b91c1c"
                st.markdown(
                    f'{icon} **{nom}** — <span style="color:{color}">Stock : {stock}</span> (min {mini})',
                    unsafe_allow_html=True,
                )

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — K2 PROCÉDURE
# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## 📘 Procédure d'intervention — Pompe P-17")

    # Détection type d'anomalie depuis capteurs
    if c_temp > 75:
        anomalie = "Surchauffe"
    elif c_vib > 2.5:
        anomalie = "Vibration excessive"
    elif c_pres < 2.0:
        anomalie = "Pression insuffisante"
    else:
        anomalie = "Usure normale"

    st.info(f"**Anomalie détectée :** {anomalie} — RUL : {c_rul} j — Statut : {r_status}")

    # Documents HSE depuis Notion
    with st.expander("📄 Documents HSE associés à P-17", expanded=False):
        try:
            docs = nc.get_docs_hse(machine_id="P-17", persona="Lionel - Technicien")
            if docs:
                for d in docs:
                    epi_list = ", ".join(d.get("epi") or []) or "Non spécifié"
                    st.markdown(
                        f'<div class="doc-box"><b>{d["titre"]}</b> '
                        f'({d.get("type","")}) — v{d.get("version","?")} — '
                        f'Risque : {d.get("niveau_risque","")}<br>'
                        f'EPI : {epi_list}<br>'
                        f'<small>{d.get("resume","")}</small></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("Aucun document HSE spécifique à P-17 trouvé dans Notion.")
        except Exception:
            st.warning("Documents HSE indisponibles.")

    st.markdown("---")
    st.markdown("### ✅ Checklist LOTO / EPI / Intervention")

    # Initialiser les étapes si besoin
    CHECKLIST_STEPS = [
        # Phase 0 — Préparation & EPI
        ("phase", "🦺 Phase 1 — Préparation & EPI"),
        ("step",  "Mettre les EPI : casque, gants anti-coupure, lunettes, chaussures de sécurité"),
        ("step",  "Récupérer le kit d'intervention P-17 au magasin (casier B-07)"),
        ("step",  "Vérifier la disponibilité des pièces requises en stock"),
        ("step",  "Informer le manager Sophie de l'arrêt planifié"),
        # Phase 1 — LOTO
        ("phase", "🔒 Phase 2 — Consignation LOTO"),
        ("step",  "Isoler l'alimentation électrique (disjoncteur Q-17A) et apposer cadenas rouge"),
        ("step",  "Fermer les vannes d'isolement amont V-17A et aval V-17B"),
        ("step",  "Purger la pression résiduelle via le point de test PT-17"),
        ("step",  "Apposer la plaque de consignation et notifier le poste de contrôle"),
        # Phase 2 — Intervention
        ("phase", "🔧 Phase 3 — Intervention mécanique"),
        ("step",  "Déposer le carter avant (4 vis M12, clé 19)"),
        ("step",  "Extraire le roulement défectueux avec l'extracteur hydraulique"),
        ("step",  "Nettoyer le logement et vérifier l'état de l'arbre"),
        ("step",  "Monter le nouveau roulement (graissage préalable Mobilux EP2)"),
        ("step",  "Remonter le carter et vérifier le couple de serrage (45 N·m)"),
        # Phase 3 — Remise en service
        ("phase", "✅ Phase 4 — Remise en service"),
        ("step",  "Retirer les consignations LOTO et informer le poste de contrôle"),
        ("step",  "Démarrage progressif et surveillance 15 min (temp, vib, pression)"),
        ("step",  "Valider les paramètres : T < 70 °C, vib < 1.5 mm/s, P > 3.5 bar"),
    ]

    if "checklist_steps" not in st.session_state:
        st.session_state["checklist_steps"] = [False] * sum(
            1 for kind, _ in CHECKLIST_STEPS if kind == "step"
        )

    checked_total = sum(st.session_state["checklist_steps"])
    step_total    = len(st.session_state["checklist_steps"])
    step_idx      = 0

    for kind, label in CHECKLIST_STEPS:
        if kind == "phase":
            st.markdown(f"**{label}**")
        else:
            checked = st.checkbox(
                label, value=st.session_state["checklist_steps"][step_idx],
                key=f"chk_{step_idx}"
            )
            st.session_state["checklist_steps"][step_idx] = checked
            step_idx += 1

    st.markdown("---")
    pct_done = checked_total / step_total if step_total else 0
    st.progress(pct_done, text=f"{checked_total}/{step_total} étapes validées")

    col_r, col_d = st.columns([1, 3])
    with col_r:
        if st.button("🔄 Réinitialiser", use_container_width=True):
            st.session_state["checklist_steps"] = [False] * step_total
            st.rerun()
    with col_d:
        if pct_done == 1.0:
            st.success("✅ Procédure complète — passez à l'onglet **K3 Post-intervention**")

# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — K3 POST-INTERVENTION
# ════════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## 📝 Rapport post-intervention")

    if st.session_state.get("k3_submitted"):
        st.success("✅ Rapport déjà soumis pour cette session.")
        if st.button("📋 Soumettre un nouveau rapport"):
            st.session_state["k3_submitted"] = False
            st.rerun()
    else:
        with st.form("form_post_intervention", clear_on_submit=False):
            st.markdown("### Informations générales")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                f_machine = st.selectbox(
                    "Machine concernée",
                    ["Pompe P-17 (P-17)", "Compresseur C-03", "Convoyeur CV-01", "Autre"],
                    index=0,
                )
                f_date = st.date_input("Date de l'intervention", value=datetime.date.today())
                f_technicien = st.text_input("Technicien(s)", value="Lionel B.")
            with col_f2:
                f_type = st.selectbox(
                    "Type d'intervention",
                    ["Maintenance prescriptive", "Panne corrective",
                     "Maintenance préventive", "Inspection", "Remplacement planifié"],
                )
                f_statut = st.selectbox(
                    "Statut",
                    ["Terminée", "En cours", "En attente pièces", "Annulée"],
                )
                f_duree = st.number_input("Durée réelle (h)", min_value=0.0, step=0.5, value=2.0)

            st.markdown("### Détail de l'intervention")
            f_actions = st.text_area(
                "Actions réalisées",
                placeholder="Ex: Remplacement du roulement 6205-2RS, nettoyage du logement, regraissage...",
                height=100,
            )
            f_pieces = st.text_area(
                "Pièces remplacées",
                placeholder="Ex: 1x Roulement 6205-2RS, 2x Joint torique Ø52...",
                height=70,
            )

            st.markdown("### Analyse & coûts")
            col_f3, col_f4 = st.columns(2)
            with col_f3:
                f_cause = st.selectbox(
                    "Cause racine",
                    ["Usure normale", "Surcharge", "Défaut lubrification",
                     "Corrosion", "Vibration excessive", "Surchauffe", "Inconnu"],
                )
                f_cout = st.number_input("Coût intervention (€)", min_value=0.0, step=50.0, value=350.0)
            with col_f4:
                f_rul_avant = st.number_input("RUL avant intervention (j)", min_value=0, step=1, value=int(c_rul))
                f_observations = st.text_area("Observations / remarques", height=68)

            submitted = st.form_submit_button(
                "📤 Enregistrer dans Notion", use_container_width=True, type="primary"
            )

        if submitted:
            machine_label = f_machine.split("(")[0].strip()
            machine_id    = f_machine.split("(")[-1].rstrip(")") if "(" in f_machine else f_machine
            payload = {
                "titre":       f"Intervention {machine_id} — {f_date.isoformat()}",
                "machine":     machine_label,
                "type":        f_type,
                "statut":      f_statut,
                "technicien":  f_technicien,
                "date":        f_date.isoformat(),
                "duree_reelle": f_duree,
                "actions":     f_actions,
                "pieces":      f_pieces,
                "cause_racine": f_cause,
                "cout":        f_cout,
                "rul_avant":   f_rul_avant,
                "observations": f_observations,
            }
            try:
                with st.spinner("Enregistrement dans Notion..."):
                    nc.create_intervention(payload)
                    # Invalide le cache historique
                    nc.get_historique.clear()
                st.session_state["k3_submitted"] = True
                st.balloons()
                st.success("✅ Rapport enregistré dans la base Historique Maintenance Notion !")
            except Exception as e:
                st.error(f"Erreur Notion : {e}")
                st.info("💡 Vérifiez que le token NOTION_TOKEN est configuré dans les secrets Streamlit.")

# ════════════════════════════════════════════════════════════════════════════════
# TAB 4 — K4 ARBITRAGE
# ════════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## ⚖️ Arbitrage multi-machine")
    st.caption("Aide à la décision : quelle machine traiter en priorité ?")

    # Dégradation simulée selon le statut du simulateur (pour P-17)
    _DEG_BY_STATUS = {"Critique": 88, "Alerte": 45, "Nominal": 8}

    def score_alerte(machine: dict) -> float:
        """Calcule un score d'urgence 0–100 (100 = urgence maximale)."""
        rul  = machine.get("rul_jours") or 72
        deg  = machine.get("score_degradation") or 0
        rul_score = max(0, (1 - rul / 72)) * 60
        deg_score = (deg / 100) * 40
        return round(rul_score + deg_score, 1)

    try:
        all_machines = nc.get_machines()
        if not all_machines:
            raise ValueError("Aucune machine Notion")
    except Exception:
        # Fallback — données fictives représentatives
        all_machines = [
            {"id": "P-17",  "nom": "Pompe P-17",         "statut": "Alerte",
             "rul_jours": 18, "score_degradation": 45, "temperature": 77.2, "vibration": 2.8,
             "unite": "Unité B", "responsable": "Lionel Dumont"},
            {"id": "C-03",  "nom": "Compresseur C-03",   "statut": "Alerte",
             "rul_jours": 20, "score_degradation": 38, "temperature": 65.1, "vibration": 1.4,
             "unite": "Ligne 1", "responsable": "Marc Lefebvre"},
            {"id": "M-08",  "nom": "Moteur M-08",        "statut": "Nominal",
             "rul_jours": 100, "score_degradation": 8, "temperature": 52.0, "vibration": 0.6,
             "unite": "Ligne 2", "responsable": "Marc Lefebvre"},
        ]

    # ── Aligner P-17 avec le simulateur (K0) ──────────────────────────────────
    # Le simulateur est la source de vérité pour P-17.
    # On écrase les valeurs statiques Notion avec les valeurs temps réel.
    for m in all_machines:
        if "P-17" in (m.get("id") or "") or "P-17" in (m.get("nom") or ""):
            m["rul_jours"]        = c_rul
            m["statut"]           = r_status
            m["temperature"]      = c_temp
            m["vibration"]        = c_vib
            m["score_degradation"] = _DEG_BY_STATUS.get(r_status, 20)
    # ──────────────────────────────────────────────────────────────────────────

    # Trier par score décroissant et prendre les 2 premières
    ranked = sorted(all_machines, key=score_alerte, reverse=True)
    top2   = ranked[:2] if len(ranked) >= 2 else ranked

    # Affichage comparatif
    if len(top2) >= 2:
        m_a, m_b = top2[0], top2[1]
        score_a, score_b = score_alerte(m_a), score_alerte(m_b)

        col_a, col_mid, col_b = st.columns([2, 1, 2])
        for col, m, score in [(col_a, m_a, score_a), (col_b, m_b, score_b)]:
            statut_m = m.get("statut") or "Nominal"
            if statut_m == "Critique" or score >= 60:
                bg, score_color, badge = "#fee2e2", "#b91c1c", "🔴 Critique"
            elif statut_m == "Alerte" or score >= 30:
                bg, score_color, badge = "#fef3c7", "#b45309", "🟠 Alerte"
            else:
                bg, score_color, badge = "#f0fdf4", "#166534", "🟢 Nominal"
            with col:
                st.markdown(
                    f'<div style="background:{bg};border-radius:10px;padding:20px;text-align:center;">'
                    f'<div style="font-size:1.3rem;font-weight:700;">{m.get("nom","?")}</div>'
                    f'<div style="color:#64748b;">{m.get("id","")} — {m.get("unite","")}</div>'
                    f'<div style="font-size:0.8rem;margin-top:4px;">{badge}</div>'
                    f'<hr style="margin:10px 0;">'
                    f'<div style="font-size:2rem;font-weight:800;color:{score_color};">'
                    f'{score}<span style="font-size:1rem;">/100</span></div>'
                    f'<div style="font-size:0.82rem;color:#475569;">Score urgence</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("")
                st.markdown(f"**RUL :** {m.get('rul_jours','?')} j")
                st.markdown(f"**Dégradation :** {m.get('score_degradation', 0)} %")
                st.markdown(f"**Statut :** {statut_m}")
                st.markdown(f"**Température :** {m.get('temperature') or '—'} °C")
                st.markdown(f"**Vibration :** {m.get('vibration') or '—'} mm/s")
                st.markdown(f"**Responsable :** {m.get('responsable','?')}")

        with col_mid:
            st.markdown("<br><br><br><br>", unsafe_allow_html=True)
            st.markdown(
                '<div style="text-align:center;font-size:2rem;color:#94a3b8;">VS</div>',
                unsafe_allow_html=True,
            )

        # Recommandation
        st.markdown("---")
        winner = m_a if score_a >= score_b else m_b
        delta  = abs(score_a - score_b)
        if delta >= 20:
            st.error(
                f"🔴 **Intervention prioritaire : {winner.get('nom')}** — Score d'urgence {score_alerte(winner)}/100. "
                f"Différence significative ({delta:.0f} pts) : traitement immédiat recommandé."
            )
        elif delta >= 8:
            st.warning(
                f"🟡 **Privilégier : {winner.get('nom')}** — Score d'urgence légèrement supérieur ({delta:.0f} pts). "
                f"Concertez-vous avec Sophie pour la planification."
            )
        else:
            st.info(
                f"🔵 **Scores proches** ({delta:.0f} pts d'écart). Consultez Sophie (Manager) pour arbitrer "
                f"selon les contraintes de production et disponibilité équipe."
            )

        # Graphique comparatif
        st.markdown("---")
        st.markdown("### 📊 Comparaison des indicateurs")
        indicators = ["Score urgence", "Dégradation (%)", "Température (°C/100)", "Vibration (×10)"]
        vals_a = [
            score_a,
            m_a.get("score_degradation") or 0,
            (m_a.get("temperature") or 0) / 100 * 100,
            (m_a.get("vibration") or 0) * 10,
        ]
        vals_b = [
            score_b,
            m_b.get("score_degradation") or 0,
            (m_b.get("temperature") or 0) / 100 * 100,
            (m_b.get("vibration") or 0) * 10,
        ]

        fig = go.Figure(data=[
            go.Bar(name=m_a.get("nom","M1"), x=indicators, y=vals_a,
                   marker_color="#ef4444", opacity=0.85),
            go.Bar(name=m_b.get("nom","M2"), x=indicators, y=vals_b,
                   marker_color="#3b82f6", opacity=0.85),
        ])
        fig.update_layout(
            barmode="group",
            legend=dict(orientation="h", y=1.1),
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(l=0, r=0, t=30, b=0),
            height=300,
        )
        st.plotly_chart(fig, use_container_width=True)

    elif len(top2) == 1:
        st.info(f"Une seule machine disponible : **{top2[0].get('nom')}** — Score {score_alerte(top2[0])}/100.")
    else:
        st.warning("Aucune machine à comparer.")

    # Toutes les machines
    with st.expander("📋 Classement complet du parc", expanded=False):
        for i, m in enumerate(ranked, 1):
            score = score_alerte(m)
            icon = "🔴" if score >= 60 else ("🟡" if score >= 30 else "🟢")
            st.markdown(f"{i}. {icon} **{m.get('nom')}** — Score {score}/100 — RUL {m.get('rul_jours','?')} j")

# ── AUTO-REFRESH (K0 seulement) ───────────────────────────────────────────────
if st.session_state.running:
    time.sleep(1)
    st.rerun()
