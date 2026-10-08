from pathlib import Path

from skills.report_generator import ReportGenerator


def test_report_escapes_untrusted_html(tmp_path: Path):
    result = {"repository": {"full_name": "owner/repo", "url": "https://github.com/owner/repo", "selection_mode": "explicit"}, "audit": {"score": 90, "grade": "A"}, "summary": "<script>alert(1)</script>", "findings": [], "categories": {}, "provenance": {"commit_sha": "abc"}}
    report = ReportGenerator(tmp_path).write_report(result)
    assert "&lt;script&gt;" in report.read_text(encoding="utf-8")
