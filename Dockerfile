# ============================================================================
# Dockerfile pour Hyperion v2.7 - API Principal
# ============================================================================

FROM python:3.11-slim

# Métadonnées
LABEL maintainer="Matthieu Ryckman <contact@ryckmat.dev>"
LABEL version="2.7.0"
LABEL description="Hyperion Git Repository Profiler & Knowledge Graph Platform with RAG"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    HYPERION_HOME=/app

# Dépendances système
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Répertoire de travail
WORKDIR /app

# Copier les fichiers de configuration Python
COPY pyproject.toml setup.py requirements.txt README.md ./
COPY requirements-dev.txt ./

# Installation des dépendances Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY src/ ./src/
COPY templates/ ./templates/
COPY scripts/ ./scripts/

# Installation du package Hyperion
RUN pip install -e .

# Créer les répertoires de données
RUN mkdir -p /app/data/repositories \
             /app/data/ml/feature_store \
             /app/modeles \
             /app/mlruns \
             /app/logs

# Créer utilisateur non-root
RUN groupadd -r hyperion && useradd -r -g hyperion -d /app hyperion && \
    chown -R hyperion:hyperion /app

USER hyperion

# Sanity check
RUN hyperion --help

# Port exposé
EXPOSE 8000

# Point d'entrée par défaut
CMD ["python", "scripts/dev/run_api.py"]