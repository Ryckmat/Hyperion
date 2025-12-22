# hyperion/api/openai_compat.py
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from hyperion.api.main import get_query_engine  # réutilise ton lazy loader existant

router = APIRouter(tags=["openai-compat"])


class ChatCompletionsIn(BaseModel):
    model: str | None = "hyperion-rag"
    messages: list[dict[str, Any]]
    stream: bool | None = False
    temperature: float | None = None


@router.get("/v1/models")
def list_models():
    now = int(time.time())
    return {
        "object": "list",
        "data": [
            {"id": "hyperion-rag", "object": "model", "created": now, "owned_by": "hyperion"},
        ],
    }


@router.post("/v1/chat/completions")
def chat_completions(body: ChatCompletionsIn):
    msgs = body.messages or []
    if not msgs:
        raise HTTPException(status_code=400, detail="messages is required")

    # Dernier message user = question
    user_message = None
    history: list[dict[str, str]] = []

    for m in msgs:
        role = m.get("role")
        content = m.get("content", "")
        if role == "user":
            user_message = content
        if role in ("user", "assistant") and content:
            history.append({"role": role, "content": content})

    if not user_message:
        raise HTTPException(status_code=400, detail="No user message found")

    # Retire la question finale de l'historique
    if history and history[-1]["role"] == "user":
        history = history[:-1]

    # Appel direct du moteur RAG (pas besoin de requête HTTP interne)
    try:
        engine = get_query_engine()
        data = engine.chat(
            question=user_message,
            repo=None,  # tu peux ajouter une logique de repo ici si tu veux
            history=history if history else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    answer = data.get("answer", "Pas de réponse.")

    # (Option) inclure les sources dans le texte (pratique dans Open WebUI)
    sources = data.get("sources", [])
    if sources:
        answer += "\n\n---\n**Sources:**\n"
        for _i, src in enumerate(sources[:3], 1):
            answer += f"- [{src.get('repo','?')}/{src.get('section','?')}] (score: {src.get('score',0):.2f})\n"

    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": body.model or "hyperion-rag",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": answer},
                "finish_reason": "stop",
            }
        ],
    }
