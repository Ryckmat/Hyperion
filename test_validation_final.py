#!/usr/bin/env python3
"""Test de validation finale Hyperion v2 pour note 8/10."""

import time
import requests
import json
from typing import Dict, List

API_BASE = "http://localhost:8000"

class HyperionV2Validator:
    """Validateur pour les 8 moteurs Hyperion v2."""

    def __init__(self):
        self.results = {}
        self.total_score = 0
        self.max_score = 40  # 8 moteurs x 5 points

    def test_rag_engine(self) -> float:
        """Test RAG & Compréhension Basique (5 points)."""
        print("🔍 Test 1: RAG & Compréhension Basique")

        tests = [
            {
                "question": "Où se trouve la logique de gestion des sessions HTTP dans requests ?",
                "expected_keywords": ["sessions.py", "Session"],
                "points": 2
            },
            {
                "question": "Comment requests gère-t-il les cookies ?",
                "expected_keywords": ["RequestsCookieJar", "set_cookie", "update"],
                "points": 3
            }
        ]

        score = 0
        for test in tests:
            try:
                start_time = time.time()
                resp = requests.post(
                    f"{API_BASE}/api/chat",
                    json={"question": test["question"], "repo": "requests"},
                    timeout=30
                )
                duration = time.time() - start_time

                if resp.status_code == 200:
                    answer = resp.json().get("answer", "")
                    sources = resp.json().get("sources", [])

                    # Vérifier présence keywords
                    found_keywords = sum(1 for kw in test["expected_keywords"] if kw.lower() in answer.lower())
                    keyword_score = (found_keywords / len(test["expected_keywords"])) * test["points"]

                    # Bonus pour sources
                    source_bonus = 0.5 if len(sources) > 0 else 0

                    # Malus pour temps
                    time_malus = 0.5 if duration > 15 else 0

                    test_score = max(0, keyword_score + source_bonus - time_malus)
                    score += test_score

                    print(f"   ✓ {test['question'][:50]}... Score: {test_score:.1f}/{test['points']} ({duration:.1f}s)")
                else:
                    print(f"   ✗ API Error: {resp.status_code}")

            except Exception as e:
                print(f"   ✗ Exception: {e}")

        print(f"   📊 RAG Score: {score:.1f}/5.0")
        return score

    def test_neo4j_code_engine(self) -> float:
        """Test Neo4j v2 Code Understanding (5 points)."""
        print("🔍 Test 2: Neo4j v2 Code Understanding")

        score = 0

        # Test 1: Functions endpoint
        try:
            resp = requests.get(f"{API_BASE}/api/v2/repos/requests/functions?limit=10")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("count", 0) >= 10:
                    score += 2
                    print(f"   ✓ Functions: {data['count']} found")
                else:
                    print(f"   ⚠ Functions: only {data.get('count', 0)} found")
            else:
                print(f"   ✗ Functions API error: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Functions error: {e}")

        # Test 2: Classes endpoint
        try:
            resp = requests.get(f"{API_BASE}/api/v2/repos/requests/classes?limit=10")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("count", 0) >= 5:
                    score += 1.5
                    print(f"   ✓ Classes: {data['count']} found")
                else:
                    print(f"   ⚠ Classes: only {data.get('count', 0)} found")
            else:
                print(f"   ✗ Classes API error: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Classes error: {e}")

        # Test 3: Stats
        try:
            resp = requests.get(f"{API_BASE}/api/v2/repos/requests/stats")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("functions", 0) >= 100:
                    score += 1.5
                    print(f"   ✓ Stats: {data['functions']} functions, {data.get('classes', 0)} classes")
                else:
                    print(f"   ⚠ Stats: only {data.get('functions', 0)} functions")
            else:
                print(f"   ✗ Stats API error: {resp.status_code}")
        except Exception as e:
            print(f"   ✗ Stats error: {e}")

        print(f"   📊 Neo4j Score: {score:.1f}/5.0")
        return score

    def test_impact_analysis_engine(self) -> float:
        """Test Impact Analysis Engine (5 points)."""
        print("🔍 Test 3: Impact Analysis Engine")

        score = 0

        try:
            payload = {
                "repo": "requests",
                "file": "src/requests/sessions.py",
                "changes": ["Session.request"]
            }

            resp = requests.post(
                f"{API_BASE}/api/v2/impact/analyze",
                json=payload,
                timeout=20
            )

            if resp.status_code == 200:
                data = resp.json()

                # Vérifier présence des champs requis
                if "affected_functions" in data and len(data["affected_functions"]) > 0:
                    score += 2
                    print(f"   ✓ Affected functions: {len(data['affected_functions'])}")

                if "risk_level" in data and data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]:
                    score += 1.5
                    print(f"   ✓ Risk level: {data['risk_level']}")

                if "impact_summary" in data:
                    score += 1.5
                    print(f"   ✓ Impact summary: {data['impact_summary']}")

            else:
                print(f"   ✗ Impact API error: {resp.status_code}")

        except Exception as e:
            print(f"   ✗ Impact error: {e}")

        print(f"   📊 Impact Score: {score:.1f}/5.0")
        return score

    def test_anomaly_detection_engine(self) -> float:
        """Test Anomaly Detection Engine (5 points)."""
        print("🔍 Test 4: Anomaly Detection Engine")

        score = 0

        try:
            payload = {
                "repo": "requests",
                "types": ["complexity", "size"]
            }

            resp = requests.post(
                f"{API_BASE}/api/v2/anomaly/scan",
                json=payload,
                timeout=20
            )

            if resp.status_code == 200:
                data = resp.json()

                # Vérifier détection anomalies
                if data.get("total_found", 0) > 0:
                    score += 2
                    print(f"   ✓ Anomalies detected: {data['total_found']}")

                if "severity_summary" in data:
                    score += 1.5
                    summary = data["severity_summary"]
                    print(f"   ✓ Severity: HIGH:{summary.get('HIGH', 0)} MEDIUM:{summary.get('MEDIUM', 0)} LOW:{summary.get('LOW', 0)}")

                if data.get("anomalies") and len(data["anomalies"]) > 0:
                    anomaly = data["anomalies"][0]
                    if "suggestion" in anomaly:
                        score += 1.5
                        print(f"   ✓ Suggestions provided: {anomaly['type']}")

            else:
                print(f"   ✗ Anomaly API error: {resp.status_code}")

        except Exception as e:
            print(f"   ✗ Anomaly error: {e}")

        print(f"   📊 Anomaly Score: {score:.1f}/5.0")
        return score

    def test_code_search_engine(self) -> float:
        """Test Code Understanding/Search Engine (5 points)."""
        print("🔍 Test 5: Code Understanding/Search Engine")

        score = 0

        try:
            payload = {
                "query": "session management",
                "repo": "requests",
                "type": "function"
            }

            resp = requests.post(
                f"{API_BASE}/api/v2/understanding/search",
                json=payload,
                timeout=25
            )

            if resp.status_code == 200:
                data = resp.json()

                if "answer" in data and len(data["answer"]) > 50:
                    score += 2.5
                    print(f"   ✓ Search answer: {len(data['answer'])} chars")

                if "sources" in data and len(data["sources"]) > 0:
                    score += 1.5
                    print(f"   ✓ Sources: {len(data['sources'])}")

                if data.get("type") == "semantic_search":
                    score += 1
                    print(f"   ✓ Semantic search confirmed")

            else:
                print(f"   ✗ Search API error: {resp.status_code}")

        except Exception as e:
            print(f"   ✗ Search error: {e}")

        print(f"   📊 Search Score: {score:.1f}/5.0")
        return score

    def test_code_exploration_engine(self) -> float:
        """Test Code Exploration Engine (5 points)."""
        print("🔍 Test 6: Code Exploration Engine")

        score = 0

        try:
            # Test exploration avec pattern session
            resp = requests.get(
                f"{API_BASE}/api/v2/understanding/requests/explore?pattern=session",
                timeout=15
            )

            if resp.status_code == 200:
                data = resp.json()

                if data.get("results") and len(data["results"]) > 0:
                    score += 3
                    print(f"   ✓ Exploration results: {len(data['results'])}")

                    # Vérifier qualité des résultats
                    result = data["results"][0]
                    if "file" in result and "signature" in result:
                        score += 1
                        print(f"   ✓ Result quality: {result['name']} in {result['file']}")

                if data.get("type") == "code_exploration":
                    score += 1
                    print(f"   ✓ Exploration type confirmed")

            else:
                print(f"   ✗ Exploration API error: {resp.status_code}")

        except Exception as e:
            print(f"   ✗ Exploration error: {e}")

        print(f"   📊 Exploration Score: {score:.1f}/5.0")
        return score

    def test_performance(self) -> float:
        """Test Performance Global (5 points)."""
        print("🔍 Test 7: Performance Global")

        score = 0

        # Test 1: Temps réponse RAG
        try:
            start = time.time()
            resp = requests.post(
                f"{API_BASE}/api/chat",
                json={"question": "Où est l'authentification ?", "repo": "requests"},
                timeout=15
            )
            rag_time = time.time() - start

            if rag_time < 10:
                score += 2
                print(f"   ✓ RAG performance: {rag_time:.1f}s")
            else:
                print(f"   ⚠ RAG slow: {rag_time:.1f}s")

        except Exception as e:
            print(f"   ✗ RAG performance error: {e}")

        # Test 2: Temps réponse Neo4j
        try:
            start = time.time()
            resp = requests.get(f"{API_BASE}/api/v2/repos/requests/functions?limit=20")
            neo4j_time = time.time() - start

            if neo4j_time < 3:
                score += 2
                print(f"   ✓ Neo4j performance: {neo4j_time:.1f}s")
            else:
                print(f"   ⚠ Neo4j slow: {neo4j_time:.1f}s")

        except Exception as e:
            print(f"   ✗ Neo4j performance error: {e}")

        # Test 3: Health check v2
        try:
            resp = requests.get(f"{API_BASE}/api/v2/health")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "healthy":
                    score += 1
                    print(f"   ✓ Health check: {data['status']}")

        except Exception as e:
            print(f"   ✗ Health check error: {e}")

        print(f"   📊 Performance Score: {score:.1f}/5.0")
        return score

    def test_integration_complete(self) -> float:
        """Test Intégration Complète (5 points)."""
        print("🔍 Test 8: Intégration Complète")

        score = 0

        # Test workflow complet : RAG → Neo4j → Impact → Anomaly
        try:
            # 1. RAG pour identifier un fichier sensible
            resp = requests.post(
                f"{API_BASE}/api/chat",
                json={"question": "Fichier principal sessions ?", "repo": "requests"}
            )

            if resp.status_code == 200:
                answer = resp.json().get("answer", "")
                if "sessions.py" in answer:
                    score += 1
                    print(f"   ✓ RAG identifies key file")

                    # 2. Neo4j pour explorer ce fichier
                    resp = requests.get(f"{API_BASE}/api/v2/repos/requests/functions?limit=50")
                    if resp.status_code == 200:
                        functions = resp.json().get("functions", [])
                        session_functions = [f for f in functions if "sessions.py" in f.get("file", "")]

                        if len(session_functions) > 0:
                            score += 1.5
                            print(f"   ✓ Neo4j explores file: {len(session_functions)} functions")

                            # 3. Impact analysis sur une fonction
                            resp = requests.post(
                                f"{API_BASE}/api/v2/impact/analyze",
                                json={
                                    "repo": "requests",
                                    "file": "src/requests/sessions.py",
                                    "changes": ["Session"]
                                }
                            )

                            if resp.status_code == 200:
                                impact = resp.json()
                                if impact.get("affected_functions"):
                                    score += 1.5
                                    print(f"   ✓ Impact analysis: {len(impact['affected_functions'])} affected")

                                    # 4. Anomaly detection
                                    resp = requests.post(
                                        f"{API_BASE}/api/v2/anomaly/scan",
                                        json={"repo": "requests", "types": ["complexity"]}
                                    )

                                    if resp.status_code == 200:
                                        anomalies = resp.json()
                                        if anomalies.get("total_found", 0) > 0:
                                            score += 1
                                            print(f"   ✓ Anomaly scan: {anomalies['total_found']} issues")

        except Exception as e:
            print(f"   ✗ Integration workflow error: {e}")

        print(f"   📊 Integration Score: {score:.1f}/5.0")
        return score

    def run_full_validation(self) -> Dict:
        """Exécute la validation complète."""
        print("🚀 VALIDATION FINALE HYPERION V2")
        print("=" * 50)

        # Exécuter tous les tests
        tests = [
            ("RAG Engine", self.test_rag_engine),
            ("Neo4j v2", self.test_neo4j_code_engine),
            ("Impact Analysis", self.test_impact_analysis_engine),
            ("Anomaly Detection", self.test_anomaly_detection_engine),
            ("Code Search", self.test_code_search_engine),
            ("Code Exploration", self.test_code_exploration_engine),
            ("Performance", self.test_performance),
            ("Integration", self.test_integration_complete)
        ]

        total_score = 0
        for test_name, test_func in tests:
            try:
                score = test_func()
                total_score += score
                self.results[test_name] = score
                print()
            except Exception as e:
                print(f"   ❌ {test_name} FAILED: {e}")
                self.results[test_name] = 0
                print()

        # Score final
        final_score = (total_score / self.max_score) * 10
        print("🏆 RÉSULTATS FINAUX")
        print("=" * 50)

        for test_name, score in self.results.items():
            print(f"{test_name:20} : {score:4.1f}/5.0")

        print("-" * 50)
        print(f"SCORE TOTAL         : {total_score:4.1f}/{self.max_score}")
        print(f"NOTE FINALE         : {final_score:4.1f}/10")

        if final_score >= 8.0:
            print("✅ OBJECTIF ATTEINT : Note ≥ 8/10 !")
        else:
            print(f"❌ OBJECTIF MANQUÉ : {8.0 - final_score:.1f} points manquants")

        return {
            "final_score": final_score,
            "total_points": total_score,
            "max_points": self.max_score,
            "tests": self.results,
            "success": final_score >= 8.0
        }

if __name__ == "__main__":
    validator = HyperionV2Validator()
    result = validator.run_full_validation()

    # Export JSON
    with open("/tmp/hyperion_v2_validation.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n📊 Résultats exportés: /tmp/hyperion_v2_validation.json")