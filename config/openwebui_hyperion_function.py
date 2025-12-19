"""
title: Hyperion RAG
author: Hyperion
version: 1.0.0
description: Connecte Open WebUI au RAG Hyperion pour interroger les repos Git analysés
"""

import requests
from typing import Optional, Callable, Awaitable, Any
from pydantic import BaseModel, Field


class Pipe:
    """
    Pipe Open WebUI pour Hyperion RAG.
    Route les questions vers l'API Hyperion /api/chat.
    """
    
    class Valves(BaseModel):
        """Configuration du pipe."""
        HYPERION_API_URL: str = Field(
            default="http://host.docker.internal:8000",
            description="URL de l'API Hyperion"
        )
        DEFAULT_REPO: str = Field(
            default="",
            description="Repo par défaut (vide = tous les repos)"
        )
    
    def __init__(self):
        self.type = "pipe"
        self.name = "Hyperion RAG"
        self.valves = self.Valves()
    
    def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> str:
        """
        Traite la requête et appelle l'API Hyperion.
        """
        # Extraire le message utilisateur
        messages = body.get("messages", [])
        if not messages:
            return "Aucun message reçu."
        
        # Dernier message utilisateur
        user_message = messages[-1].get("content", "")
        if not user_message:
            return "Message vide."
        
        # Construire l'historique
        history = []
        for msg in messages[:-1]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ["user", "assistant"] and content:
                history.append({"role": role, "content": content})
        
        # Détecter si un repo est mentionné dans le message
        repo = self.valves.DEFAULT_REPO or None
        
        # Appeler l'API Hyperion
        try:
            response = requests.post(
                f"{self.valves.HYPERION_API_URL}/api/chat",
                json={
                    "question": user_message,
                    "repo": repo,
                    "history": history if history else None
                },
                timeout=60
            )
            
            if response.status_code != 200:
                return f"Erreur API Hyperion: {response.status_code} - {response.text}"
            
            data = response.json()
            answer = data.get("answer", "Pas de réponse.")
            sources = data.get("sources", [])
            
            # Formater la réponse avec sources
            result = answer
            
            if sources:
                result += "\n\n---\n**Sources:**\n"
                for i, src in enumerate(sources[:3], 1):
                    repo_name = src.get("repo", "unknown")
                    section = src.get("section", "")
                    score = src.get("score", 0)
                    result += f"- [{repo_name}/{section}] (score: {score:.2f})\n"
            
            return result
            
        except requests.exceptions.ConnectionError:
            return "❌ Impossible de se connecter à l'API Hyperion. Vérifiez que le service tourne sur http://localhost:8000"
        except requests.exceptions.Timeout:
            return "❌ Timeout: L'API Hyperion met trop de temps à répondre."
        except Exception as e:
            return f"❌ Erreur: {str(e)}"
