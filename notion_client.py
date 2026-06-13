# notion_client.py
# Connexion live aux 6 bases Notion — ResilientFlow AI
# Remplace les données statiques de shared_state.py

import requests
import streamlit as st
import os

# ── CONFIG ────────────────────────────────────────────────────────────────────
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

# IDs des 6 bases de données Notion
DB_IDS = {
    "machines":   "5279cb2a42b54b42936e22313521f825",
    "equipe":     "0a82b4f53a26491c81e64b0cb8bb058c",
    "pieces":     "c22138baa8ca4806b19403108735bc68",
    "ordres_fab": "d7ee45dab07943c1bda09a6b47089202",
    "historique": "6f53558bfbee455891efa53b6536d892",
    "hse_docs":   "b6ab3a9bd41d4967add92f27d1cd2d5c",
}


def _get_token() -> str:
    try:
        return st.secrets["NOTION_TOKEN"]
    except Exception:
        return os.environ.get("NOTION_TOKEN", "")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_token()}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _query_db(db_id: str, filter_payload: dict = None, sorts: list = None) -> list:
    """Interroge une base Notion avec pagination automatique."""
    url = f"{NOTION_BASE_URL}/databases/{db_id}/query"
    body = {}
    if filter_payload:
        body["filter"] = filter_payload
    if sorts:
        body["sorts"] = sorts

    results, has_more, next_cursor = [], True, None
    while has_more:
        if next_cursor:
            body["start_cursor"] = next_cursor
        resp = requests.post(url, headers=_headers(), json=body, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")
    return results


def _prop(page: dict, name: str):
    """Extrait la valeur typée d'une propriété Notion."""
    p = page.get("properties", {}).get(name, {})
    t = p.get("type", "")
    if t == "title":
        return "".join(r.get("plain_text", "") for r in p.get("title", []))
    if t == "rich_text":
        return "".join(r.get("plain_text", "") for r in p.get("rich_text", []))
    if t == "number":
        return p.get("number")
    if t == "select":
        s = p.get("select")
        return s["name"] if s else None
    if t == "multi_select":
        return [s["name"] for s in p.get("multi_select", [])]
    if t == "date":
        d = p.get("date")
        return d["start"] if d else None
    if t == "url":
        return p.get("url")
    if t == "checkbox":
        return p.get("checkbox")
    return None


# ── 1. MACHINES ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def get_machines(statut: str = None) -> list[dict]:
    """Toutes les machines, triées par RUL croissant. Filtre optionnel par statut."""
    f = {"property": "Statut", "select": {"equals": statut}} if statut else None
    pages = _query_db(DB_IDS["machines"], f,
                      sorts=[{"property": "RUL (jours)", "direction": "ascending"}])
    return [_parse_machine(p) for p in pages]


@st.cache_data(ttl=30)
def get_machine(machine_id: str) -> dict | None:
    """Machine par son ID métier (ex: 'P-17', 'C-03')."""
    pages = _query_db(DB_IDS["machines"],
                      {"property": "ID Machine", "rich_text": {"equals": machine_id}})
    return _parse_machine(pages[0]) if pages else None


def _parse_machine(p: dict) -> dict:
    return {
        "id":                    _prop(p, "ID Machine"),
        "nom":                   _prop(p, "Nom Machine"),
        "type":                  _prop(p, "Type"),
        "statut":                _prop(p, "Statut"),
        "rul_jours":             _prop(p, "RUL (jours)"),
        "temperature":           _prop(p, "Température actuelle (°C)"),
        "vibration":             _prop(p, "Vibration actuelle (mm/s)"),
        "score_degradation":     _prop(p, "Score dégradation (%)"),
        "seuil_temp":            _prop(p, "Seuil température (°C)"),
        "seuil_vib":             _prop(p, "Seuil vibration (mm/s)"),
        "unite":                 _prop(p, "Unité / Zone"),
        "responsable":           _prop(p, "Responsable"),
        "notes_ia":              _prop(p, "Notes IA"),
        "derniere_inspection":   _prop(p, "Dernière inspection"),
        "prochaine_maintenance": _prop(p, "Prochaine maintenance"),
    }


# ── 2. ÉQUIPE MAINTENANCE ─────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_equipe(disponibilite: str = None) -> list[dict]:
    """Équipe maintenance. Filtre optionnel par disponibilité."""
    f = {"property": "Disponibilité", "select": {"equals": disponibilite}} if disponibilite else None
    pages = _query_db(DB_IDS["equipe"], f)
    return [{
        "nom":             _prop(p, "Nom Technicien"),
        "prenom":          _prop(p, "Prénom"),
        "role":            _prop(p, "Rôle"),
        "persona":         _prop(p, "Persona"),
        "specialite":      _prop(p, "Spécialité"),
        "habilitations":   _prop(p, "Habilitations"),   # list
        "disponibilite":   _prop(p, "Disponibilité"),
        "charge_horaire":  _prop(p, "Charge horaire (h/sem)"),
        "heures_restantes": _prop(p, "Heures restantes"),
        "zone":            _prop(p, "Zone assignée"),
        "certifications":  _prop(p, "Certifications"),
        "telephone":       _prop(p, "Téléphone"),
        "notes":           _prop(p, "Notes"),
    } for p in pages]


# ── 3. PIÈCES DÉTACHÉES ───────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_pieces(machine_id: str = None, statut_stock: str = None) -> list[dict]:
    """Pièces détachées. Filtres optionnels par machine et/ou statut stock."""
    filters = []
    if machine_id:
        filters.append({"property": "Machine concernée", "rich_text": {"contains": machine_id}})
    if statut_stock:
        filters.append({"property": "Statut stock", "select": {"equals": statut_stock}})

    f = None if not filters else (filters[0] if len(filters) == 1 else {"and": filters})
    pages = _query_db(DB_IDS["pieces"], f)
    return [{
        "designation":     _prop(p, "Désignation pièce"),
        "reference":       _prop(p, "Référence"),
        "categorie":       _prop(p, "Catégorie"),
        "machine":         _prop(p, "Machine concernée"),
        "emplacement":     _prop(p, "Emplacement magasin"),
        "stock_actuel":    _prop(p, "Stock actuel"),
        "stock_minimum":   _prop(p, "Stock minimum"),
        "statut_stock":    _prop(p, "Statut stock"),
        "prix_unitaire":   _prop(p, "Prix unitaire (€)"),
        "fournisseur":     _prop(p, "Fournisseur"),
        "delai_livraison": _prop(p, "Délai livraison (j)"),
        "notes":           _prop(p, "Notes"),
    } for p in pages]


# ── 4. ORDRES DE FABRICATION ──────────────────────────────────────────────────

@st.cache_data(ttl=30)
def get_ordres_fabrication(statut: str = None, machine_id: str = None) -> list[dict]:
    """Ordres de fabrication. Filtres optionnels par statut et machine."""
    filters = []
    if statut:
        filters.append({"property": "Statut OF", "select": {"equals": statut}})
    if machine_id:
        filters.append({"property": "Machine impactée", "rich_text": {"contains": machine_id}})

    f = None if not filters else (filters[0] if len(filters) == 1 else {"and": filters})
    pages = _query_db(DB_IDS["ordres_fab"], f,
                      sorts=[{"property": "Priorité", "direction": "ascending"}])
    return [{
        "reference":    _prop(p, "Référence OF"),
        "produit":      _prop(p, "Produit"),
        "statut":       _prop(p, "Statut OF"),
        "priorite":     _prop(p, "Priorité"),
        "ligne":        _prop(p, "Ligne de production"),
        "machine":      _prop(p, "Machine impactée"),
        "date_debut":   _prop(p, "Date début"),
        "date_fin":     _prop(p, "Date fin prévue"),
        "qte_prevue":   _prop(p, "Quantité prévue"),
        "qte_realisee": _prop(p, "Quantité réalisée"),
        "cout_arret":   _prop(p, "Coût arrêt (€)"),
        "duree_arret":  _prop(p, "Durée arrêt (h)"),
        "impact_rul":   _prop(p, "Impact RUL"),
        "responsable":  _prop(p, "Responsable production"),
    } for p in pages]


# ── 5. HISTORIQUE & PLAN DE MAINTENANCE ───────────────────────────────────────

@st.cache_data(ttl=60)
def get_historique(machine_id: str = None, statut: str = None, limit: int = 20) -> list[dict]:
    """Historique des interventions, triées par date décroissante."""
    filters = []
    if machine_id:
        filters.append({"property": "Machine", "rich_text": {"contains": machine_id}})
    if statut:
        filters.append({"property": "Statut", "select": {"equals": statut}})

    f = None if not filters else (filters[0] if len(filters) == 1 else {"and": filters})
    pages = _query_db(DB_IDS["historique"], f,
                      sorts=[{"property": "Date intervention", "direction": "descending"}])
    return [{
        "titre":             _prop(p, "Titre intervention"),
        "machine":           _prop(p, "Machine"),
        "type":              _prop(p, "Type"),
        "statut":            _prop(p, "Statut"),
        "technicien":        _prop(p, "Technicien assigné"),
        "date":              _prop(p, "Date intervention"),
        "prochaine_echeance": _prop(p, "Prochaine échéance"),
        "duree_estimee":     _prop(p, "Durée estimée (h)"),
        "duree_reelle":      _prop(p, "Durée réelle (h)"),
        "cout_intervention": _prop(p, "Coût intervention (€)"),
        "cout_arret_prod":   _prop(p, "Coût arrêt production (€)"),
        "rul_avant":         _prop(p, "RUL avant intervention (j)"),
        "rul_apres":         _prop(p, "RUL après intervention (j)"),
        "cause_racine":      _prop(p, "Cause racine"),
        "actions":           _prop(p, "Actions réalisées"),
        "pieces":            _prop(p, "Pièces remplacées"),
        "observations":      _prop(p, "Observations"),
        "alerte_ia":         _prop(p, "Lien alerte IA"),
    } for p in pages[:limit]]


# ── 6. DOCUMENTATION & HSE ────────────────────────────────────────────────────

@st.cache_data(ttl=120)
def get_docs_hse(machine_id: str = None, type_doc: str = None, persona: str = None) -> list[dict]:
    """Documents HSE. Filtres optionnels par machine, type et persona destinataire."""
    filters = []
    if machine_id:
        filters.append({"property": "Machine concernée", "rich_text": {"contains": machine_id}})
    if type_doc:
        filters.append({"property": "Type", "select": {"equals": type_doc}})

    f = None if not filters else (filters[0] if len(filters) == 1 else {"and": filters})
    pages = _query_db(DB_IDS["hse_docs"], f)

    docs = [{
        "titre":           _prop(p, "Titre document"),
        "type":            _prop(p, "Type"),
        "statut":          _prop(p, "Statut"),
        "machine":         _prop(p, "Machine concernée"),
        "niveau_risque":   _prop(p, "Niveau risque"),
        "epi":             _prop(p, "EPI obligatoires"),        # list
        "persona":         _prop(p, "Persona destinataire"),    # list
        "version":         _prop(p, "Version"),
        "auteur":          _prop(p, "Auteur"),
        "resume":          _prop(p, "Contenu résumé"),
        "lien":            _prop(p, "Lien document"),
        "date_validation": _prop(p, "Date validation"),
        "date_revision":   _prop(p, "Date révision"),
    } for p in pages]

    if persona:
        docs = [d for d in docs if persona in (d.get("persona") or [])]
    return docs


# ── CONTEXTE COMPLET MACHINE (agrégateur) ─────────────────────────────────────

@st.cache_data(ttl=30)
def get_contexte_machine(machine_id: str) -> dict:
    """
    Retourne le contexte complet d'une machine pour alimenter les 4 agents.
    Remplace dynamiquement le CONTEXTE_USINE statique de shared_state.py.

    Usage dans un agent :
        from notion_client import get_contexte_machine
        ctx = get_contexte_machine("P-17")
        rul = ctx["machine"]["rul_jours"]
        pieces_dispo = ctx["pieces"]
    """
    return {
        "machine":      get_machine(machine_id) or {},
        "pieces":       get_pieces(machine_id=machine_id),
        "ordres_fab":   get_ordres_fabrication(machine_id=machine_id, statut="En cours"),
        "historique":   get_historique(machine_id=machine_id, limit=5),
        "docs_hse":     get_docs_hse(machine_id=machine_id),
        "equipe_dispo": get_equipe(disponibilite="Disponible"),
    }


# ── MÉTRIQUES ROI (Agent Antoine) ────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_metriques_roi() -> dict:
    """
    Calcule les KPIs ROI depuis l'historique Notion.
    Utilisé par l'Agent Antoine pour le dashboard exécutif.
    """
    interventions  = get_historique(limit=100)
    terminees      = [i for i in interventions if i["statut"] == "Terminée"]
    prescriptives  = [i for i in terminees if i["type"] == "Maintenance prescriptive"]

    cout_interventions = sum(i.get("cout_intervention") or 0 for i in terminees)
    couts_evites       = sum(i.get("cout_arret_prod") or 0 for i in prescriptives)
    roi = round(couts_evites / cout_interventions, 1) if cout_interventions > 0 else 0

    machines_alerte = get_machines(statut="Alerte critique")

    return {
        "nb_interventions":   len(terminees),
        "nb_prescriptives":   len(prescriptives),
        "cout_interventions": cout_interventions,
        "couts_evites":       couts_evites,
        "roi":                roi,
        "machines_alerte":    len(machines_alerte),
        "detail_alertes":     machines_alerte,
    }
