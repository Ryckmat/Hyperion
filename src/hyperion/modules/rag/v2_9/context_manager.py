"""
Context Manager for Hyperion v2.9

Gestion intelligente du contexte avec mémoire et personalisation.
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Un échange dans la conversation"""

    timestamp: float
    user_query: str
    system_response: str
    context_used: list[str]
    satisfaction_score: float | None = None
    follow_up_queries: list[str] = field(default_factory=list)


@dataclass
class UserProfile:
    """Profil utilisateur pour personnalisation"""

    user_id: str
    expertise_level: str = "intermediate"  # beginner, intermediate, expert
    preferred_language: str = "fr"
    preferred_detail_level: str = "balanced"  # brief, balanced, detailed
    domain_interests: list[str] = field(default_factory=list)
    interaction_history: list[ConversationTurn] = field(default_factory=list)

    # Préférences apprises
    preferred_response_style: str = "explanatory"  # direct, explanatory, example_heavy
    common_topics: list[str] = field(default_factory=list)
    successful_interaction_patterns: dict[str, int] = field(default_factory=dict)


@dataclass
class ContextWindow:
    """Fenêtre de contexte pour une session"""

    session_id: str
    conversation_history: deque = field(default_factory=lambda: deque(maxlen=20))
    active_topics: list[str] = field(default_factory=list)
    current_repo_context: str | None = None
    user_intent_chain: list[str] = field(default_factory=list)

    # Métadonnées contextuelles
    session_start_time: float = field(default_factory=time.time)
    last_interaction_time: float = field(default_factory=time.time)
    context_quality_score: float = 0.0


class ContextManager:
    """
    Gestionnaire de contexte intelligent pour Hyperion v2.9

    Fonctionnalités :
    - Mémoire conversationnelle persistante
    - Profiling utilisateur automatique
    - Adaptation du style de réponse
    - Détection de changement de sujet
    - Résolution de références contextuelles
    - Prédiction d'intentions
    - Optimisation de fenêtre contextuelle
    """

    def __init__(self, max_sessions: int = 1000, context_retention_hours: int = 24):
        self.max_sessions = max_sessions
        self.context_retention_hours = context_retention_hours

        # Storage
        self.active_contexts: dict[str, ContextWindow] = {}
        self.user_profiles: dict[str, UserProfile] = {}
        self.global_patterns: dict[str, Any] = {
            "common_sequences": {},
            "successful_styles": {},
            "topic_transitions": {},
        }

        # Configuration
        self.context_compression_threshold = 15  # Nombre de tours avant compression

        logger.info("ContextManager v2.9 initialisé")

    def get_or_create_context(self, session_id: str, _user_id: str | None = None) -> ContextWindow:
        """Obtenir ou créer un contexte de session"""

        if session_id not in self.active_contexts:
            # Créer nouveau contexte
            context = ContextWindow(session_id=session_id)
            self.active_contexts[session_id] = context

            # Nettoyer les anciens contextes si nécessaire
            if len(self.active_contexts) > self.max_sessions:
                self._cleanup_old_contexts()

            logger.debug(f"Nouveau contexte créé: {session_id}")
        else:
            context = self.active_contexts[session_id]
            context.last_interaction_time = time.time()

        return context

    def get_user_profile(self, user_id: str) -> UserProfile:
        """Obtenir ou créer un profil utilisateur"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id=user_id)
            logger.debug(f"Nouveau profil utilisateur créé: {user_id}")

        return self.user_profiles[user_id]

    def add_conversation_turn(
        self,
        session_id: str,
        user_id: str | None,
        query: str,
        response: str,
        sources_used: list[str],
    ):
        """Ajouter un échange à l'historique conversationnel"""

        context = self.get_or_create_context(session_id, user_id)

        turn = ConversationTurn(
            timestamp=time.time(),
            user_query=query,
            system_response=response,
            context_used=sources_used,
        )

        context.conversation_history.append(turn)

        # Mise à jour du profil utilisateur si disponible
        if user_id:
            profile = self.get_user_profile(user_id)
            profile.interaction_history.append(turn)

            # Apprentissage automatique des préférences
            self._learn_user_preferences(profile, turn)

        # Mise à jour des topics actifs
        self._update_active_topics(context, query)

        # Mise à jour de la chaîne d'intentions
        self._update_intent_chain(context, query)

        # Compression si nécessaire
        if len(context.conversation_history) >= self.context_compression_threshold:
            self._compress_context_history(context)

        logger.debug(f"Tour de conversation ajouté: {session_id}")

    def _learn_user_preferences(self, profile: UserProfile, turn: ConversationTurn):
        """Apprentissage automatique des préférences utilisateur"""

        query = turn.user_query.lower()

        # Analyse du niveau de détail préféré
        if any(word in query for word in ["detail", "explain", "how exactly", "step by step"]):
            if profile.preferred_detail_level != "detailed":
                profile.preferred_detail_level = "detailed"

        elif (
            any(word in query for word in ["quick", "brief", "summary", "tldr"])
            and profile.preferred_detail_level != "brief"
        ):
            profile.preferred_detail_level = "brief"

        # Détection des domaines d'intérêt
        technical_domains = {
            "backend": ["api", "server", "database", "backend"],
            "frontend": ["ui", "frontend", "interface", "component"],
            "devops": ["docker", "deploy", "infrastructure", "ci/cd"],
            "security": ["auth", "security", "permission", "vulnerability"],
            "testing": ["test", "testing", "unittest", "coverage"],
        }

        for domain, keywords in technical_domains.items():
            if (
                any(keyword in query for keyword in keywords)
                and domain not in profile.domain_interests
            ):
                profile.domain_interests.append(domain)

        # Analyse du style de réponse préféré
        if any(word in query for word in ["example", "show me", "demonstrate"]):
            profile.preferred_response_style = "example_heavy"

    def _update_active_topics(self, context: ContextWindow, query: str):
        """Mise à jour des topics actifs"""

        # Extraction simple de topics
        query_lower = query.lower()
        potential_topics = []

        # Topics techniques
        tech_topics = {
            "authentication": ["auth", "login", "token", "session"],
            "database": ["db", "database", "query", "sql"],
            "api": ["api", "endpoint", "request", "response"],
            "testing": ["test", "testing", "unittest", "mock"],
            "error_handling": ["error", "exception", "try", "catch"],
        }

        for topic, keywords in tech_topics.items():
            if any(keyword in query_lower for keyword in keywords):
                potential_topics.append(topic)

        # Mise à jour avec decay temporel
        current_time = time.time()
        context.active_topics = [
            topic
            for topic in context.active_topics
            if current_time - context.last_interaction_time < 300  # 5 minutes
        ]

        # Ajouter nouveaux topics
        for topic in potential_topics:
            if topic not in context.active_topics:
                context.active_topics.append(topic)

        # Limiter le nombre de topics actifs
        context.active_topics = context.active_topics[-5:]

    def _update_intent_chain(self, context: ContextWindow, query: str):
        """Mise à jour de la chaîne d'intentions"""

        intent = self._detect_intent(query)
        if intent:
            context.user_intent_chain.append(intent)

            # Garder seulement les 10 dernières intentions
            context.user_intent_chain = context.user_intent_chain[-10:]

    def _detect_intent(self, query: str) -> str | None:
        """Détection d'intention simplifiée"""
        query_lower = query.lower()

        intent_patterns = {
            "learn": ["learn", "understand", "explain", "what is"],
            "troubleshoot": ["error", "problem", "issue", "bug", "not working"],
            "implement": ["how to", "implement", "create", "build"],
            "optimize": ["optimize", "improve", "performance", "faster"],
            "compare": ["compare", "difference", "vs", "versus", "better"],
            "find": ["find", "search", "locate", "where"],
        }

        for intent, patterns in intent_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return intent

        return None

    def _compress_context_history(self, context: ContextWindow):
        """Compression intelligente de l'historique"""

        if len(context.conversation_history) < self.context_compression_threshold:
            return

        # Garder les N derniers échanges complets
        recent_turns = 5
        important_turns = []

        # Identifier les échanges importants (haute satisfaction, topics clés)
        for turn in list(context.conversation_history)[:-recent_turns]:
            if (turn.satisfaction_score and turn.satisfaction_score > 0.8) or any(
                topic in turn.user_query.lower() for topic in context.active_topics
            ):
                important_turns.append(turn)

        # Créer résumé des anciens échanges
        if len(context.conversation_history) > recent_turns + len(important_turns):
            old_turns = list(context.conversation_history)[:-recent_turns]
            summary = self._create_conversation_summary(old_turns)

            # Remplacer par le résumé
            context.conversation_history.clear()

            # Ajouter résumé comme premier élément
            summary_turn = ConversationTurn(
                timestamp=old_turns[0].timestamp,
                user_query="[SUMMARY]",
                system_response=summary,
                context_used=["conversation_summary"],
            )
            context.conversation_history.append(summary_turn)

            # Ré-ajouter les échanges importants et récents
            for turn in important_turns:
                context.conversation_history.append(turn)

            for turn in list(context.conversation_history)[-recent_turns:]:
                if turn.user_query != "[SUMMARY]":
                    context.conversation_history.append(turn)

        logger.debug(f"Historique compressé pour session {context.session_id}")

    def _create_conversation_summary(self, turns: list[ConversationTurn]) -> str:
        """Créer un résumé des échanges précédents"""

        topics = set()
        key_points = []

        for turn in turns:
            # Extraire topics
            query_topics = self._extract_topics_from_text(turn.user_query)
            topics.update(query_topics)

            # Extraire points clés
            if len(turn.system_response) > 100:
                key_points.append(turn.system_response[:100] + "...")

        summary_parts = []

        if topics:
            summary_parts.append(f"Topics discutés: {', '.join(topics)}")

        if key_points:
            summary_parts.append(f"Points clés: {' | '.join(key_points[:3])}")

        return " // ".join(summary_parts) if summary_parts else "Session précédente résumée."

    def _extract_topics_from_text(self, text: str) -> list[str]:
        """Extraction simple de topics d'un texte"""
        text_lower = text.lower()
        topics = []

        topic_keywords = {
            "auth": ["auth", "login", "token"],
            "api": ["api", "endpoint", "request"],
            "database": ["db", "database", "query"],
            "testing": ["test", "testing", "unittest"],
            "deployment": ["deploy", "docker", "build"],
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)

        return topics

    def get_contextual_prompt_enhancement(
        self, session_id: str, user_id: str | None, current_query: str
    ) -> dict[str, Any]:
        """Obtenir des améliorations contextuelles pour le prompt"""

        context = self.get_or_create_context(session_id, user_id)
        enhancements = {}

        # Contexte conversationnel
        if context.conversation_history:
            recent_context = self._build_recent_context(context)
            enhancements["conversation_context"] = recent_context

        # Profil utilisateur
        if user_id:
            profile = self.get_user_profile(user_id)
            enhancements["user_preferences"] = {
                "expertise_level": profile.expertise_level,
                "detail_level": profile.preferred_detail_level,
                "response_style": profile.preferred_response_style,
                "domain_interests": profile.domain_interests,
            }

        # Topics actifs
        if context.active_topics:
            enhancements["active_topics"] = context.active_topics

        # Prédiction d'intention
        predicted_intent = self._predict_next_intent(context)
        if predicted_intent:
            enhancements["predicted_intent"] = predicted_intent

        # Références contextuelles
        references = self._resolve_contextual_references(context, current_query)
        if references:
            enhancements["contextual_references"] = references

        return enhancements

    def _build_recent_context(self, context: ContextWindow) -> str:
        """Construire le contexte récent"""

        if not context.conversation_history:
            return ""

        # Prendre les 3 derniers échanges
        recent_turns = list(context.conversation_history)[-3:]

        context_parts = []
        for turn in recent_turns:
            if turn.user_query != "[SUMMARY]":
                context_parts.append(f"User: {turn.user_query}")
                context_parts.append(f"Assistant: {turn.system_response[:200]}...")

        return "\n".join(context_parts)

    def _predict_next_intent(self, context: ContextWindow) -> str | None:
        """Prédiction de la prochaine intention"""

        if len(context.user_intent_chain) < 2:
            return None

        # Analyse des patterns d'intention
        recent_intents = context.user_intent_chain[-3:]

        # Patterns communs observés
        intent_transitions = {
            ("learn", "implement"): "troubleshoot",
            ("troubleshoot", "find"): "implement",
            ("compare", "learn"): "implement",
            ("implement", "troubleshoot"): "optimize",
        }

        if len(recent_intents) >= 2:
            transition = (recent_intents[-2], recent_intents[-1])
            return intent_transitions.get(transition)

        return None

    def _resolve_contextual_references(self, context: ContextWindow, query: str) -> list[str]:
        """Résolution des références contextuelles"""

        references = []
        query_lower = query.lower()

        # Références temporelles
        if (
            any(word in query_lower for word in ["that", "this", "it", "same"])
            and context.conversation_history
        ):
            last_turn = list(context.conversation_history)[-1]
            references.append(f"Référence possible: {last_turn.user_query}")

        # Références de continuation
        if (
            any(word in query_lower for word in ["also", "additionally", "moreover"])
            and context.active_topics
        ):
            references.append(f"Topic actuel: {context.active_topics[-1]}")

        # Références d'opposition
        if (
            any(word in query_lower for word in ["but", "however", "instead"])
            and context.conversation_history
        ):
            last_turn = list(context.conversation_history)[-1]
            references.append(f"Contraste avec: {last_turn.user_query}")

        return references

    def set_satisfaction_score(self, session_id: str, score: float):
        """Définir le score de satisfaction pour le dernier échange"""

        if session_id in self.active_contexts:
            context = self.active_contexts[session_id]
            if context.conversation_history:
                last_turn = list(context.conversation_history)[-1]
                last_turn.satisfaction_score = score

                # Apprentissage global des patterns réussis
                self._update_global_patterns(last_turn, score)

    def _update_global_patterns(self, turn: ConversationTurn, satisfaction: float):
        """Mise à jour des patterns globaux de succès"""

        if satisfaction > 0.7:  # Interaction réussie
            # Enregistrer le style de réponse réussi
            response_style = self._analyze_response_style(turn.system_response)
            if response_style not in self.global_patterns["successful_styles"]:
                self.global_patterns["successful_styles"][response_style] = 0
            self.global_patterns["successful_styles"][response_style] += 1

    def _analyze_response_style(self, response: str) -> str:
        """Analyser le style d'une réponse"""
        response_lower = response.lower()

        if any(word in response_lower for word in ["example", "for instance", "e.g."]):
            return "example_based"
        elif any(word in response_lower for word in ["step", "first", "then", "finally"]):
            return "step_by_step"
        elif any(word in response_lower for word in ["because", "since", "therefore"]):
            return "explanatory"
        elif len(response) < 200:
            return "concise"
        else:
            return "detailed"

    def _cleanup_old_contexts(self):
        """Nettoyer les anciens contextes"""
        current_time = time.time()
        cutoff_time = current_time - (self.context_retention_hours * 3600)

        to_remove = []
        for session_id, context in self.active_contexts.items():
            if context.last_interaction_time < cutoff_time:
                to_remove.append(session_id)

        for session_id in to_remove:
            del self.active_contexts[session_id]

        if to_remove:
            logger.debug(f"Nettoyé {len(to_remove)} contextes anciens")

    def get_context_statistics(self) -> dict[str, Any]:
        """Obtenir les statistiques du gestionnaire de contexte"""

        return {
            "active_sessions": len(self.active_contexts),
            "registered_users": len(self.user_profiles),
            "avg_conversation_length": sum(
                len(ctx.conversation_history) for ctx in self.active_contexts.values()
            )
            / max(len(self.active_contexts), 1),
            "common_topics": self._get_most_common_topics(),
            "successful_styles": dict(self.global_patterns["successful_styles"]),
        }

    def _get_most_common_topics(self) -> list[str]:
        """Obtenir les topics les plus communs"""
        topic_counts = {}

        for context in self.active_contexts.values():
            for topic in context.active_topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Retourner les 10 plus communs
        return sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    def export_user_profile(self, user_id: str) -> dict[str, Any] | None:
        """Exporter le profil d'un utilisateur"""
        if user_id not in self.user_profiles:
            return None

        profile = self.user_profiles[user_id]
        return {
            "user_id": profile.user_id,
            "expertise_level": profile.expertise_level,
            "preferred_language": profile.preferred_language,
            "preferred_detail_level": profile.preferred_detail_level,
            "domain_interests": profile.domain_interests,
            "preferred_response_style": profile.preferred_response_style,
            "common_topics": profile.common_topics,
            "interaction_count": len(profile.interaction_history),
            "avg_satisfaction": sum(
                turn.satisfaction_score
                for turn in profile.interaction_history
                if turn.satisfaction_score is not None
            )
            / max(
                len(
                    [
                        turn
                        for turn in profile.interaction_history
                        if turn.satisfaction_score is not None
                    ]
                ),
                1,
            ),
        }
