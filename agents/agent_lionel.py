"""
agents/agent_lionel.py — Agent prescriptif de Lionel (Technicien Terrain)
Rôle : diagnostiquer une anomalie capteur, identifier la procédure d'intervention,
       vérifier les pièces disponibles et guider Lionel étape par étape sur le terrain.

Intégration dans pages/1_Lionel.py :
    from agents.agent_lionel import run_agent_lionel
    prescription = run_agent_lionel(c_temp, c_vib, c_pres, c_rul)
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


# ── CLIENTS ───────────────────────────────────────────────────────────────────
_notion   = Client(auth=_get_secret("NOTION_TOKEN"))

DB_EQUIPEMENTS = "f8c546b6-40b6-484c-b686-6a6ad42520ee"
DB_MAINTENANCE = "1c9d8c5d-e394-490a-b913-e0cf833abb5b"
DB_STOCK       = "7229437a-027a-440f-a7be-5e37157f3b8d"


# ── HELPERS NOTION ────────────────────────────────────────────────────────────
def _text(prop):
    if not prop: return ""
    t = prop.get("type")
    if t == "title":       return "".join(r["plain_text"] for r in prop.get("title", []))
    if t == "rich_text":   return "".join(r["plain_text"] for r in prop.get("rich_text", []))
    if t == "select":      s = prop.get("select"); return s["name"] if s else ""
    if t == "multi_select":return ", ".join(o["name"] for o in prop.get("multi_select", []))
    if t == "number":      return prop.get("number")
    if t == "date":        d = prop.get("date"); return d["start"] if d else ""
    return ""

def _p(page): return page.get("properties", {})


# ── OUTILS TERRAIN (ce dont Lionel a besoin sur le terrain) ───────────────────

def get_fiche_equipement(nom: str) -> dict:
    """Seuils, signe d'usure connus, technicien référent."""
    res = _notion.databases.query(
        database_id=DB_EQUIPEMENTS,
        filter={"property": "Équipement", "title": {"contains": nom}}
    )
    if not res["results"]: return {"erreur": f"'{nom}' non trouvé"}
    p = _p(res["results"][0])
    return {
        "equipement":     _text(p.get("Équipement")),
        "statut":         _text(p.get("Statut")),
        "fabricant":      _text(p.get("Fabricant")),
        "modele":         _text(p.get("Modèle")),
        "seuil_temp":     _text(p.get("Seuil Température (°C)")),
        "seuil_vib":      _text(p.get("Seuil Vibration (mm/s)")),
        "seuil_pres":     _text(p.get("Seuil Pression (bar)")),
        "rul_nominal_h":  _text(p.get("RUL nominal (h)")),
        "heures_total":   _text(p.get("Heures de fonctionnement total")),
        "notes_usure":    _text(p.get("Notes")),
    }

def get_procedure_intervention(equipement: str, type_anomalie: str) -> dict:
    """Procédure d'intervention planifiée la plus proche pour ce type d'anomalie."""
    res = _notion.databases.query(
        database_id=DB_MAINTENANCE,
        filter={"and": [
            {"property": "Équipement",  "rich_text": {"contains": equipement}},
            {"property": "Statut",      "select":    {"equals": "Planifiée"}}
        ]},
        sorts=[{"property": "Date planifiée", "direction": "ascending"}]
    )
    if not res["results"]: return {"info": "Aucune procédure planifiée trouvée"}
    # Cherche d'abord une intervention liée au type d'anomalie, sinon prend la plus proche
    for page in res["results"]:
        p = _p(page)
        titre = _text(p.get("Intervention")).lower()
        if any(kw in titre for kw in [type_anomalie.lower(), "joint", "roulement", "vibr", "surchauf"]):
            return _format_maintenance(p)
    return _format_maintenance(_p(res["results"][0]))  # fallback: la plus proche

def _format_maintenance(p: dict) -> dict:
    return {
        "intervention":   _text(p.get("Intervention")),
        "type":           _text(p.get("Type d'intervention")),
        "priorite":       _text(p.get("Priorité")),
        "date_planifiee": _text(p.get("Date planifiée")),
        "duree_h":        _text(p.get("Durée estimée (h)")),
        "technicien":     _text(p.get("Technicien assigné")),
        "habilitations":  _text(p.get("Habilitation requise")),
        "composants":     _text(p.get("Composants à remplacer")),
        "loto_requis":    _text(p.get("Procédure LOTO requise")),
        "cout_estime":    _text(p.get("Coût estimé (€)")),
        "description":    _text(p.get("Description")),
    }

def get_disponibilite_piece(nom_piece: str) -> dict:
    """Stock et emplacement magasin d'une pièce — ce que Lionel doit aller chercher."""
    res = _notion.databases.query(
        database_id=DB_STOCK,
        filter={"property": "Composant", "title": {"contains": nom_piece}}
    )
    if not res["results"]: return {"erreur": f"'{nom_piece}' non trouvé en magasin"}
    p = _p(res["results"][0])
    stock = _text(p.get("Stock actuel"))
    seuil = _text(p.get("Stock minimum (seuil alerte)"))
    return {
        "composant":     _text(p.get("Composant")),
        "stock_actuel":  stock,
        "statut_stock":  _text(p.get("Statut stock")),
        "emplacement":   _text(p.get("Emplacement magasin")),
        "critique":      _text(p.get("Critique")),
        "delai_reappro": _text(p.get("Délai réappro (jours)")),
        "notes":         _text(p.get("Notes")),
        "dispo_immediate": int(stock or 0) > 0,
    }


# ── OUTILS DÉCLARÉS À L'AGENT ─────────────────────────────────────────────────
TOOLS = [
    {
        "name": "get_fiche_equipement",
        "description": "Récupère la fiche technique de l'équipement : seuils d'alerte, heures de fonctionnement, signes d'usure connus, statut actuel.",
        "input_schema": {"type": "object", "properties": {"nom": {"type": "string", "description": "Nom de l'équipement ex: 'Pompe P-17'"}}, "required": ["nom"]}
    },
    {
        "name": "get_procedure_intervention",
        "description": "Récupère la procédure d'intervention planifiée la plus pertinente : étapes, LOTO, habilitations requises, pièces à préparer.",
        "input_schema": {"type": "object", "properties": {"equipement": {"type": "string"}, "type_anomalie": {"type": "string", "description": "Nature du problème ex: 'vibration', 'surchauffe', 'pression'"}}, "required": ["equipement", "type_anomalie"]}
    },
    {
        "name": "get_disponibilite_piece",
        "description": "Vérifie si une pièce est disponible en magasin et indique son emplacement exact pour que Lionel puisse aller la chercher.",
        "input_schema": {"type": "object", "properties": {"nom_piece": {"type": "string", "description": "Nom ou mot-clé de la pièce ex: 'joint', 'roulement', 'filtre'"}}, "required": ["nom_piece"]}
    }
]

def _execute(name, inputs):
    if name == "get_fiche_equipement":       return get_fiche_equipement(inputs["nom"])
    if name == "get_procedure_intervention": return get_procedure_intervention(inputs["equipement"], inputs["type_anomalie"])
    if name == "get_disponibilite_piece":    return get_disponibilite_piece(inputs["nom_piece"])
    return {"erreur": f"Outil inconnu : {name}"}


# ── PROMPT SYSTÈME ────────────────────────────────────────────────────────────
SYSTEM = """Tu es l'assistant de terrain de Lionel, technicien habilité Mécanique/Hydraulique.
Tu reçois des alertes capteurs en temps réel sur la Pompe P-17.

Ton rôle : guider Lionel avec des instructions claires et actionnables.
Format de réponse attendu :
1. **Diagnostic** : quelle est la cause probable (1-2 phrases max)
2. **Urgence** : niveau de priorité (Immédiat / Dans les 4h / Planifiable)
3. **Avant d'intervenir** : EPI requis + LOTO si nécessaire
4. **Étapes d'intervention** : liste numérotée, concrète
5. **Pièces à préparer** : ce que Lionel doit sortir du magasin avec l'emplacement

Sois direct. Lionel est sur le terrain, pas derrière un bureau. Pas de blabla.
"""


# ── FONCTION PRINCIPALE (appelée depuis pages/1_Lionel.py) ───────────────────
def run_agent_lionel(c_temp: float, c_vib: float, c_pres: float, c_rul: int) -> str:
    """
    Lance l'agent Lionel avec les valeurs capteurs courantes.
    Retourne la prescription terrain en texte Markdown.
    """
    situation = (
        f"ALERTE POMPE P-17 :\n"
        f"- Température : {c_temp:.1f}°C (seuil 110°C)\n"
        f"- Vibration   : {c_vib:.2f} mm/s (seuil 4.5 mm/s)\n"
        f"- Pression    : {c_pres:.1f} bar (seuil 7.0 bar)\n"
        f"- RUL estimé  : {c_rul}h\n\n"
        f"Que dois-je faire ? Donne-moi les instructions d'intervention."
    )

    messages = [{"role": "user", "content": situation}]
    while True:
        resp = _llm_chat(system=SYSTEM, messages=messages, tools=TOOLS, max_tokens=1500)
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
    print(run_agent_lionel(c_temp=117.0, c_vib=5.8, c_pres=4.6, c_rul=12))
