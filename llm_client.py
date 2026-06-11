# llm_client.py
# Couche d'abstraction LLM : supporte 1min.ai OU Anthropic selon la config
# Changer de provider = changer 2 lignes dans les secrets Streamlit, rien d'autre.
#
# Secrets Streamlit à configurer (1 seul provider à la fois) :
#
#   ── Option A : 1min.ai (recommandé pour éviter un compte Anthropic) ──
#   LLM_PROVIDER   = "1minai"
#   ONEMINAI_KEY   = "votre-clé-1min.ai"
#
#   ── Option B : Anthropic direct ──
#   LLM_PROVIDER   = "anthropic"
#   ANTHROPIC_API_KEY = "sk-ant-xxxxxxxxxxxx"

import json
import requests


def _get_secret(key: str) -> str:
    try:
        import streamlit as st
        return st.secrets[key]
    except Exception:
        import os
        return os.environ.get(key, "")


def _provider() -> str:
    return _get_secret("LLM_PROVIDER") or "1minai"


# ── MODÈLES DISPONIBLES ───────────────────────────────────────────────────────
# 1min.ai donne accès à Claude via ce nom de modèle :
MODEL_1MINAI    = "claude-opus-4-5"   # ou "claude-sonnet-4-5", "gpt-4o", etc.
MODEL_ANTHROPIC = "claude-opus-4-5"


# ─────────────────────────────────────────────────────────────────────────────
# PROVIDER 1min.ai
# L'API 1min.ai ne supporte pas le tool_use natif.
# On émule la boucle agent en injectant les outils dans le system prompt
# et en parsant la réponse JSON de l'agent.
# ─────────────────────────────────────────────────────────────────────────────

def _tools_to_prompt(tools: list) -> str:
    """Convertit la liste d'outils en instructions système pour 1min.ai."""
    lines = [
        "Tu as accès aux outils suivants. Pour appeler un outil, réponds UNIQUEMENT avec ce JSON :",
        '{"tool_call": {"name": "NOM_OUTIL", "arguments": {...}}}',
        "Quand tu as la réponse finale (sans appel d'outil), réponds normalement en texte.",
        "",
        "OUTILS DISPONIBLES :",
    ]
    for t in tools:
        props = t["input_schema"].get("properties", {})
        params = ", ".join(f"{k}: {v.get('type','string')}" for k, v in props.items())
        lines.append(f"- {t['name']}({params}) : {t['description']}")
    return "\n".join(lines)


def _call_1minai(system: str, messages: list, tools: list = None) -> dict:
    """
    Appelle l'API 1min.ai et retourne un objet normalisé :
    {"stop_reason": "end_turn"|"tool_use", "content": [...]}
    """
    api_key = _get_secret("ONEMINAI_KEY")

    # Construire le prompt complet (system + historique + outils)
    system_full = system
    if tools:
        system_full += "\n\n" + _tools_to_prompt(tools)

    # Reconstituer l'historique en un seul prompt texte
    history_text = ""
    for msg in messages[:-1]:   # tout sauf le dernier message
        role = "Utilisateur" if msg["role"] == "user" else "Assistant"
        if isinstance(msg["content"], str):
            history_text += f"{role}: {msg['content']}\n"
        elif isinstance(msg["content"], list):
            for block in msg["content"]:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        history_text += f"{role}: {block['text']}\n"
                    elif block.get("type") == "tool_result":
                        history_text += f"[Résultat outil]: {block.get('content', '')}\n"

    # Dernier message utilisateur
    last = messages[-1]
    if isinstance(last["content"], str):
        last_prompt = last["content"]
    elif isinstance(last["content"], list):
        parts = []
        for block in last["content"]:
            if isinstance(block, dict):
                if block.get("type") == "tool_result":
                    parts.append(f"[Résultat outil]: {block.get('content', '')}")
                elif block.get("type") == "text":
                    parts.append(block["text"])
        last_prompt = "\n".join(parts)
    else:
        last_prompt = str(last["content"])

    full_prompt = ""
    if history_text:
        full_prompt = f"Historique:\n{history_text}\n"
    full_prompt += last_prompt

    payload = {
        "type":  "UNIFY_CHAT_WITH_AI",
        "model": MODEL_1MINAI,
        "promptObject": {
            "prompt": full_prompt,
            "isMixed": False,
            "webSearch": False,
            "systemPrompt": system_full,
        }
    }

    resp = requests.post(
        "https://api.1min.ai/api/chat-with-ai",
        headers={"API-KEY": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=60
    )
    resp.raise_for_status()
    data = resp.json()

    # Extraire le texte de la réponse
    raw_text = (
        data.get("aiRecord", {})
            .get("aiRecordDetail", {})
            .get("resultObject", [""])[0]
        or ""
    )

    # Détecter si l'agent veut appeler un outil (JSON {"tool_call": ...})
    raw_stripped = raw_text.strip()
    if raw_stripped.startswith("{") and "tool_call" in raw_stripped:
        try:
            parsed    = json.loads(raw_stripped)
            tool_call = parsed.get("tool_call", {})
            return {
                "stop_reason": "tool_use",
                "content": [{
                    "type":  "tool_use",
                    "id":    "tc_1minai_0",
                    "name":  tool_call.get("name", ""),
                    "input": tool_call.get("arguments", {}),
                }]
            }
        except json.JSONDecodeError:
            pass

    # Réponse finale texte
    return {
        "stop_reason": "end_turn",
        "content": [{"type": "text", "text": raw_text}]
    }


# ─────────────────────────────────────────────────────────────────────────────
# PROVIDER Anthropic (inchangé, pour référence)
# ─────────────────────────────────────────────────────────────────────────────

def _call_anthropic(system: str, messages: list, tools: list = None,
                    max_tokens: int = 2000) -> dict:
    import anthropic as _anthropic
    client = _anthropic.Anthropic(api_key=_get_secret("ANTHROPIC_API_KEY"))
    kwargs = dict(model=MODEL_ANTHROPIC, max_tokens=max_tokens,
                  system=system, messages=messages)
    if tools:
        kwargs["tools"] = tools
    resp = client.messages.create(**kwargs)
    # Normaliser en dict simple pour uniformité
    return {
        "stop_reason": resp.stop_reason,
        "content": [
            {"type": b.type, "text": getattr(b, "text", None),
             "id": getattr(b, "id", None), "name": getattr(b, "name", None),
             "input": getattr(b, "input", None)}
            for b in resp.content
        ]
    }


# ─────────────────────────────────────────────────────────────────────────────
# INTERFACE PUBLIQUE — utilisée par tous les agents
# ─────────────────────────────────────────────────────────────────────────────

class LLMResponse:
    """Wrapper unifié autour des réponses des deux providers."""
    def __init__(self, raw: dict):
        self._raw = raw

    @property
    def stop_reason(self) -> str:
        return self._raw.get("stop_reason", "end_turn")

    @property
    def content(self) -> list:
        return self._raw.get("content", [])

    def final_text(self) -> str:
        return "".join(
            b.get("text", "") or ""
            for b in self.content
            if b.get("type") == "text"
        )

    def tool_calls(self) -> list:
        """Retourne la liste des appels d'outils demandés par l'agent."""
        return [b for b in self.content if b.get("type") == "tool_use"]


def chat(system: str, messages: list, tools: list = None,
         max_tokens: int = 2000) -> LLMResponse:
    """
    Point d'entrée unique pour tous les agents.
    Utilise 1min.ai ou Anthropic selon LLM_PROVIDER dans les secrets.

    Usage dans un agent :
        from llm_client import chat, LLMResponse
        resp = chat(system=SYSTEM, messages=messages, tools=TOOLS)
        if resp.stop_reason == "tool_use":
            for tc in resp.tool_calls():
                result = execute_tool(tc["name"], tc["input"])
    """
    provider = _provider()
    if provider == "anthropic":
        raw = _call_anthropic(system, messages, tools, max_tokens)
    else:
        raw = _call_1minai(system, messages, tools)
    return LLMResponse(raw)
