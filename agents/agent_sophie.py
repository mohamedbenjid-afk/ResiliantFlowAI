"""
agents/agent_sophie.py — Agent d'arbitrage de Sophie (Manager Maintenance)
Rôle : évaluer l'impact production d'une alerte, arbitrer entre intervention
       immédiate et report, optimiser l'assignation des techniciens.

Intégration dans pages/2_Sophie.py :
    from agents.agent_sophie import run_agent_sophie
    arbitrage = run_agent_sophie(c_rul, equipement="Pompe P-17")
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


# ── OUTILS PLANIFICATION (ce dont Sophie a besoin pour arbitrer) ──────────────

def get_impact_production(equipement: str) -> dict:
    """OF en cours + OF planifiés sur cet équipement avec coût d'arrêt et ligne de secours."""
    res = _notion.databases.query(
        database_id=DB_OF,
        filter={"property": "Équipement concerné", "rich_text": {"contains": equipement}},
        sorts=[{"property": "Statut", "direction": "ascending"}]
    )
    of_en_cours, of_planifies = [], []
    for page in res["results"]:
        p = _p(page)
        entry = {
            "of":              _text(p.get("Ordre de Fabrication")),
            "statut":          _text(p.get("Statut")),
            "produit":         _text(p.get("Produit fabriqué")),
            "qte_cible":       _text(p.get("Quantité cible")),
            "qte_realisee":    _text(p.get("Quantité réalisée")),
            "cout_arret_h":    _text(p.get("Coût arrêt horaire (€)")),
            "ligne_secours":   _text(p.get("Ligne de secours disponible")),
            "date_fin_prevue": _text(p.get("Date fin prévue")),
            "responsable":     _text(p.get("Responsable OF")),
        }
        if _text(p.get("Statut")) == "En cours":
            of_en_cours.append(entry)
        else:
            of_planifies.append(entry)
    return {
        "of_en_cours":  of_en_cours  or [{"info": "Aucun OF en cours"}],
        "of_planifies": of_planifies or [{"info": "Aucun OF planifié"}],
        "total_of":     len(res["results"]),
    }

def get_charge_techniciens(equipement: str) -> list:
    """Liste des techniciens assignés aux interventions planifiées — pour détecter les surcharges."""
    res = _notion.databases.query(
        database_id=DB_MAINTENANCE,
        filter={"and": [
            {"property": "Équipement", "rich_text": {"contains": equipement}},
            {"property": "Statut",     "select":    {"not_equals": "Réalisée"}}
        ]}
    )
    techniciens = {}
    for page in res["results"]:
        p = _p(page)
        tech   = _text(p.get("Technicien assigné")) or "Non assigné"
        duree  = float(_text(p.get("Durée estimée (h)")) or 0)
        statut = _text(p.get("Statut"))
        if tech not in techniciens:
            techniciens[tech] = {"technicien": tech, "interventions": [], "charge_totale_h": 0}
        techniciens[tech]["interventions"].append({
            "intervention": _text(p.get("Intervention")),
            "priorite":     _text(p.get("Priorité")),
            "date":         _text(p.get("Date planifiée")),
            "duree_h":      duree,
            "statut":       statut,
        })
        techniciens[tech]["charge_totale_h"] += duree
    return list(techniciens.values()) or [{"info": "Aucune intervention planifiée"}]

def get_fenetre_maintenance(equipement: str) -> list:
    """Toutes les interventions planifiées avec leurs dates — pour trouver un créneau d'arrêt optimal."""
    res = _notion.databases.query(
        database_id=DB_MAINTENANCE,
        filter={"and": [
            {"property": "Équipement", "rich_text": {"contains": equipement}},
            {"property": "Statut",     "select":    {"equals": "Planifiée"}}
        ]},
        sorts=[{"property": "Date planifiée", "direction": "ascending"}]
    )
    return [
        {
            "intervention":   _text(_p(p).get("Intervention")),
            "priorite":       _text(_p(p).get("Priorité")),
            "date_planifiee": _text(_p(p).get("Date planifiée")),
            "duree_h":        _text(_p(p).get("Durée estimée (h)")),
            "technicien":     _text(_p(p).get("Technicien assigné")),
            "cout_estime":    _text(_p(p).get("Coût estimé (€)")),
        }
        for p in res["results"]
    ] or [{"info": "Aucune fenêtre planifiée"}]

def get_pieces_critiques_manquantes(equipement: str) -> list:
    """Pièces en rupture ou stock bas qui bloqueraient une intervention immédiate."""
    res = _notion.databases.query(
        database_id=DB_STOCK,
        filter={"and": [
            {"property": "Équipements compatibles", "rich_text": {"contains": equipement}},
            {"property": "Statut stock", "select": {"does_not_equal": "OK"}}
        ]}
    )
    return [
        {
            "composant":     _text(_p(p).get("Composant")),
            "statut_stock":  _text(_p(p).get("Statut stock")),
            "stock_actuel":  _text(_p(p).get("Stock actuel")),
            "delai_reappro": _text(_p(p).get("Délai réappro (jours)")),
            "critique":      _text(_p(p).get("Critique")),
            "notes":         _text(_p(p).get("Notes")),
        }
        for p in res["results"]
    ] or [{"info": "Aucune pièce critique manquante — stock OK pour intervention"}]


# ── OUTILS DÉCLARÉS À L'AGENT ─────────────────────────────────────────────────
TOOLS = [
    {
        "name": "get_impact_production",
        "description": "Récupère les OF en cours et planifiés sur cet équipement : coût d'arrêt horaire, ligne de secours disponible, dates de fin prévues. Permet d'évaluer le risque financier d'un arrêt.",
        "input_schema": {"type": "object", "properties": {"equipement": {"type": "string"}}, "required": ["equipement"]}
    },
    {
        "name": "get_charge_techniciens",
        "description": "Analyse la charge de travail de chaque technicien sur les interventions planifiées. Permet de détecter les surcharges et d'optimiser l'assignation.",
        "input_schema": {"type": "object", "properties": {"equipement": {"type": "string"}}, "required": ["equipement"]}
    },
    {
        "name": "get_fenetre_maintenance",
        "description": "Liste toutes les interventions planifiées avec leurs dates et durées. Permet de trouver un créneau d'arrêt optimal qui minimise l'impact sur la production.",
        "input_schema": {"type": "object", "properties": {"equipement": {"type": "string"}}, "required": ["equipement"]}
    },
    {
        "name": "get_pieces_critiques_manquantes",
        "description": "Identifie les pièces en rupture de stock ou en commande qui pourraient bloquer une intervention immédiate. Essentiel pour l'arbitrage du timing.",
        "input_schema": {"type": "object", "properties": {"equipement": {"type": "string"}}, "required": ["equipement"]}
    }
]

def _execute(name, inputs):
    if name == "get_impact_production":          return get_impact_production(inputs["equipement"])
    if name == "get_charge_techniciens":         return get_charge_techniciens(inputs["equipement"])
    if name == "get_fenetre_maintenance":        return get_fenetre_maintenance(inputs["equipement"])
    if name == "get_pieces_critiques_manquantes":return get_pieces_critiques_manquantes(inputs["equipement"])
    return {"erreur": f"Outil inconnu : {name}"}


# ── PROMPT SYSTÈME ────────────────────────────────────────────────────────────
SYSTEM = """Tu es l'assistant de Sophie, Manager Maintenance de l'Unité B.
Tu analyses les alertes machine pour l'aider à prendre des décisions de planification.

Ton rôle : arbitrer entre intervention immédiate et report, en tenant compte de :
- L'impact sur la production en cours (OF actifs, coût d'arrêt)
- La disponibilité des techniciens et leur charge
- La disponibilité des pièces nécessaires
- Les fenêtres de maintenance déjà planifiées

Format de réponse attendu :
1. **Situation** : résumé de l'alerte et des contraintes identifiées
2. **Option A — Intervention immédiate** : avantages, risques, coût estimé
3. **Option B — Report planifié** : date suggérée, conditions requises, risque RUL
4. **Recommandation** : quelle option privilégier et pourquoi
5. **Actions à lancer maintenant** : liste concrète (contacter Lionel, commander pièce, etc.)

Sois factuel. Chiffre les risques financiers quand tu le peux.
"""


# ── FONCTION PRINCIPALE (appelée depuis pages/2_Sophie.py) ───────────────────
def run_agent_sophie(c_rul: int, equipement: str = "Pompe P-17",
                     c_temp: float = None, c_vib: float = None) -> str:
    """
    Lance l'agent Sophie avec le RUL courant et le contexte machine.
    Retourne l'arbitrage planification en texte Markdown.
    """
    details = ""
    if c_temp: details += f"\n- Température : {c_temp:.1f}°C"
    if c_vib:  details += f"\n- Vibration   : {c_vib:.2f} mm/s"

    situation = (
        f"ALERTE MAINTENANCE — {equipement}\n"
        f"- RUL estimé : {c_rul}h{details}\n\n"
        f"Analyse l'impact production, la disponibilité des ressources "
        f"et recommande la meilleure stratégie d'intervention."
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
    print(run_agent_sophie(c_rul=18, equipement="Pompe P-17", c_temp=78.0, c_vib=5.8))
