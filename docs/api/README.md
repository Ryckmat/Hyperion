# 🚀 API Documentation Hyperion v2.7

## Overview

Hyperion expose une API REST complète pour interagir avec la plateforme d'analyse de code et RAG.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required for the API endpoints.

## Core Endpoints

### Health Check
```http
GET /api/health
```

Returns the health status of all services.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "qdrant": "connected",
    "ollama": "connected",
    "neo4j": "connected"
  },
  "version": "2.7.0"
}
```

### Repository Analysis

#### Get Repository Functions
```http
GET /api/v2/repos/{repo}/functions
```

Returns all functions detected in a repository.

#### Get Repository Stats
```http
GET /api/v2/repos/{repo}/stats
```

Returns analysis statistics for a repository.

### RAG Chat

#### Chat with Repository
```http
POST /api/chat
```

Interact with the repository using natural language.

**Request Body:**
```json
{
  "question": "What does the main function do?",
  "repo": "my-repository"
}
```

**Response:**
```json
{
  "answer": "The main function initializes the application...",
  "sources": [
    {
      "file": "src/main.py",
      "line": 15,
      "content": "def main():"
    }
  ]
}
```

### Anomaly Detection

#### Scan for Anomalies
```http
POST /api/v2/anomaly/scan
```

Scan repository for code anomalies and complexity issues.

**Request Body:**
```json
{
  "repo": "my-repository",
  "types": ["complexity", "security", "patterns"]
}
```

## WebSocket Endpoints

### Real-time Analysis
```
ws://localhost:8000/ws/analysis
```

Real-time updates during repository analysis.

## Error Handling

All endpoints follow standard HTTP status codes:

- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error

Error responses include details:
```json
{
  "error": "Repository not found",
  "code": 404,
  "timestamp": "2025-12-26T01:33:00Z"
}
```

## Rate Limiting

Currently no rate limiting is implemented.

## OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Examples

### Analyze a Repository

```bash
# 1. Health check
curl http://localhost:8000/api/health

# 2. Get repository functions
curl http://localhost:8000/api/v2/repos/my-repo/functions

# 3. Ask a question about the code
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"How many files are in this repository?","repo":"my-repo"}'

# 4. Scan for anomalies
curl -X POST http://localhost:8000/api/v2/anomaly/scan \
  -H "Content-Type: application/json" \
  -d '{"repo":"my-repo","types":["complexity"]}'
```

### Python Client Example

```python
import requests

# Initialize client
base_url = "http://localhost:8000"

# Health check
response = requests.get(f"{base_url}/api/health")
print(response.json())

# Chat with repository
chat_data = {
    "question": "What are the main components of this system?",
    "repo": "hyperion"
}
response = requests.post(f"{base_url}/api/chat", json=chat_data)
print(response.json()["answer"])
```

## SDK and Libraries

- **Python SDK**: Available in `src/hyperion/sdk/`
- **JavaScript SDK**: Coming soon
- **CLI**: `hyperion` command-line tool

For detailed API schema, see the interactive documentation at `/docs`.