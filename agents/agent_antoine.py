"""
agents/agent_antoine.py — Agent stratégique d'Antoine (Directeur Technique)
Rôle : analyser les tendances de fiabilité, calculer le ROI de la maintenance
       prescriptive, modéliser les décisions CAPEX vs OPEX.

Intégration dans pages/3_Antoine.py :
    from agents.agent_antoine import run_agent_antoine
    analyse = run_agent_antoine(equipement="Pompe P-17")
"""

import os, json
from notion_client import Client
import sys, os as _os
sys.path.append(_os.path.join(_os.path.dirname(__file__), '..'))
from llm_client import chat as _llm_chat

def _get_secret(key):
    try:
        import streamlit as st
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, "")

_notion = Client(auth=_get_secret("NOTION_TOKEN"))

DB_OF          = "6777a9e0-4c76-49ca-a3d4-fb20a579cb2d"
DB_MAINTENANCE = "1c9d8c5d-e394-490a-b913-e0cf833abb5b"
DB_STOCK       = "7229437a-027a-440f-a7be-5e37157f3b8d"
DB_EQUIPEMENTS = "f8c546b6-40b6-484c-b686-6a6ad42520ee"


# ── HELPERS ───────────────────────────────────────────────────────────────────
def _text(prop):
    if not prop: return ""
    t = prop.get("type")
    if t == "title":        return "".join(r["plain_text"] for r in prop.get("title", []))
    if t == "rich_text":    return "".join(r["plain_text"] for r in prop.get("rich_text", []))
    if t == "select":       s = prop.get("select"); return s["name"] if s else ""
    if t == "multi_select": return ", ".join(o["name"] for o in prop.get("multi_select", []))
    if t == "number":       return prop.get("number")
    if t == "date":         d = prop.get("date"); return d["start"] if d else ""
    return ""

def _p(page): return page.get("properties", {})


# ── OUTILS STRATÉGIQUES (ce dont Antoine a besoin pour décider) ───────────────

def get_bilan_equipement(nom: str) -> dict:
    """Données d'usure et de vie restante pour évaluer la pertinence d'un remplacement."""
    res = _notion.databases.query(
        database_id=DB_EQUIPEMENTS,
        filter={"property": "Équipement", "title": {"contains": nom}}
    )
    if not res["results"]: return {"erreur": f"'{nom}' non trouvé"}
    p = _p(res["results"][0])
    heures      = float(_text(p.get("Heures de fonctionnement total")) or 0)
    rul_nominal = float(_text(p.get("RUL nominal (h)")) or 72)
    return {
        "equipement":        _text(p.get("Équipement")),
        "statut":            _text(p.get("Statut")),
        "fabricant":         _text(p.get("Fabricant")),
        "modele":            _text(p.get("Modèle")),
        "mise_en_service":   _text(p.get("Date de mise en service")),
        "heures_total":      heures,
        "rul_nominal_h":     rul_nominal,
        "taux_usure_pct":    round(min(100, heures / (rul_nominal * 100) * 100), 1),
        "notes":             _text(p.get("Notes")),
    }

def get_historique_couts_maintenance(equipement: str) -> dict:
    """Coûts cumulés de maintenance et tendance — pour calculer le point mort CAPEX."""
    res = _notion.databases.query(
        database_id=DB_MAINTENANCE,
        filter={"property": "Équipement", "rich_text": {"contains": equipement}},
    )
    toutes, realisees = [], []
    cout_total_realise = 0
    cout_total_planifie = 0
    for page in res["results"]:
        p = _p(page)
        statut = _text(p.get("Statut"))
        cout   = float(_text(p.get("Coût estimé (€)")) or 0)
        entry  = {
            "intervention":   _text(p.get("Intervention")),
            "type":           _text(p.get("Type d'intervention")),
            "statut":         statut,
            "priorite":       _text(p.get("Priorité")),
            "date":           _text(p.get("Date planifiée")) or _text(p.get("Date réalisée")),
            "duree_h":        _text(p.get("Durée estimée (h)")),
            "cout_estime":    cout,
        }
        toutes.append(entry)
        if statut == "Réalisée":
            realisees.append(entry)
            cout_total_realise += cout
        else:
            cout_total_planifie += cout

    return {
        "nb_interventions_total":    len(toutes),
        "nb_interventions_realisees": len(realisees),
        "cout_total_realise_eur":    cout_total_realise,
        "cout_total_planifie_eur":   cout_total_planifie,
        "cout_total_cumule_eur":     cout_total_realise + cout_total_planifie,
        "detail_interventions":      toutes,
    }

def get_exposition_financiere_production(equipement: str) -> dict:
    """Coût d'exposition totale si la machine tombe en panne non planifiée (tous OF impactés)."""
    res = _notion.databases.query(
        database_id=DB_OF,
        filter={"property": "Équipement concerné", "rich_text": {"contains": equipement}}
    )
    exposition_totale = 0
    details = []
    for page in res["results"]:
        p = _p(page)
        cout_h = float(_text(p.get("Coût arrêt horaire (€)")) or 0)
        qte_c  = float(_text(p.get("Quantité cible"))   or 0)
        qte_r  = float(_text(p.get("Quantité réalisée")) or 0)
        pct    = round((qte_r / qte_c * 100) if qte_c else 0, 1)
        # Estimation : 7h d'arrêt non planifié en moyenne
        perte_estimee = cout_h * 7
        exposition_totale += perte_estimee
        details.append({
            "of":             _text(p.get("Ordre de Fabrication")),
            "statut":         _text(p.get("Statut")),
            "avancement_pct": pct,
            "cout_arret_h":   cout_h,
            "perte_7h":       perte_estimee,
            "ligne_secours":  _text(p.get("Ligne de secours disponible")),
        })
    return {
        "exposition_financiere_totale_eur": exposition_totale,
        "hypothese": "Arrêt non planifié de 7h en pic de charge",
        "of_impactes": details,
    }

def get_etat_stock_strategique(equipement: str) -> dict:
    """Valeur immobilisée en stock + pièces critiques manquantes — vision trésorerie."""
    res = _notion.databases.query(
        database_id=DB_STOCK,
        filter={"property": "Équipements compatibles", "rich_text": {"contains": equipement}}
    )
    valeur_stock = 0
    pieces = []
    for page in res["results"]:
        p = _p(page)
        stock = float(_text(p.get("Stock actuel")) or 0)
        prix  = float(_text(p.get("Prix unitaire (€)")) or 0)
        valeur_stock += stock * prix
        pieces.append({
            "composant":    _text(p.get("Composant")),
            "stock":        stock,
            "prix_u":       prix,
            "valeur_immo":  round(stock * prix, 2),
            "statut":       _text(p.get("Statut stock")),
            "critique":     _text(p.get("Critique")),
            "delai_reappro":_text(p.get("Délai réappro (jours)")),
        })
    return {
        "valeur_stock_immobilisee_eur": round(valeur_stock, 2),
        "nb_references":                len(pieces),
        "pieces_en_rupture":            [p for p in pieces if p["statut"] == "Rupture"],
        "pieces_alerte":                [p for p in pieces if "Alerte" in p["statut"]],
        "detail_stock":                 pieces,
    }


# ── OUTILS DÉCLARÉS À L'AGENT ─────────────────────────────────────────────────
TOOLS = [
    {
        "name": "get_bilan_equipement",
        "description": "Récupère le bilan de vie de l'équipement : âge, heures de fonctionnement, taux d'usure estimé. Permet d'évaluer si un remplacement CAPEX est justifié.",
        "input_schema": {"type": "object", "properties": {"nom": {"type": "string"}}, "required": ["nom"]}
    },
    {
        "name": "get_historique_couts_maintenance",
        "description": "Calcule les coûts cumulés de maintenance (réalisés + planifiés). Clé pour le calcul du ROI et la comparaison CAPEX vs OPEX.",
        "input_schema": {"type": "object", "properties": {"equipement": {"type": "string"}}, "required": ["equipement"]}
    },
    {
        "name": "get_exposition_financiere_production",
        "description": "Estime l'exposition financière totale en cas de panne non planifiée : perte de production sur tous les OF actifs. Quantifie le risque résiduel.",
        "input_schema": {"type": "object", "properties": {"equipement": {"type": "string"}}, "required": ["equipement"]}
    },
    {
        "name": "get_etat_stock_strategique",
        "description": "Analyse la valeur immobilisée en stock de pièces détachées et identifie les pièces critiques manquantes. Vision trésorerie et risque approvisionnement.",
        "input_schema": {"type": "object", "properties": {"equipement": {"type": "string"}}, "required": ["equipement"]}
    }
]

def _execute(name, inputs):
    if name == "get_bilan_equipement":                  return get_bilan_equipement(inputs["nom"])
    if name == "get_historique_couts_maintenance":      return get_historique_couts_maintenance(inputs["equipement"])
    if name == "get_exposition_financiere_production":  return get_exposition_financiere_production(inputs["equipement"])
    if name == "get_etat_stock_strategique":            return get_etat_stock_strategique(inputs["equipement"])
    return {"erreur": f"Outil inconnu : {name}"}


# ── PROMPT SYSTÈME ────────────────────────────────────────────────────────────
SYSTEM = """Tu es l'assistant stratégique d'Antoine, Directeur Technique.
Tu analyses les données de fiabilité industrielle pour l'aider à prendre
des décisions d'investissement et de politique de maintenance.

Ton rôle : transformer les données terrain en indicateurs de pilotage,
comparer les scénarios CAPEX vs OPEX et quantifier le ROI de la maintenance prescriptive.

Format de réponse attendu :
1. **Synthèse exécutive** : 3 lignes max, chiffres clés
2. **Analyse OPEX** : coûts de maintenance cumulés et trajectoire
3. **Analyse CAPEX** : justification ou non du remplacement avec point mort financier
4. **Exposition au risque** : perte financière estimée en cas de panne non maîtrisée
5. **Recommandation CODIR** : décision à présenter avec justification chiffrée

Sois synthétique et chiffré. Antoine parle au CODIR, pas à un technicien.
"""


# ── FONCTION PRINCIPALE (appelée depuis pages/3_Antoine.py) ──────────────────
def run_agent_antoine(equipement: str = "Pompe P-17", c_rul: int = None) -> str:
    """
    Lance l'agent Antoine pour une analyse stratégique d'un équipement.
    Retourne l'analyse ROI/CAPEX en texte Markdown.
    """
    rul_info = f"\n- RUL actuel estimé : {c_rul}h" if c_rul else ""
    situation = (
        f"ANALYSE STRATÉGIQUE — {equipement}{rul_info}\n\n"
        f"Réalise une analyse complète CAPEX vs OPEX pour cet équipement : "
        f"coûts de maintenance cumulés, exposition financière production, "
        f"état du stock. Formule une recommandation pour le CODIR."
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
