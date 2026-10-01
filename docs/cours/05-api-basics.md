---
title: "Chapitre 05 - API Basics"
toc: true
description: "Utiliser l'API REST et OpenAI : Intégrer Hyperion dans vos outils"
weight: 6
---

**Utiliser l'API REST et OpenAI** - Intégrer Hyperion dans vos outils

*⏱️ Durée estimée : 40 minutes*

---

## 🎯 **Objectifs de ce Chapitre**

À la fin de ce chapitre, vous saurez :
- ✅ Utiliser les 3 niveaux d'API d'Hyperion (Core, OpenAI, Code Intelligence)
- ✅ Intégrer Hyperion dans vos outils existants
- ✅ Développer des applications qui exploitent Hyperion
- ✅ Gérer l'authentification et les bonnes pratiques

---

## 🏗️ **Architecture API Hyperion**

### 📊 **3 Couches d'API**

```
┌─────────────────────────────────────┐
│         Code Intelligence v2        │  ← Recherche sémantique, ML
├─────────────────────────────────────┤
│         OpenAI Compatible           │  ← Compatible ChatGPT/GPT-4
├─────────────────────────────────────┤
│              Core API               │  ← Repositories, métriques
└─────────────────────────────────────┘
```

### 🌐 **Points d'accès**

- **API Core** : `http://localhost:8000/api/*`
- **OpenAI Compatible** : `http://localhost:8000/api/openai/*`
- **Code Intelligence** : `http://localhost:8000/api/v2/*`
- **Documentation** : `http://localhost:8000/docs`

---

## 📊 **Core API - Repositories et Métriques**

### 🔍 **Endpoints Principales**

#### 📂 **Gestion Repositories**

```bash
# Lister les repositories analysés
curl http://localhost:8000/api/repos

# Informations sur un repository
curl http://localhost:8000/api/repos/mon-projet

# Analyser un nouveau repository
curl -X POST http://localhost:8000/api/repos/analyze \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/repo", "name": "mon-projet"}'
```

#### 📈 **Métriques et Analytics**

```bash
# Métriques principales
curl http://localhost:8000/api/repos/mon-projet/metrics

# Métriques temporelles
curl "http://localhost:8000/api/repos/mon-projet/metrics/timeline?days=30"

# Hotspots (fichiers critiques)
curl http://localhost:8000/api/repos/mon-projet/hotspots

# Analyse équipe
curl http://localhost:8000/api/repos/mon-projet/team-analytics
```

### 💡 **Exemples avec Python**

#### 🐍 **Script d'Analyse Automatique**

```python
import requests
import json
from datetime import datetime, timedelta

class HyperionClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def analyze_repository(self, repo_path, repo_name):
        """Analyser un repository"""
        url = f"{self.base_url}/api/repos/analyze"
        data = {"path": repo_path, "name": repo_name}

        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def get_metrics(self, repo_name):
        """Récupérer les métriques"""
        url = f"{self.base_url}/api/repos/{repo_name}/metrics"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_timeline_metrics(self, repo_name, days=30):
        """Métriques temporelles"""
        url = f"{self.base_url}/api/repos/{repo_name}/metrics/timeline"
        params = {"days": days}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

# Utilisation
client = HyperionClient()

# Analyser un repository
result = client.analyze_repository("/path/to/repo", "my-project")
print(f"Analysis ID: {result['analysis_id']}")

# Récupérer les métriques
metrics = client.get_metrics("my-project")
print(f"Complexity Score: {metrics['architecture']['complexity_score']}")
print(f"Team Score: {metrics['team']['collaboration_score']}")
```

#### 📊 **Dashboard de Métriques**

```python
import matplotlib.pyplot as plt
import pandas as pd

def create_quality_dashboard(repo_name):
    client = HyperionClient()

    # Récupérer métriques temporelles
    timeline = client.get_timeline_metrics(repo_name, days=90)

    # Convertir en DataFrame
    df = pd.DataFrame(timeline['metrics'])
    df['date'] = pd.to_datetime(df['date'])

    # Créer graphiques
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(f'Quality Dashboard - {repo_name}', fontsize=16)

    # Complexité dans le temps
    axes[0,0].plot(df['date'], df['complexity_score'])
    axes[0,0].set_title('Complexity Evolution')
    axes[0,0].set_ylabel('Complexity Score')

    # Maintenabilité
    axes[0,1].plot(df['date'], df['maintainability_index'], color='green')
    axes[0,1].set_title('Maintainability')
    axes[0,1].set_ylabel('Maintainability Index')

    # Detta technique
    axes[1,0].plot(df['date'], df['technical_debt_ratio'], color='red')
    axes[1,0].set_title('Technical Debt')
    axes[1,0].set_ylabel('Debt Ratio')

    # Activité équipe
    axes[1,1].plot(df['date'], df['team_activity'], color='blue')
    axes[1,1].set_title('Team Activity')
    axes[1,1].set_ylabel('Commits per Day')

    plt.tight_layout()
    plt.savefig(f'{repo_name}_dashboard.png', dpi=300)
    plt.show()

# Utilisation
create_quality_dashboard("my-project")
```

---

## 🤖 **OpenAI Compatible API**

### 🔗 **Compatibilité Totale**

L'API OpenAI d'Hyperion est **100% compatible** avec les SDK OpenAI existants.

### 🐍 **Utilisation avec OpenAI SDK**

```python
import openai

# Configuration pour Hyperion
openai.api_base = "http://localhost:8000/api/openai"
openai.api_key = "hyperion-local-key"  # Clé locale

# Utilisation normale comme ChatGPT
def ask_codebase(question, repository="my-project"):
    response = openai.ChatCompletion.create(
        model="hyperion-rag",  # Modèle Hyperion avec RAG
        messages=[
            {
                "role": "system",
                "content": f"You are an AI assistant analyzing the {repository} codebase."
            },
            {"role": "user", "content": question}
        ],
        temperature=0.1,
        max_tokens=1000
    )

    return response.choices[0].message.content

# Exemples d'utilisation
print(ask_codebase("Comment ajouter une nouvelle API endpoint ?"))
print(ask_codebase("Où sont gérées les erreurs dans ce projet ?"))
print(ask_codebase("Quels sont les patterns d'architecture utilisés ?"))
```

### 🌐 **Intégration avec des Outils Existants**

#### 💬 **Slack Bot**

```python
from slack_bolt import App
import openai

# Configuration Slack + Hyperion
app = App(token=os.environ["SLACK_BOT_TOKEN"])
openai.api_base = "http://localhost:8000/api/openai"

@app.message("hyperion")
def handle_hyperion_questions(message, say):
    # Extraire la question
    question = message['text'].replace('hyperion', '').strip()

    # Poser à Hyperion
    response = openai.ChatCompletion.create(
        model="hyperion-rag",
        messages=[{"role": "user", "content": question}],
        temperature=0.1
    )

    # Répondre sur Slack
    say(f"🤖 Hyperion: {response.choices[0].message.content}")

# Lancer le bot
app.start(port=3000)
```

#### 🖥️ **VSCode Extension**

```javascript
// Extension VSCode qui utilise Hyperion
const vscode = require('vscode');
const axios = require('axios');

function activate(context) {
    // Commande pour poser une question au code
    let disposable = vscode.commands.registerCommand('hyperion.askCode', async () => {
        // Récupérer la sélection de code
        const editor = vscode.window.activeTextEditor;
        const selection = editor.selection;
        const selectedText = editor.document.getText(selection);

        // Demander une question à l'utilisateur
        const question = await vscode.window.showInputBox({
            prompt: 'Que voulez-vous savoir sur ce code ?'
        });

        if (question) {
            // Envoyer à Hyperion
            const response = await axios.post('http://localhost:8000/api/openai/chat/completions', {
                model: 'hyperion-rag',
                messages: [
                    {role: 'user', content: `${question}\n\nCode:\n${selectedText}`}
                ]
            });

            // Afficher la réponse
            const answer = response.data.choices[0].message.content;
            vscode.window.showInformationMessage(`Hyperion: ${answer}`);
        }
    });

    context.subscriptions.push(disposable);
}
```

### 📱 **Applications Web**

#### ⚛️ **Interface React**

```jsx
import React, { useState } from 'react';
import OpenAI from 'openai';

const openai = new OpenAI({
    baseURL: 'http://localhost:8000/api/openai',
    apiKey: 'hyperion-local',
    dangerouslyAllowBrowser: true
});

function CodeChat({ repository }) {
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState('');
    const [loading, setLoading] = useState(false);

    const askHyperion = async () => {
        setLoading(true);
        try {
            const response = await openai.chat.completions.create({
                model: 'hyperion-rag',
                messages: [
                    {
                        role: 'system',
                        content: `Analyse du repository ${repository}`
                    },
                    { role: 'user', content: question }
                ],
                temperature: 0.1,
                max_tokens: 800
            });

            setAnswer(response.choices[0].message.content);
        } catch (error) {
            setAnswer(`Erreur: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="code-chat">
            <h2>💬 Chat avec {repository}</h2>

            <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Posez votre question sur le code..."
                rows={3}
                className="question-input"
            />

            <button onClick={askHyperion} disabled={loading}>
                {loading ? '🤔 Réflexion...' : '🚀 Poser la question'}
            </button>

            {answer && (
                <div className="answer">
                    <h3>🤖 Hyperion répond :</h3>
                    <pre>{answer}</pre>
                </div>
            )}
        </div>
    );
}

export default CodeChat;
```

---

## 🔬 **Code Intelligence v2 API**

### 🎯 **API Avancées pour Analyse de Code**

#### 🔍 **Recherche Sémantique**

```bash
# Recherche dans le code
curl -X POST http://localhost:8000/api/v2/repos/mon-projet/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication logic",
    "limit": 10,
    "include_context": true
  }'

# Recherche par similarité de code
curl -X POST http://localhost:8000/api/v2/search/similar \
  -H "Content-Type: application/json" \
  -d '{
    "code_snippet": "def authenticate_user(username, password):",
    "language": "python"
  }'
```

#### 🎯 **Analyse d'Impact**

```bash
# Analyser l'impact d'un changement
curl -X POST http://localhost:8000/api/v2/repos/mon-projet/impact \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "src/auth.py",
    "change_type": "modify",
    "affected_lines": [25, 30]
  }'
```

#### 🤖 **Prédictions ML**

```bash
# Prédiction de risques
curl http://localhost:8000/api/v2/repos/mon-projet/predictions/risk

# Détection d'anomalies
curl http://localhost:8000/api/v2/repos/mon-projet/predictions/anomaly

# Prédiction de bugs
curl "http://localhost:8000/api/v2/repos/mon-projet/predictions/bugs?horizon=30"
```

### 💡 **Client Python Avancé**

```python
class HyperionAdvanced:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def semantic_search(self, repo_name, query, limit=10):
        """Recherche sémantique dans le code"""
        url = f"{self.base_url}/api/v2/repos/{repo_name}/search"
        data = {
            "query": query,
            "limit": limit,
            "include_context": True
        }
        response = self.session.post(url, json=data)
        return response.json()

    def analyze_impact(self, repo_name, file_path, lines=None):
        """Analyser l'impact d'un changement"""
        url = f"{self.base_url}/api/v2/repos/{repo_name}/impact"
        data = {
            "file_path": file_path,
            "change_type": "modify"
        }
        if lines:
            data["affected_lines"] = lines

        response = self.session.post(url, json=data)
        return response.json()

    def get_predictions(self, repo_name, pred_type="risk"):
        """Récupérer prédictions ML"""
        url = f"{self.base_url}/api/v2/repos/{repo_name}/predictions/{pred_type}"
        response = self.session.get(url)
        return response.json()

    def find_similar_code(self, code_snippet, language="python"):
        """Trouver code similaire"""
        url = f"{self.base_url}/api/v2/search/similar"
        data = {
            "code_snippet": code_snippet,
            "language": language
        }
        response = self.session.post(url, json=data)
        return response.json()

# Exemple d'utilisation avancée
client = HyperionAdvanced()

# Recherche sémantique
results = client.semantic_search(
    "mon-projet",
    "error handling middleware"
)

for result in results['matches']:
    print(f"File: {result['file']}")
    print(f"Score: {result['score']:.2f}")
    print(f"Context: {result['context'][:100]}...")
    print("---")

# Analyse d'impact
impact = client.analyze_impact(
    "mon-projet",
    "src/middleware/auth.py",
    lines=[15, 20, 25]
)

print(f"Impact Score: {impact['impact_score']}")
print(f"Affected Components: {len(impact['affected_components'])}")
```

---

## 🔐 **Authentification et Sécurité**

### 🔑 **Configuration JWT**

```yaml
# config.yaml
security:
  jwt_secret_key: "your-secret-key"
  jwt_algorithm: "HS256"
  token_expire_minutes: 1440  # 24h
  api_rate_limit: 100  # requests per minute
```

### 🛡️ **Utilisation avec Authentification**

```python
import jwt
import datetime

class SecureHyperionClient:
    def __init__(self, base_url="http://localhost:8000", api_key=None):
        self.base_url = base_url
        self.api_key = api_key
        self.token = None
        self.session = requests.Session()

    def login(self, username, password):
        """Authentification"""
        url = f"{self.base_url}/api/auth/login"
        data = {"username": username, "password": password}

        response = self.session.post(url, json=data)
        response.raise_for_status()

        self.token = response.json()["access_token"]
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}"
        })

        return self.token

    def refresh_token(self):
        """Renouveler le token"""
        if not self.token:
            raise Exception("No token to refresh")

        url = f"{self.base_url}/api/auth/refresh"
        response = self.session.post(url)
        response.raise_for_status()

        self.token = response.json()["access_token"]
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}"
        })

    def api_request(self, endpoint, method="GET", data=None):
        """Requête API avec gestion d'erreurs"""
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = self.session.get(url)
            elif method == "POST":
                response = self.session.post(url, json=data)
            elif method == "PUT":
                response = self.session.put(url, json=data)
            elif method == "DELETE":
                response = self.session.delete(url)

            # Gestion du renouvellement automatique
            if response.status_code == 401:
                self.refresh_token()
                # Retry
                if method == "GET":
                    response = self.session.get(url)
                elif method == "POST":
                    response = self.session.post(url, json=data)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            raise

# Utilisation sécurisée
client = SecureHyperionClient()
client.login("admin", "password")

# Maintenant toutes les requêtes sont authentifiées
metrics = client.api_request("/api/repos/mon-projet/metrics")
```

---

## 📊 **Monitoring et Performance**

### 📈 **Métriques API**

```bash
# Métriques du serveur API
curl http://localhost:8000/api/metrics/server

# Performance par endpoint
curl http://localhost:8000/api/metrics/endpoints

# Utilisation des ressources
curl http://localhost:8000/api/metrics/resources
```

### ⚡ **Optimisation des Requêtes**

```python
# Utilisation du cache et pagination
def get_metrics_efficiently(client, repo_name):
    # Utiliser cache pour métriques récentes
    metrics = client.api_request(
        f"/api/repos/{repo_name}/metrics?use_cache=true"
    )

    # Pagination pour gros datasets
    all_commits = []
    page = 1
    while True:
        commits = client.api_request(
            f"/api/repos/{repo_name}/commits?page={page}&limit=100"
        )
        if not commits['items']:
            break
        all_commits.extend(commits['items'])
        page += 1

    return metrics, all_commits

# Requêtes parallèles pour performance
import asyncio
import aiohttp

async def get_multiple_repos_data(repo_names):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for repo in repo_names:
            task = get_repo_metrics(session, repo)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return dict(zip(repo_names, results))

async def get_repo_metrics(session, repo_name):
    url = f"http://localhost:8000/api/repos/{repo_name}/metrics"
    async with session.get(url) as response:
        return await response.json()
```

---

## 🎉 **Maîtrise des APIs !**

### ✅ **Ce que Vous Savez Maintenant**

- 🌐 **Core API** : Repositories, métriques, analytics
- 🤖 **OpenAI API** : Compatibilité totale avec SDK existants
- 🔬 **Code Intelligence v2** : Recherche sémantique, ML, prédictions
- 🔐 **Sécurité** : Authentification, tokens, rate limiting
- 📊 **Performance** : Cache, pagination, requêtes parallèles

### 🚀 **Applications Possibles**

- Dashboard custom pour votre équipe
- Intégration Slack/Teams
- Extension IDE (VSCode, IntelliJ)
- CI/CD avec quality gates
- Monitoring automatique

### 📚 **Prochaines Étapes**

Vous maîtrisez maintenant les APIs d'Hyperion !

👉 **Continuez avec** : [Chapitre 06 - RAG et Chat](06-rag-chat)

Au prochain chapitre :
- Comprendre le RAG en profondeur
- Optimiser les questions pour de meilleures réponses
- Chat avancé avec votre codebase
- Intégrations chat (Discord, Slack, etc.)

---

## 📖 **Récapitulatif du Chapitre**

### ✅ **APIs Maîtrisées :**
- **Core API** : Analyse repositories et métriques
- **OpenAI Compatible** : Chat avec votre code
- **Code Intelligence v2** : Recherche et prédictions ML
- **Auth & Security** : Authentification sécurisée

### 🔧 **Compétences Acquises :**
- Intégration dans applications existantes
- Scripts d'automation et monitoring
- Dashboard et visualisations
- Optimisation performance

---

*Excellent ! Vous pouvez maintenant intégrer Hyperion partout. Rendez-vous au [Chapitre 06](06-rag-chat) !* 🌐

---

*Cours Hyperion - Chapitre 05*