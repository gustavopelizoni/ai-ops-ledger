#!/usr/bin/env python3
"""Check a local Ollama installation and optionally pull the configured model."""
from __future__ import annotations

import argparse
import os
import sys

import requests


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=os.getenv("HERMES_MODEL", "hermes3:8b"))
    parser.add_argument("--pull", action="store_true", help="Pull the model when it is absent")
    args = parser.parse_args()
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    try:
        response = requests.get(f"{host}/api/tags", timeout=10)
        response.raise_for_status()
        models = response.json().get("models", [])
    except (requests.RequestException, ValueError) as error:
        print(f"OLLAMA: ERROR ({error})")
        return 1
    print("OLLAMA: OK")
    names = {model.get("name") for model in models}
    if args.model not in names:
        if not args.pull:
            print(f"MODEL: MISSING ({args.model})\nInstall with: ollama pull {args.model}")
            return 1
        try:
            response = requests.post(f"{host}/api/pull", json={"name": args.model, "stream": False}, timeout=3600)
            response.raise_for_status()
        except requests.RequestException as error:
            print(f"MODEL: ERROR ({error})")
            return 1
    print("MODEL: OK")
    try:
        response = requests.post(f"{host}/api/generate", json={"model": args.model, "prompt": "Reply with OK", "stream": False}, timeout=60)
        response.raise_for_status()
        print("INFERENCE: OK")
        return 0
    except requests.RequestException as error:
        print(f"INFERENCE: ERROR ({error})")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
