#!/usr/bin/env python3
"""Lance le dashboard Hyperion (API + Frontend)."""

import http.server
import socketserver
import sys
import time
import webbrowser
from pathlib import Path
from threading import Thread

# Ajouter Hyperion au PATH
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_api():
    """Lance l'API FastAPI."""
    import uvicorn

    from hyperion.api.main import app

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")  # Moins verbeux


def run_frontend():
    """Lance le serveur frontend (simple HTTP server)."""
    frontend_dir = Path(__file__).parent.parent / "frontend"

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(frontend_dir), **kwargs)

        def log_message(self, format, *args):
            # Supprimer les logs HTTP
            pass

    with socketserver.TCPServer(("", 3000), Handler) as httpd:
        print("📱 Frontend disponible sur http://localhost:3000")
        httpd.serve_forever()


def main():
    """Lance API + Frontend."""
    print("=" * 70)
    print("🚀 HYPERION DASHBOARD")
    print("=" * 70)
    print()
    print("🔧 Démarrage des services...")
    print()

    # Lancer API en thread
    api_thread = Thread(target=run_api, daemon=True)
    api_thread.start()
    print("✅ API lancée sur http://localhost:8000")

    # Attendre que l'API soit prête
    time.sleep(2)

    # Lancer frontend en thread
    frontend_thread = Thread(target=run_frontend, daemon=True)
    frontend_thread.start()
    print("✅ Frontend lancé sur http://localhost:3000")

    print()
    print("=" * 70)
    print("🎉 DASHBOARD PRÊT !")
    print("=" * 70)
    print()
    print("📱 Dashboard  : http://localhost:3000")
    print("📡 API        : http://localhost:8000")
    print("📚 API Docs   : http://localhost:8000/docs")
    print()
    print("💡 Ctrl+C pour arrêter")
    print()

    # Ouvrir le navigateur automatiquement
    time.sleep(1)
    webbrowser.open("http://localhost:3000")

    try:
        # Garder le programme actif
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Arrêt du dashboard...")
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)
