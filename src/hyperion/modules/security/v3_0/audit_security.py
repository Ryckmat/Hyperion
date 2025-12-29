"""
Hyperion v3.0 - Audit de Sécurité Enterprise
Audit complet des vulnérabilités et conformité sécurité
"""

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SecurityVulnerability:
    """Vulnérabilité de sécurité détectée"""

    vuln_id: str
    severity: str  # critical, high, medium, low
    category: str
    description: str
    file_path: str | None = None
    line_number: int | None = None
    evidence: str | None = None
    remediation: str | None = None
    cve_id: str | None = None
    confidence: float = 0.8


@dataclass
class ComplianceCheck:
    """Vérification de conformité"""

    check_id: str
    standard: str  # GDPR, ISO27001, SOX, etc.
    description: str
    status: str  # compliant, non_compliant, partial, unknown
    evidence: list[str]
    recommendations: list[str]


@dataclass
class SecurityAuditReport:
    """Rapport d'audit de sécurité complet"""

    audit_id: str
    timestamp: float
    scope: str
    vulnerabilities: list[SecurityVulnerability]
    compliance_checks: list[ComplianceCheck]
    risk_score: float
    executive_summary: str
    total_issues: int
    critical_issues: int
    high_issues: int


class SecurityAuditor:
    """Auditeur de sécurité enterprise"""

    def __init__(self):
        self.audit_history: list[SecurityAuditReport] = []
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.compliance_frameworks = self._load_compliance_frameworks()

    def _load_vulnerability_patterns(self) -> dict[str, Any]:
        """Charge les patterns de vulnérabilités"""
        return {
            "sql_injection": {
                "patterns": [
                    r"SELECT\s+.*\s+FROM\s+.*\s+WHERE\s+.*=.*\+",
                    r"UNION\s+SELECT",
                    r"OR\s+1\s*=\s*1",
                    r"\';\s*DROP\s+TABLE",
                ],
                "severity": "critical",
                "remediation": "Utiliser des requêtes préparées et validation des entrées",
            },
            "xss": {
                "patterns": [
                    r"<script[^>]*>.*?</script>",
                    r"javascript:",
                    r"onload\s*=",
                    r"innerHTML\s*=.*\+",
                ],
                "severity": "high",
                "remediation": "Encoder les sorties et valider les entrées utilisateur",
            },
            "hardcoded_secrets": {
                "patterns": [
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'api_key\s*=\s*["\'][^"\']+["\']',
                    r'secret\s*=\s*["\'][^"\']+["\']',
                    r'token\s*=\s*["\'][^"\']+["\']',
                ],
                "severity": "critical",
                "remediation": "Utiliser des variables d'environnement ou un gestionnaire de secrets",
            },
            "path_traversal": {
                "patterns": [r"\.\./\.\.", r"\.\.\\\.\.\\", r"%2e%2e%2f", r"%252e%252e%252f"],
                "severity": "high",
                "remediation": "Valider et sanitizer tous les chemins de fichiers",
            },
            "weak_crypto": {
                "patterns": [r"md5\(", r"sha1\(", r"DES\(", r"RC4\("],
                "severity": "medium",
                "remediation": "Utiliser des algorithmes cryptographiques forts (SHA-256, AES-256)",
            },
        }

    def _load_compliance_frameworks(self) -> dict[str, Any]:
        """Charge les frameworks de conformité"""
        return {
            "GDPR": {
                "checks": [
                    {
                        "id": "GDPR-001",
                        "description": "Consentement explicite pour traitement des données",
                        "requirements": ["consent_mechanism", "data_processing_notice"],
                    },
                    {
                        "id": "GDPR-002",
                        "description": "Droit à l'oubli et portabilité des données",
                        "requirements": ["data_deletion", "data_export"],
                    },
                    {
                        "id": "GDPR-003",
                        "description": "Chiffrement des données personnelles",
                        "requirements": ["encryption_at_rest", "encryption_in_transit"],
                    },
                ]
            },
            "ISO27001": {
                "checks": [
                    {
                        "id": "ISO-001",
                        "description": "Politique de sécurité de l'information",
                        "requirements": ["security_policy", "risk_management"],
                    },
                    {
                        "id": "ISO-002",
                        "description": "Contrôle d'accès et gestion des identités",
                        "requirements": [
                            "access_control",
                            "user_authentication",
                            "privilege_management",
                        ],
                    },
                    {
                        "id": "ISO-003",
                        "description": "Surveillance et logging de sécurité",
                        "requirements": ["security_monitoring", "audit_logs", "incident_response"],
                    },
                ]
            },
            "SOX": {
                "checks": [
                    {
                        "id": "SOX-001",
                        "description": "Contrôles internes sur les rapports financiers",
                        "requirements": ["financial_data_integrity", "access_controls_financial"],
                    },
                    {
                        "id": "SOX-002",
                        "description": "Traçabilité et auditabilité des transactions",
                        "requirements": ["transaction_logging", "audit_trail", "data_retention"],
                    },
                ]
            },
        }

    def scan_vulnerabilities(self, target_path: str) -> list[SecurityVulnerability]:
        """Scan des vulnérabilités dans le code"""
        vulnerabilities = []
        target = Path(target_path)

        try:
            if target.is_file():
                files_to_scan = [target]
            elif target.is_dir():
                files_to_scan = []
                for ext in ["*.py", "*.js", "*.ts", "*.java", "*.php", "*.rb"]:
                    files_to_scan.extend(target.rglob(ext))
            else:
                logger.warning(f"Chemin non valide pour scan: {target_path}")
                return vulnerabilities

            for file_path in files_to_scan:
                try:
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        file_vulns = self._scan_file_content(str(file_path), content)
                        vulnerabilities.extend(file_vulns)
                except Exception as e:
                    logger.error(f"Erreur lecture fichier {file_path}: {e}")

        except Exception as e:
            logger.error(f"Erreur scan vulnérabilités: {e}")

        return vulnerabilities

    def _scan_file_content(self, file_path: str, content: str) -> list[SecurityVulnerability]:
        """Scan d'un fichier pour les vulnérabilités"""
        vulnerabilities = []
        lines = content.split("\n")

        for vuln_type, vuln_config in self.vulnerability_patterns.items():
            for pattern in vuln_config["patterns"]:
                import re

                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        vuln_id = hashlib.md5(
                            f"{file_path}:{line_num}:{pattern}".encode()
                        ).hexdigest()[:8]

                        vulnerability = SecurityVulnerability(
                            vuln_id=vuln_id,
                            severity=vuln_config["severity"],
                            category=vuln_type,
                            description=f"Vulnérabilité {vuln_type} détectée",
                            file_path=file_path,
                            line_number=line_num,
                            evidence=line.strip()[:200],
                            remediation=vuln_config["remediation"],
                            confidence=0.8,
                        )
                        vulnerabilities.append(vulnerability)

        return vulnerabilities

    def check_compliance(
        self, framework: str, system_config: dict[str, Any]
    ) -> list[ComplianceCheck]:
        """Vérification de conformité pour un framework donné"""
        compliance_checks = []

        if framework not in self.compliance_frameworks:
            logger.warning(f"Framework de conformité non supporté: {framework}")
            return compliance_checks

        framework_config = self.compliance_frameworks[framework]

        for check_config in framework_config["checks"]:
            status = "unknown"
            evidence = []
            recommendations = []

            # Vérification basique selon les requirements
            requirements_met = 0
            total_requirements = len(check_config["requirements"])

            for requirement in check_config["requirements"]:
                if requirement in system_config and system_config[requirement]:
                    requirements_met += 1
                    evidence.append(f"✅ {requirement} configuré")
                else:
                    recommendations.append(f"Configurer {requirement}")
                    evidence.append(f"❌ {requirement} manquant")

            # Déterminer le statut
            if requirements_met == total_requirements:
                status = "compliant"
            elif requirements_met > total_requirements / 2:
                status = "partial"
            else:
                status = "non_compliant"

            compliance_check = ComplianceCheck(
                check_id=check_config["id"],
                standard=framework,
                description=check_config["description"],
                status=status,
                evidence=evidence,
                recommendations=recommendations,
            )
            compliance_checks.append(compliance_check)

        return compliance_checks

    def generate_risk_score(
        self, vulnerabilities: list[SecurityVulnerability], compliance_checks: list[ComplianceCheck]
    ) -> float:
        """Calcule un score de risque global"""
        # Score basé sur les vulnérabilités
        vuln_score = 0.0
        severity_weights = {"critical": 10, "high": 7, "medium": 4, "low": 1}

        for vuln in vulnerabilities:
            weight = severity_weights.get(vuln.severity, 1)
            vuln_score += weight * vuln.confidence

        # Score basé sur la conformité
        compliance_score = 0.0
        total_checks = len(compliance_checks)
        if total_checks > 0:
            non_compliant = len([c for c in compliance_checks if c.status == "non_compliant"])
            partial = len([c for c in compliance_checks if c.status == "partial"])
            compliance_score = (non_compliant * 5 + partial * 2) / total_checks

        # Score final (0-100, où 0 = très sûr, 100 = très risqué)
        final_score = min(100, (vuln_score * 2 + compliance_score * 20) / 3)
        return round(final_score, 2)

    def perform_full_audit(
        self,
        target_path: str,
        compliance_frameworks: list[str] = None,
        system_config: dict[str, Any] = None,
    ) -> SecurityAuditReport:
        """Effectue un audit de sécurité complet"""
        audit_id = hashlib.sha256(f"{target_path}:{time.time()}".encode()).hexdigest()[:12]
        timestamp = time.time()

        # Scan des vulnérabilités
        vulnerabilities = self.scan_vulnerabilities(target_path)

        # Vérifications de conformité
        compliance_checks = []
        if compliance_frameworks and system_config:
            for framework in compliance_frameworks:
                checks = self.check_compliance(framework, system_config)
                compliance_checks.extend(checks)

        # Calcul du score de risque
        risk_score = self.generate_risk_score(vulnerabilities, compliance_checks)

        # Statistiques
        total_issues = len(vulnerabilities)
        critical_issues = len([v for v in vulnerabilities if v.severity == "critical"])
        high_issues = len([v for v in vulnerabilities if v.severity == "high"])

        # Résumé exécutif
        executive_summary = self._generate_executive_summary(
            vulnerabilities, compliance_checks, risk_score
        )

        report = SecurityAuditReport(
            audit_id=audit_id,
            timestamp=timestamp,
            scope=target_path,
            vulnerabilities=vulnerabilities,
            compliance_checks=compliance_checks,
            risk_score=risk_score,
            executive_summary=executive_summary,
            total_issues=total_issues,
            critical_issues=critical_issues,
            high_issues=high_issues,
        )

        self.audit_history.append(report)
        logger.info(f"Audit de sécurité terminé: {audit_id}, score de risque: {risk_score}")

        return report

    def _generate_executive_summary(
        self,
        vulnerabilities: list[SecurityVulnerability],
        compliance_checks: list[ComplianceCheck],
        risk_score: float,
    ) -> str:
        """Génère un résumé exécutif de l'audit"""
        summary_parts = []

        # Évaluation du risque
        if risk_score >= 70:
            risk_level = "CRITIQUE"
            summary_parts.append(f"🚨 RISQUE {risk_level}: Score {risk_score}/100")
        elif risk_score >= 40:
            risk_level = "ÉLEVÉ"
            summary_parts.append(f"⚠️ RISQUE {risk_level}: Score {risk_score}/100")
        elif risk_score >= 20:
            risk_level = "MODÉRÉ"
            summary_parts.append(f"🟡 RISQUE {risk_level}: Score {risk_score}/100")
        else:
            risk_level = "FAIBLE"
            summary_parts.append(f"✅ RISQUE {risk_level}: Score {risk_score}/100")

        # Vulnérabilités
        critical_count = len([v for v in vulnerabilities if v.severity == "critical"])
        high_count = len([v for v in vulnerabilities if v.severity == "high"])

        if critical_count > 0:
            summary_parts.append(f"🔴 {critical_count} vulnérabilités critiques détectées")
        if high_count > 0:
            summary_parts.append(f"🟠 {high_count} vulnérabilités haute priorité")

        # Conformité
        non_compliant = len([c for c in compliance_checks if c.status == "non_compliant"])
        if non_compliant > 0:
            summary_parts.append(f"📋 {non_compliant} non-conformités détectées")

        # Recommandations prioritaires
        if risk_score >= 40:
            summary_parts.append("🎯 Action immédiate requise pour réduire le risque")

        return " | ".join(summary_parts)

    def export_report(
        self, report: SecurityAuditReport, output_path: str, format: str = "json"
    ) -> bool:
        """Exporte un rapport d'audit"""
        try:
            output_file = Path(output_path)

            if format == "json":
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(asdict(report), f, indent=2, ensure_ascii=False)

            elif format == "markdown":
                markdown_content = self._generate_markdown_report(report)
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

            logger.info(f"Rapport exporté: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Erreur export rapport: {e}")
            return False

    def _generate_markdown_report(self, report: SecurityAuditReport) -> str:
        """Génère un rapport en markdown"""
        md_lines = [
            "# Rapport d'Audit de Sécurité",
            f"**ID Audit:** {report.audit_id}",
            f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.timestamp))}",
            f"**Scope:** {report.scope}",
            "",
            "## Résumé Exécutif",
            report.executive_summary,
            "",
            f"## Score de Risque: {report.risk_score}/100",
            "",
            "## Statistiques",
            f"- Total des problèmes: {report.total_issues}",
            f"- Issues critiques: {report.critical_issues}",
            f"- Issues haute priorité: {report.high_issues}",
            "",
        ]

        if report.vulnerabilities:
            md_lines.extend(["## Vulnérabilités Détectées", ""])

            for vuln in report.vulnerabilities:
                md_lines.extend(
                    [
                        f"### {vuln.vuln_id} - {vuln.category.upper()}",
                        f"**Sévérité:** {vuln.severity.upper()}",
                        f"**Description:** {vuln.description}",
                        f"**Fichier:** {vuln.file_path}:{vuln.line_number}",
                        f"**Remédiation:** {vuln.remediation}",
                        "",
                    ]
                )

        if report.compliance_checks:
            md_lines.extend(["## Vérifications de Conformité", ""])

            for check in report.compliance_checks:
                status_icon = "✅" if check.status == "compliant" else "❌"
                md_lines.extend(
                    [
                        f"### {status_icon} {check.check_id} ({check.standard})",
                        f"**Status:** {check.status}",
                        f"**Description:** {check.description}",
                        "**Recommandations:**",
                        *[f"- {rec}" for rec in check.recommendations],
                        "",
                    ]
                )

        return "\n".join(md_lines)

    def get_audit_history(self) -> list[SecurityAuditReport]:
        """Retourne l'historique des audits"""
        return self.audit_history.copy()

    def compare_audits(self, audit1_id: str, audit2_id: str) -> dict[str, Any]:
        """Compare deux audits"""
        audit1 = next((a for a in self.audit_history if a.audit_id == audit1_id), None)
        audit2 = next((a for a in self.audit_history if a.audit_id == audit2_id), None)

        if not audit1 or not audit2:
            raise ValueError("Audit non trouvé")

        comparison = {
            "risk_score_change": audit2.risk_score - audit1.risk_score,
            "vulnerabilities_change": audit2.total_issues - audit1.total_issues,
            "critical_issues_change": audit2.critical_issues - audit1.critical_issues,
            "new_vulnerabilities": len(
                [
                    v
                    for v in audit2.vulnerabilities
                    if v.vuln_id not in [v1.vuln_id for v1 in audit1.vulnerabilities]
                ]
            ),
            "resolved_vulnerabilities": len(
                [
                    v
                    for v in audit1.vulnerabilities
                    if v.vuln_id not in [v2.vuln_id for v2 in audit2.vulnerabilities]
                ]
            ),
        }

        return comparison


# Instances globales
default_security_auditor = SecurityAuditor()


# Fonctions utilitaires
def quick_scan(target_path: str) -> SecurityAuditReport:
    """Scan rapide de sécurité"""
    return default_security_auditor.perform_full_audit(target_path)


def compliance_check(framework: str, config: dict[str, Any]) -> list[ComplianceCheck]:
    """Vérification rapide de conformité"""
    return default_security_auditor.check_compliance(framework, config)
