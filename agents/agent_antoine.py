"""
agents/agent_antoine.py — Agent stratégique d'Antoine (Directeur Technique)
Rôle : analyser les tendances de fiabilité, calculer le ROI de la maintenance
       prescriptive, modéliser les décisions CAPEX vs OPEX.

Intégration dans pages/3_Antoine.py :
    from agents.agent_antoine import run_agent_antoine
    analyse = run_agent_antoine(equipement="Pompe P-17")
"""

import os, json
import requests as _requests

import sys, os as _os
sys.path.append(_os.path.join(_os.path.dirname(__file__), '..'))
from llm_client import chat as _llm_chat


def _get_secret(key):
    try:
        import streamlit as st
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, "")


# ── CLIENT NOTION via requests ────────────────────────────────────────────────
def _notion_query(database_id: str, filter_obj: dict = None, sorts: list = None) -> list:
    token = _get_secret("NOTION_TOKEN")
    url   = f"https://api.notion.com/v1/databases/{database_id}/query"
    headers = {
        "Authorization":  f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type":   "application/json",
    }
    payload = {}
    if filter_obj: payload["filter"] = filter_obj
    if sorts:      payload["sorts"]  = sorts

    results, has_more, cursor = [], True, None
    while has_more:
        if cursor:
            payload["start_cursor"] = cursor
        resp = _requests.post(url, headers=headers, json=payload, timeout=15)
        if not resp.ok:
            return []
        data = resp.json()
        results.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        cursor   = data.get("next_cursor")
    return results


# ── IDs des bases Notion ResilientFlow ───────────────────────────────────────
DB_MACHINES   = "5279cb2a42b54b42936e22313521f825"   # Machines & équipements
DB_ORDRES_FAB = "d7ee45dab07943c1bda09a6b47089202"   # Ordres de fabrication
DB_HISTORIQUE = "6f53558bfbee455891efa53b6536d892"   # Historique & plan de maintenance
DB_PIECES     = "c22138baa8ca4806b19403108735bc68"   # Pièces détachées


# ── HELPERS ───────────────────────────────────────────────────────────────────
def _text(prop):
    if not prop: return ""
    t = prop.get("type")
    if t == "title":        return "".join(r["plain_text"] for r in prop.get("title", []))
    if t == "rich_text":    return "".join(r["plain_text"] for r in prop.get("rich_text", []))
    if t == "select":       s = prop.get("select"); return s["name"] if s else ""
    if t == "multi_select": return ", ".join(o["name"] for o in prop.get("multi_select", []))
    if t == "number":       v = prop.get("number"); return v if v is not None else ""
    if t == "date":         d = prop.get("date"); return d["start"] if d else ""
    return ""

def _num(prop) -> float:
    v = _text(prop)
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0

def _p(page): return page.get("properties", {})


# ── OUTILS STRATÉGIQUES ────────────────────────────────────────────────────────

def get_bilan_equipement(nom: str) -> dict:
    """État de dégradation et données de fiabilité pour évaluer un remplacement CAPEX."""
    res = _notion_query(
        DB_MACHINES,
        filter_obj={"property": "Nom Machine", "title": {"contains": nom}}
    )
    if not res:
        return {"erreur": f"'{nom}' non trouvé dans la base machines"}
    p = _p(res[0])
    rul_jours    = _num(p.get("RUL (jours)"))
    score_deg    = _num(p.get("Score dégradation (%)"))
    return {
        "machine":               _text(p.get("Nom Machine")),
        "id_machine":            _text(p.get("ID Machine")),
        "type":                  _text(p.get("Type")),
        "statut":                _text(p.get("Statut")),
        "rul_jours":             rul_jours,
        "score_degradation_pct": score_deg,
        "vie_restante_pct":      round(100 - score_deg, 1),
        "temperature_actuelle":  _text(p.get("Température actuelle (°C)")),
        "vibration_actuelle":    _text(p.get("Vibration actuelle (mm/s)")),
        "seuil_temp":            _text(p.get("Seuil température (°C)")),
        "seuil_vib":             _text(p.get("Seuil vibration (mm/s)")),
        "unite":                 _text(p.get("Unité / Zone")),
        "responsable":           _text(p.get("Responsable")),
        "derniere_inspection":   _text(p.get("Dernière inspection")),
        "prochaine_maintenance": _text(p.get("Prochaine maintenance")),
        "notes_ia":              _text(p.get("Notes IA")),
    }


def get_historique_couts_maintenance(equipement: str) -> dict:
    """Coûts cumulés de maintenance et tendance — pour calculer le point mort CAPEX."""
    res = _notion_query(
        DB_HISTORIQUE,
        filter_obj={"property": "Machine", "rich_text": {"contains": equipement}},
        sorts=[{"property": "Date intervention", "direction": "descending"}]
    )
    toutes, terminees, prescriptives = [], [], []
    cout_total   = 0.0
    cout_arrets  = 0.0

    for page in res:
        p      = _p(page)
        statut = _text(p.get("Statut"))
        type_  = _text(p.get("Type"))
        cout   = _num(p.get("Coût intervention (€)"))
        arret  = _num(p.get("Coût arrêt production (€)"))
        entry  = {
            "titre":           _text(p.get("Titre intervention")),
            "type":            type_,
            "statut":          statut,
            "date":            _text(p.get("Date intervention")),
            "duree_estimee_h": _text(p.get("Durée estimée (h)")),
            "duree_reelle_h":  _text(p.get("Durée réelle (h)")),
            "cout_eur":        cout,
            "cout_arret_eur":  arret,
            "rul_avant":       _text(p.get("RUL avant intervention (j)")),
            "rul_apres":       _text(p.get("RUL après intervention (j)")),
        }
        toutes.append(entry)
        if statut == "Terminée":
            terminees.append(entry)
            cout_total  += cout
            cout_arrets += arret
            if type_ == "Maintenance prescriptive":
                prescriptives.append(entry)

    roi = round(cout_arrets / cout_total, 1) if cout_total > 0 else 0

    return {
        "nb_interventions":       len(toutes),
        "nb_terminees":           len(terminees),
        "nb_prescriptives":       len(prescriptives),
        "cout_total_maintenance": round(cout_total, 2),
        "couts_arrets_evites":    round(cout_arrets, 2),
        "roi_maintenance":        roi,
        "detail_interventions":   toutes[:10],  # 10 plus récentes
    }


def get_exposition_financiere_production(equipement: str) -> dict:
    """Coût d'exposition totale si la machine tombe en panne non planifiée."""
    res = _notion_query(
        DB_ORDRES_FAB,
        filter_obj={"property": "Machine impactée", "rich_text": {"contains": equipement}}
    )
    exposition_totale = 0.0
    details = []
    for page in res:
        p       = _p(page)
        cout    = _num(p.get("Coût arrêt (€)"))
        duree_h = _num(p.get("Durée arrêt (h)"))
        qte_p   = _num(p.get("Quantité prévue"))
        qte_r   = _num(p.get("Quantité réalisée"))
        pct     = round((qte_r / qte_p * 100) if qte_p else 0, 1)
        exposition_totale += cout
        details.append({
            "reference":      _text(p.get("Référence OF")),
            "statut":         _text(p.get("Statut OF")),
            "produit":        _text(p.get("Produit")),
            "ligne":          _text(p.get("Ligne de production")),
            "avancement_pct": pct,
            "cout_arret_eur": cout,
            "duree_arret_h":  duree_h,
            "impact_rul":     _text(p.get("Impact RUL")),
            "date_fin":       _text(p.get("Date fin prévue")),
        })

    return {
        "exposition_financiere_totale_eur": round(exposition_totale, 2),
        "nb_of_impactes": len(details),
        "of_impactes":    details,
    }


def get_etat_stock_strategique(equipement: str) -> dict:
    """Valeur immobilisée en stock + pièces critiques — vision trésorerie."""
    res = _notion_query(
        DB_PIECES,
        filter_obj={"property": "Machine concernée", "rich_text": {"contains": equipement}}
    )
    valeur_stock = 0.0
    pieces = []
    for page in res:
        p       = _p(page)
        stock   = _num(p.get("Stock actuel"))
        prix    = _num(p.get("Prix unitaire (€)"))
        valeur  = round(stock * prix, 2)
        statut  = _text(p.get("Statut stock"))
        valeur_stock += valeur
        pieces.append({
            "designation":     _text(p.get("Désignation pièce")),
            "reference":       _text(p.get("Référence")),
            "categorie":       _text(p.get("Catégorie")),
            "stock":           stock,
            "stock_minimum":   _text(p.get("Stock minimum")),
            "prix_unitaire":   prix,
            "valeur_immobilisee": valeur,
            "statut_stock":    statut,
            "fournisseur":     _text(p.get("Fournisseur")),
            "delai_livraison": _text(p.get("Délai livraison (j)")),
        })

    return {
        "valeur_stock_immobilisee_eur": round(valeur_stock, 2),
        "nb_references":       len(pieces),
        "pieces_en_rupture":   [p for p in pieces if p["statut_stock"] == "Rupture"],
        "pieces_alerte":       [p for p in pieces if "Alerte" in p["statut_stock"]],
        "detail_stock":        pieces,
    }


# ── OUTILS DÉCLARÉS À L'AGENT ─────────────────────────────────────────────────
TOOLS = [
    {
        "name": "get_bilan_equipement",
        "description": "Récupère le bilan de vie de l'équipement : RUL, score de dégradation, vie restante estimée. Permet d'évaluer si un remplacement CAPEX est justifié.",
        "input_schema": {"type": "object", "properties": {"nom": {"type": "string"}}, "required": ["nom"]}
    },
    {
        "name": "get_historique_couts_maintenance",
        "description": "Calcule les coûts cumulés de maintenance (réalisés), le ROI de la maintenance prescriptive et la tendance des coûts. Clé pour comparaison CAPEX vs OPEX.",
        "input_schema": {"type": "object", "properties": {"equipement": {"type": "string"}}, "required": ["equipement"]}
    },
    {
        "name": "get_exposition_financiere_production",
        "description": "Estime l'exposition financière totale en cas de panne non planifiée sur tous les OF actifs. Quantifie le risque résiduel production.",
        "input_schema": {"type": "object", "properties": {"equipement": {"type": "string"}}, "required": ["equipement"]}
    },
    {
        "name": "get_etat_stock_strategique",
        "description": "Analyse la valeur immobilisée en stock de pièces détachées et identifie les ruptures. Vision trésorerie et risque approvisionnement.",
        "input_schema": {"type": "object", "properties": {"equipement": {"type": "string"}}, "required": ["equipement"]}
    }
]


def _execute(name, inputs):
    if name == "get_bilan_equipement":                 return get_bilan_equipement(inputs["nom"])
    if name == "get_historique_couts_maintenance":     return get_historique_couts_maintenance(inputs["equipement"])
    if name == "get_exposition_financiere_production": return get_exposition_financiere_production(inputs["equipement"])
    if name == "get_etat_stock_strategique":           return get_etat_stock_strategique(inputs["equipement"])
    return {"erreur": f"Outil inconnu : {name}"}


# ── PROMPT SYSTÈME ────────────────────────────────────────────────────────────
SYSTEM = """Tu es l'assistant stratégique d'Antoine, Directeur Technique.
Tu analyses les données de fiabilité industrielle pour l'aider à prendre
des décisions d'investissement et de politique de maintenance.

Ton rôle : transformer les données terrain en indicateurs de pilotage,
comparer les scénarios CAPEX vs OPEX et quantifier le ROI de la maintenance prescriptive.

Format de réponse attendu :
1. **Synthèse exécutive** : 3 lignes max, chiffres clés
2. **Analyse OPEX** : coûts de maintenance cumulés, ROI prescriptif, tendance
3. **Analyse CAPEX** : justification ou non du remplacement avec point mort financier
4. **Exposition au risque** : perte financière estimée en cas de panne non maîtrisée
5. **Recommandation CODIR** : décision à présenter avec justification chiffrée

Sois synthétique et chiffré. Antoine parle au CODIR, pas à un technicien.
"""


# ── FONCTION PRINCIPALE ───────────────────────────────────────────────────────
def run_agent_antoine(equipement: str = "Pompe P-17", c_rul: int = None) -> str:
    """
    Lance l'agent Antoine pour une analyse stratégique d'un équipement.
    Retourne l'analyse ROI/CAPEX en texte Markdown.
    """
    rul_info = f"\n- RUL actuel estimé : {c_rul}j" if c_rul else ""
    situation = (
        f"ANALYSE STRATÉGIQUE — {equipement}{rul_info}\n\n"
        f"Réalise une analyse complète CAPEX vs OPEX pour cet équipement : "
        f"état de dégradation, coûts de maintenance cumulés, exposition financière production, "
        f"état du stock. Calcule le ROI et formule une recommandation pour le CODIR."
    )

    messages = [{"role": "user", "content": situation}]
    while True:
        resp = _llm_chat(system=SYSTEM, messages=messages, tools=TOOLS, max_tokens=2000)
        if resp.stop_reason == "end_turn":
            return resp.final_text()
        if resp.stop_reason == "tool_use":
            results = []
            for tc in resp.tool_calls():
                out = _execute(tc["name"], tc["input"])
                results.append({"type": "tool_result", "tool_use_id": tc.get("id", "tc0"),
                                "content": json.dumps(out, ensure_ascii=False)})
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user",      "content": results})


# ── TEST STANDALONE ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(run_agent_antoine(equipement="Pompe P-17", c_rul=18))
