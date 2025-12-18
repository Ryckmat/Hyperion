#!/usr/bin/env python3
"""Lance l'API Hyperion."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == "__main__":
    import uvicorn
    from hyperion.api.main import app
    
    print("=" * 70)
    print("🚀 HYPERION API")
    print("=" * 70)
    print("\n📡 Démarrage sur http://localhost:8000")
    print("📚 Documentation : http://localhost:8000/docs")
    print("🔄 Health check : http://localhost:8000/api/health")
    print("\n⏳ Lancement en cours...\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload en dev
        log_level="info"
    )
