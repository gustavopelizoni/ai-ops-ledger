from agent.models import SelectedContext, SelectedFile
from agent.trivy import TrivyScanner


def test_trivy_scanner_unavailable_graceful():
    scanner = TrivyScanner()
    # Force available to False for testing graceful degradation
    scanner.available = False
    context = SelectedContext([SelectedFile("main.py", "print('hello')", 1, 10)])
    report = scanner.scan_context(context)
    assert report["available"] is False
    assert report["vulnerabilities"] == []
    assert report["secrets"] == []
    assert report["misconfigurations"] == []
    assert "not installed" in report["summary"]
