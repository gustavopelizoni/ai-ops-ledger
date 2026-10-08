#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from agent.agent import HermesAuditor
from agent.config import Settings, scope_with_environment
from agent.logging import configure_logging, event
from agent.sdd import load_sdd
from skills.github_collector import GitHubCollector, read_repository_list


ROOT = Path(__file__).resolve().parent


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Static, local-LLM auditor for public AI-agent repositories.")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--repo", help="One public GitHub repository: owner/repository")
    selection.add_argument("--repos", help="UTF-8 file with one owner/repository per line")
    selection.add_argument("--search", help="Explicit GitHub repository search query")
    parser.add_argument("--limit", type=int, default=5, help="Search result limit (1-100; search only)")
    parser.add_argument("--sort", choices=("stars", "forks", "help-wanted-issues", "updated"), default="stars", help="Deterministic GitHub search ordering")
    parser.add_argument("--model", help="Ollama model name; defaults to HERMES_MODEL or hermes3:8b")
    parser.add_argument("--output", default="site", help="Static report directory relative to project root")
    parser.add_argument("--dry-run", action="store_true", help="Validate/select targets and print manifest without model or collection")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = arguments()
    if not args.search and (args.limit != 5 or args.sort != "stars"):
        raise ValueError("--limit and --sort are available only with --search")
    logger = configure_logging(args.verbose)
    settings = Settings.from_environment(ROOT, args.model, args.output)
    sdd = load_sdd(ROOT)
    collector = GitHubCollector(settings.github_token, settings.request_timeout_seconds, scope_with_environment(sdd.scope))
    event(logger, "repository_selection_started")
    if args.repo:
        event(logger, "repository_validation_started", repository=args.repo)
        targets = [collector.validate(args.repo)]
    elif args.repos:
        event(logger, "repository_validation_started", source=args.repos)
        targets = collector.validate_all(read_repository_list(args.repos))
    else:
        targets = collector.search(args.search, args.limit, args.sort)
    if not targets:
        raise RuntimeError("Repository selection returned no public repositories")
    for target in targets:
        event(logger, "repository_selected", repository=target.full_name, selection_mode=target.selection_mode)
    manifest = {"selection_mode": "discovery" if args.search else "explicit", "query": args.search, "sort": args.sort if args.search else None, "targets": [target.to_dict() for target in targets]}
    manifest["selected_at"] = datetime.now(UTC).isoformat()
    manifest_dir = ROOT / "data" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / f"selection-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.dry_run:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0
    auditor = HermesAuditor(settings, sdd, logger)
    auditor.check_model()
    results = [auditor.audit(target) for target in targets]
    auditor.publish(results)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
