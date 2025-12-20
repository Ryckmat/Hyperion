#!/usr/bin/env python3
"""Test de connexion Neo4j."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def test_neo4j_connection():
    """Teste la connexion à Neo4j."""
    
    try:
        from neo4j import GraphDatabase
    except ImportError:
        print("❌ Package neo4j non installé")
        print("📦 Installer avec : pip install neo4j --break-system-packages")
        sys.exit(1)
    
    # Charger config depuis .env
    from hyperion.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE
    
    print("=" * 70)
    print("🔍 TEST CONNEXION NEO4J")
    print("=" * 70)
    print(f"\n📡 URI      : {NEO4J_URI}")
    print(f"👤 User     : {NEO4J_USER}")
    print(f"🗄️  Database : {NEO4J_DATABASE}")
    print(f"🔑 Password : {'*' * len(NEO4J_PASSWORD)}")
    
    print(f"\n⏳ Connexion en cours...")
    
    try:
        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        
        # Vérifier la connexion
        driver.verify_connectivity()
        
        print("✅ Connexion réussie !")
        
        # Tester une requête simple
        with driver.session(database=NEO4J_DATABASE) as session:
            result = session.run("RETURN 1 AS test")
            record = result.single()
            
            if record["test"] == 1:
                print("✅ Requête test OK !")
            
            # Compter les nœuds existants
            result = session.run("MATCH (n) RETURN count(n) AS count")
            count = result.single()["count"]
            print(f"✅ Nœuds existants : {count}")
        
        driver.close()
        
        print("\n" + "=" * 70)
        print("🎉 NEO4J EST PRÊT POUR HYPERION !")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        print("\n💡 Vérifier que :")
        print("   1. Neo4j Desktop est démarré (bouton Start)")
        print("   2. Le mot de passe dans .env est correct")
        print("   3. Le port 7687 est disponible")
        sys.exit(1)


if __name__ == "__main__":
    test_neo4j_connection()
