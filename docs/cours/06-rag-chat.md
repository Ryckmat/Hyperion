# 🤖 Chapitre 06 - RAG et Chat

**Interroger vos repos avec l'IA** - Maîtriser le Retrieval Augmented Generation

*⏱️ Durée estimée : 30 minutes*

---

## 🎯 **Objectifs de ce Chapitre**

À la fin de ce chapitre, vous maîtriserez :
- ✅ Le fonctionnement du RAG (Retrieval Augmented Generation)
- ✅ Comment poser les bonnes questions pour obtenir de meilleures réponses
- ✅ Interpréter les sources et la contextualisation
- ✅ Utiliser différentes interfaces de chat (Web, API, intégrations)

---

## 🧠 **Comprendre le RAG**

### 🔍 **Qu'est-ce que le RAG ?**

**RAG** = Retrieval Augmented Generation = **Génération Augmentée par Recherche**

```
Votre Question
     ↓
🔍 Recherche dans la base de connaissance (votre code)
     ↓
📊 Récupération des passages pertinents
     ↓
🤖 LLM génère une réponse basée sur ces sources
     ↓
💬 Réponse + Sources exactes
```

### 🏗️ **Architecture RAG Hyperion**

```
Repository Git
     ↓
📄 Extraction documentation + code
     ↓
✂️ Découpage en chunks (512 tokens)
     ↓
🧮 Vectorisation (embeddings)
     ↓
🗄️ Stockage Qdrant (base vectorielle)
     ↓
🔍 Recherche similarité cosinus
     ↓
🤖 LLM local (Ollama) + contexte
```

### ⚡ **Avantages du RAG Local**

- ✅ **Réponses précises** : Basées sur VOTRE code exactement
- ✅ **Sources tracées** : Fichier et ligne exacte pour chaque info
- ✅ **Contexte préservé** : Comprend l'architecture de votre projet
- ✅ **100% privé** : Aucune donnée n'est envoyée à l'extérieur
- ✅ **Temps réel** : Toujours à jour avec votre dernière version

---

## 💬 **Interfaces de Chat**

### 🌐 **Interface Web (Recommandée)**

```bash
# Démarrer Hyperion
hyperion serve

# Ouvrir dans le navigateur
# http://localhost:8000/chat
```

**Fonctionnalités Web :**
- 💬 Chat en temps réel
- 📎 Affichage des sources cliquables
- 🔍 Historique des conversations
- 📊 Métriques de pertinence
- 🎯 Suggestions de questions

### 📱 **Chat via API**

```bash
# Question simple
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Comment ajouter une nouvelle route ?",
    "repository": "mon-projet"
  }'

# Chat avec contexte
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Et comment gérer les erreurs sur cette route ?",
    "repository": "mon-projet",
    "conversation_id": "conv-123"
  }'
```

### 🔗 **Intégrations Externes**

#### 💬 **Open WebUI (Interface ChatGPT-like)**

```bash
# Démarrer Open WebUI connecté à Hyperion
docker run -d -p 3001:8080 \
  -e OPENAI_API_BASE_URL=http://localhost:8000/api/openai \
  -e OPENAI_API_KEY=hyperion-local \
  ghcr.io/open-webui/open-webui:main

# Accéder à http://localhost:3001
```

#### 🤖 **Discord Bot**

```python
import discord
import openai

openai.api_base = "http://localhost:8000/api/openai"

class CodeBot(discord.Client):
    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith('!code'):
            question = message.content[5:]  # Enlever '!code'

            response = openai.ChatCompletion.create(
                model="hyperion-rag",
                messages=[
                    {"role": "user", "content": question}
                ]
            )

            await message.reply(response.choices[0].message.content)

bot = CodeBot()
bot.run('YOUR_DISCORD_TOKEN')
```

---

## 🎯 **Poser les Bonnes Questions**

### ✅ **Questions Efficaces**

#### 🏗️ **Architecture et Structure**
```
✅ "Comment est organisé ce projet ?"
✅ "Où se trouve la logique de l'authentification ?"
✅ "Quels sont les modules principaux et leurs responsabilités ?"
✅ "Comment les données circulent-elles dans l'application ?"
```

#### 🔧 **Implémentation Pratique**
```
✅ "Comment ajouter une nouvelle API endpoint ?"
✅ "Où et comment configurer la base de données ?"
✅ "Comment implémenter la validation des données ?"
✅ "Quels sont les patterns utilisés pour la gestion des erreurs ?"
```

#### 🧪 **Tests et Qualité**
```
✅ "Comment écrire des tests pour ce module ?"
✅ "Où sont les exemples de tests existants ?"
✅ "Comment mocker les dépendances externes ?"
✅ "Quelle est la stratégie de tests de ce projet ?"
```

#### 📚 **Documentation et Exemples**
```
✅ "Montre-moi des exemples d'utilisation de cette fonction"
✅ "Comment configurer l'environnement de développement ?"
✅ "Quelles sont les conventions de code de ce projet ?"
✅ "Comment déployer cette application ?"
```

### ❌ **Questions Moins Efficaces**

```
❌ "Comment ça marche ?" (trop vague)
❌ "Où est le code ?" (pas de contexte)
❌ "C'est quoi ce truc ?" (pas constructif)
❌ "Peut tu débugger ça ?" (sans contexte du bug)
```

### 💡 **Techniques pour Améliorer vos Questions**

#### 🎯 **Soyez Spécifique**
```
❌ "Comment gérer les erreurs ?"
✅ "Comment gérer les erreurs 404 dans les API endpoints ?"

❌ "Où est la config ?"
✅ "Où se trouve la configuration de la base de données ?"
```

#### 📍 **Donnez du Contexte**
```
✅ "Je veux ajouter une validation email sur le formulaire d'inscription.
    Comment faire ça dans ce projet ?"

✅ "J'ai une erreur 'Connection refused' lors du test de l'API.
    Comment debugger les problèmes de connexion ?"
```

#### 🔄 **Questions de Suivi**
```
1️⃣ "Comment ajouter une nouvelle route ?"
2️⃣ "Et comment ajouter des middlewares à cette route ?"
3️⃣ "Comment tester cette route avec des données mockées ?"
```

---

## 📊 **Comprendre les Réponses**

### 🎯 **Anatomie d'une Réponse Hyperion**

```
🤖 Hyperion: Pour ajouter une nouvelle route dans cette application Flask :

📝 **Méthode recommandée :**

1. **Créer la route dans un blueprint** (recommandé pour ce projet)
   ```python
   # Dans src/blueprints/api.py
   @api_bp.route('/nouvelle-route', methods=['GET', 'POST'])
   def ma_nouvelle_route():
       return jsonify({"message": "Hello World"})
   ```

2. **Enregistrer le blueprint** (déjà fait dans ce projet)
   Le blueprint est enregistré dans `src/app.py` ligne 25

3. **Ajouter la validation** (pattern utilisé dans ce projet)
   Utiliser `marshmallow` comme dans les autres endpoints

📍 **Sources exactes :**
- src/blueprints/api.py:15-30 (exemples similaires)
- src/app.py:25 (enregistrement blueprint)
- src/schemas/api_schemas.py:10-25 (validation patterns)
- docs/api.md:45-60 (documentation patterns)

💡 **Bonnes pratiques de ce projet :**
- Utiliser les blueprints pour l'organisation
- Validation avec marshmallow
- Tests dans tests/test_api.py
```

### 🔍 **Interpréter les Sources**

#### 📂 **Types de Sources**
- **Code source** : `.py`, `.js`, `.java` - Implémentation réelle
- **Documentation** : `.md`, `.rst`, `.txt` - Explications
- **Configuration** : `.yaml`, `.json`, `.env` - Paramètres
- **Tests** : `test_*.py`, `*.spec.js` - Exemples d'usage

#### 📊 **Score de Pertinence**
```
🟢 0.8-1.0 : Très pertinent, source directe
🟡 0.6-0.8 : Pertinent, contexte utile
🟠 0.4-0.6 : Moyennement pertinent
🔴 <0.4   : Peu pertinent (peut être ignoré)
```

#### 🎯 **Actions Recommandées**
- **Score >0.8** → Examiner ce fichier en priorité
- **Multiple sources** → Pattern confirmé dans le projet
- **Sources récentes** → Approche actuelle du projet
- **Sources de tests** → Exemples d'utilisation validés

---

## ⚡ **Optimiser les Performances du Chat**

### 🚀 **Configuration Performance**

```yaml
# config.yaml
rag:
  # Modèle d'embedding (vitesse vs qualité)
  embedding_model: "all-MiniLM-L6-v2"  # Rapide
  # embedding_model: "all-mpnet-base-v2"  # Plus précis mais lent

  # Taille des chunks
  chunk_size: 512        # Plus petit = plus précis
  chunk_overlap: 50      # Chevauchement pour continuité

  # Recherche
  top_k_results: 5       # Nombre de sources récupérées
  similarity_threshold: 0.6  # Seuil de pertinence

  # LLM
  max_tokens: 1000       # Longueur max réponse
  temperature: 0.1       # Créativité (0 = factuel, 1 = créatif)
```

### ⚡ **Modes de Vitesse**

```bash
# Mode ultra-rapide (<3s)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Comment ajouter une route ?",
    "repository": "mon-projet",
    "speed_mode": "ultra_fast"
  }'

# Mode équilibré (5-10s)
curl -X POST http://localhost:8000/api/chat \
  -d '{"speed_mode": "balanced"}'

# Mode précision maximale (10-30s)
curl -X POST http://localhost:8000/api/chat \
  -d '{"speed_mode": "high_precision"}'
```

### 📊 **Cache et Optimisations**

```python
# Client avec cache intelligent
class CachedHyperionChat:
    def __init__(self):
        self.cache = {}
        self.base_url = "http://localhost:8000"

    def ask(self, question, repository, use_cache=True):
        # Vérifier cache
        cache_key = f"{repository}:{hash(question)}"
        if use_cache and cache_key in self.cache:
            print("📦 Réponse depuis cache")
            return self.cache[cache_key]

        # Requête API
        response = requests.post(f"{self.base_url}/api/chat", json={
            "message": question,
            "repository": repository
        })

        result = response.json()

        # Mettre en cache
        if use_cache:
            self.cache[cache_key] = result

        return result

# Usage avec cache
chat = CachedHyperionChat()
answer1 = chat.ask("Comment ajouter une route ?", "flask-app")
answer2 = chat.ask("Comment ajouter une route ?", "flask-app")  # Depuis cache
```

---

## 🔧 **Configuration Avancée du RAG**

### 🎯 **Personnalisation par Repository**

```yaml
# .hyperion/repo-config.yaml dans votre projet
rag_config:
  # Focus sur certains types de fichiers
  include_patterns:
    - "*.py"
    - "*.md"
    - "docs/**"
    - "README*"

  # Exclure certains dossiers
  exclude_patterns:
    - "node_modules/**"
    - "venv/**"
    - "*.log"

  # Contexte personnalisé
  system_context: |
    Tu es un assistant spécialisé dans ce projet Flask.
    Ce projet utilise SQLAlchemy, Marshmallow et pytest.
    Réponds toujours en français et donne des exemples de code.

  # Prompts spécialisés
  prompt_templates:
    architecture: "Explique l'architecture de {file} dans le contexte de ce projet Flask"
    testing: "Comment tester {function} en utilisant pytest et les patterns de ce projet ?"
```

### 🎨 **Modèles LLM Spécialisés**

```bash
# Modèles disponibles par profil d'usage
ollama list

# Ultra-rapide (<3s) - Développement quotidien
llama3.2:1b

# Équilibré (5-10s) - Analyses moyennes
llama3.1:8b

# Précis (10-30s) - Analyses complexes
qwen2.5:14b

# Expert (30s+) - Architecture et refactoring
qwen2.5:32b
```

### 🔄 **Sélection Automatique de Modèle**

```python
def choose_model_for_question(question):
    """Choisir le bon modèle selon la complexité"""

    # Questions simples → modèle rapide
    simple_patterns = [
        "où se trouve",
        "comment importer",
        "quelle commande",
        "où est défini"
    ]

    # Questions complexes → modèle précis
    complex_patterns = [
        "architecture",
        "refactoring",
        "performance",
        "conception"
    ]

    question_lower = question.lower()

    if any(pattern in question_lower for pattern in complex_patterns):
        return "qwen2.5:14b"  # Modèle précis
    elif any(pattern in question_lower for pattern in simple_patterns):
        return "llama3.2:1b"  # Modèle rapide
    else:
        return "llama3.1:8b"  # Modèle équilibré
```

---

## 📱 **Intégrations Avancées**

### 💬 **Bot Slack Intelligent**

```python
from slack_bolt import App
import openai

app = App(token=os.environ["SLACK_BOT_TOKEN"])
openai.api_base = "http://localhost:8000/api/openai"

@app.event("app_mention")
def handle_mention(event, say):
    # Extraire repository du nom du channel
    channel_name = event.get('channel_name', 'general')
    repo_name = channel_name.replace('-', '_')  # slack-bot → slack_bot

    # Question de l'utilisateur
    question = event['text'].split('>', 1)[1].strip()  # Enlever la mention

    # Contexte Slack
    user_id = event['user']

    response = openai.ChatCompletion.create(
        model="hyperion-rag",
        messages=[
            {
                "role": "system",
                "content": f"Tu es l'assistant du repository {repo_name}. "
                          f"Réponds à <@{user_id}> de manière concise pour Slack."
            },
            {"role": "user", "content": question}
        ],
        max_tokens=500,  # Limité pour Slack
        temperature=0.1
    )

    answer = response.choices[0].message.content

    # Format Slack avec sources
    say(f"🤖 *Hyperion ({repo_name})*\n\n{answer}")

# Réactions rapides
@app.event("reaction_added")
def handle_reaction(event):
    if event['reaction'] == 'hyperion':
        # Auto-analyser le message
        # ... logique d'analyse automatique
        pass
```

### 🎯 **Extension VSCode Avancée**

```typescript
// extension.ts
import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    // Provider pour hover avec Hyperion
    const hoverProvider = vscode.languages.registerHoverProvider('*', {
        provideHover(document, position, token) {
            const wordRange = document.getWordRangeAtPosition(position);
            if (!wordRange) return;

            const word = document.getText(wordRange);
            const line = document.lineAt(position.line);

            // Poser question contextuelle à Hyperion
            const question = `Explique la fonction "${word}" dans le fichier ${document.fileName}`;

            return queryHyperion(question).then(response => {
                return new vscode.Hover([
                    new vscode.MarkdownString(`**Hyperion**: ${response}`)
                ]);
            });
        }
    });

    // Commande pour analyser selection
    const analyzeCommand = vscode.commands.registerCommand('hyperion.analyzeSelection', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;

        const selection = editor.selection;
        const selectedText = editor.document.getText(selection);

        if (selectedText) {
            const question = `Analyse ce code et explique ce qu'il fait:\n\n${selectedText}`;
            const response = await queryHyperion(question);

            // Afficher dans un panel
            const panel = vscode.window.createWebviewPanel(
                'hyperion',
                'Hyperion Analysis',
                vscode.ViewColumn.Two,
                {}
            );

            panel.webview.html = `
                <html>
                <body>
                    <h2>🤖 Hyperion Analysis</h2>
                    <div style="white-space: pre-wrap;">${response}</div>
                </body>
                </html>
            `;
        }
    });

    context.subscriptions.push(hoverProvider, analyzeCommand);
}

async function queryHyperion(question: string): Promise<string> {
    // Implementation de la requête HTTP vers Hyperion
    // ...
}
```

---

## 🎉 **Maîtrise du RAG et Chat !**

### ✅ **Ce que Vous Maîtrisez Maintenant**

- 🧠 **RAG Concepts** : Comment fonctionne la recherche augmentée
- 💬 **Questions Efficaces** : Techniques pour obtenir de meilleures réponses
- 🔍 **Sources et Contexte** : Interpréter et exploiter les résultats
- ⚡ **Performance** : Optimiser vitesse et précision
- 🔧 **Configuration** : Personnaliser le comportement pour vos projets
- 📱 **Intégrations** : Slack, Discord, VSCode, et plus

### 🚀 **Utilisations Avancées**

- Assistant de développement personnalisé
- Onboarding automatique des nouvelles recrues
- Documentation interactive
- Code review assisté par IA
- Knowledge base d'équipe

### 📚 **Prochaines Étapes**

👉 **Continuez avec** : [Chapitre 07 - Infrastructure ML](07-infrastructure-ml.md)

Au prochain chapitre, vous découvrirez :
- Les 5 modèles ML d'Hyperion en détail
- Feature engineering et prédictions
- MLflow et model registry
- Optimisation des modèles pour votre contexte

---

*Parfait ! Vous maîtrisez maintenant le chat intelligent avec votre code. Rendez-vous au [Chapitre 07](07-infrastructure-ml.md) !* 🤖

---

*Cours Hyperion v2.7.0 - Chapitre 06*