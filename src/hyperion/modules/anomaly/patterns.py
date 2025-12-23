"""
Détection de patterns dangereux (sécurité, performance).

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

import re
from pathlib import Path
from typing import Any


class DangerousPatterns:
    """
    Détecte les patterns de code dangereux.

    Sécurité: SQL injection, XSS, secrets hardcodés
    Performance: N+1 queries, boucles inefficaces
    """

    def __init__(self):
        """Initialise les patterns de détection."""
        self.security_patterns = {
            "sql_injection": [
                r"execute\([\"'].*\+.*[\"']\)",  # SQL concatenation
                r"f[\"']SELECT.*{.*}",  # f-string SQL
            ],
            "hardcoded_secret": [
                r"password\s*=\s*[\"'][^\"']+[\"']",
                r"api_key\s*=\s*[\"'][^\"']+[\"']",
                r"secret\s*=\s*[\"'][^\"']+[\"']",
            ],
            "command_injection": [
                r"os\.system\(.*\+",
                r"subprocess\.(call|run|Popen)\(.*\+",
            ],
        }

        self.performance_patterns = {
            "n_plus_one": [
                r"for\s+.*in.*:\s+.*\.get\(",  # Loop + query
            ],
            "inefficient_loop": [
                r"for\s+.*in.*:\s+.*\.append\(.*\)",  # List comprehension better
            ],
        }

    def scan_file(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Scanne un fichier pour patterns dangereux.

        Args:
            file_path: Fichier à scanner

        Returns:
            Liste de patterns détectés
        """
        # TODO: Implémenter scan complet avec AST
        with open(file_path) as f:
            content = f.read()

        findings = []

        # Security patterns
        for category, patterns in self.security_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[: match.start()].count("\n") + 1
                    findings.append(
                        {
                            "type": "security",
                            "category": category,
                            "severity": "high",
                            "line": line_num,
                            "code": match.group(0),
                            "message": f"Pattern dangereux détecté: {category}",
                        }
                    )

        # Performance patterns
        for category, patterns in self.performance_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[: match.start()].count("\n") + 1
                    findings.append(
                        {
                            "type": "performance",
                            "category": category,
                            "severity": "medium",
                            "line": line_num,
                            "code": match.group(0),
                            "message": f"Pattern inefficace: {category}",
                        }
                    )

        return findings

    def check_rgpd_compliance(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Vérifie la conformité RGPD.

        Args:
            file_path: Fichier à vérifier

        Returns:
            Liste de violations potentielles
        """
        # TODO: Implémenter checks RGPD avancés
        with open(file_path) as f:
            content = f.read()

        violations = []

        # Patterns PII non chiffrés
        pii_patterns = [
            (r"email\s*=\s*[\"'][^\"']+[\"']", "email"),
            (r"phone\s*=\s*[\"'][^\"']+[\"']", "phone"),
            (r"ssn\s*=\s*[\"'][^\"']+[\"']", "ssn"),
        ]

        for pattern, data_type in pii_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(
                    {
                        "type": "rgpd",
                        "data_type": data_type,
                        "severity": "high",
                        "message": f"Données PII ({data_type}) potentiellement non chiffrées",
                    }
                )

        return violations

    def generate_report(self, file_path: Path) -> dict[str, Any]:
        """
        Génère un rapport complet.

        Args:
            file_path: Fichier analysé

        Returns:
            Rapport structuré
        """
        security_findings = self.scan_file(file_path)
        rgpd_violations = self.check_rgpd_compliance(file_path)

        return {
            "file": str(file_path),
            "security_findings": [f for f in security_findings if f["type"] == "security"],
            "performance_issues": [f for f in security_findings if f["type"] == "performance"],
            "rgpd_violations": rgpd_violations,
            "total_issues": len(security_findings) + len(rgpd_violations),
            "risk_score": self._calculate_risk_score(security_findings, rgpd_violations),
        }

    def _calculate_risk_score(
        self, security_findings: list[dict[str, Any]], rgpd_violations: list[dict[str, Any]]
    ) -> float:
        """Calcule un score de risque global."""
        severity_weights = {"low": 0.2, "medium": 0.5, "high": 0.9, "critical": 1.0}

        security_score = sum(severity_weights.get(f.get("severity", "low"), 0.5) for f in security_findings)

        rgpd_score = sum(severity_weights.get(v.get("severity", "low"), 0.5) for v in rgpd_violations)

        total = security_score + rgpd_score
        return min(total / 10, 1.0)  # Normalisé sur 10 issues max
