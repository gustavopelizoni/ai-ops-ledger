from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from agent.models import SelectedContext


class TrivyScanner:
    def __init__(self, timeout: int = 60) -> None:
        self.timeout = timeout
        self.available = shutil.which("trivy") is not None

    def scan_context(self, context: SelectedContext) -> dict[str, Any]:
        """Scan selected repository files using Trivy if available, returning structured security & guardrail insights."""
        if not self.available:
            return {
                "available": False,
                "vulnerabilities": [],
                "secrets": [],
                "misconfigurations": [],
                "summary": "Trivy scanner not installed in environment (running standard static code analysis).",
            }

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                for f in context.files:
                    file_path = tmp_path / f.path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(f.content, encoding="utf-8", errors="ignore")

                result = subprocess.run(
                    [
                        "trivy",
                        "fs",
                        "--format",
                        "json",
                        "--security-checks",
                        "config,secret,vuln",
                        "--no-progress",
                        str(tmp_path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                if result.returncode != 0 and not result.stdout.strip():
                    return {
                        "available": True,
                        "error": result.stderr,
                        "vulnerabilities": [],
                        "secrets": [],
                        "misconfigurations": [],
                    }

                data = json.loads(result.stdout) if result.stdout.strip() else {}
                results = data.get("Results", [])

                vulns = []
                secrets = []
                misconfigs = []

                for res in results:
                    for v in res.get("Vulnerabilities", []):
                        vulns.append({
                            "id": v.get("VulnerabilityID"),
                            "pkg": v.get("PkgName"),
                            "severity": v.get("Severity"),
                            "title": v.get("Title") or v.get("VulnerabilityID"),
                            "target": res.get("Target"),
                        })
                    for s in res.get("Secrets", []):
                        secrets.append({
                            "rule_id": s.get("RuleID"),
                            "title": s.get("Title"),
                            "severity": s.get("Severity"),
                            "target": res.get("Target"),
                        })
                    for m in res.get("Misconfigurations", []):
                        misconfigs.append({
                            "id": m.get("ID"),
                            "title": m.get("Title"),
                            "severity": m.get("Severity"),
                            "status": m.get("Status"),
                            "target": res.get("Target"),
                        })

                return {
                    "available": True,
                    "vulnerabilities": vulns,
                    "secrets": secrets,
                    "misconfigurations": misconfigs,
                    "summary": f"Trivy scanned successfully: {len(vulns)} vulnerabilities, {len(secrets)} secrets, {len(misconfigs)} misconfigurations found.",
                }
        except Exception as error:
            return {
                "available": True,
                "error": str(error),
                "vulnerabilities": [],
                "secrets": [],
                "misconfigurations": [],
            }
