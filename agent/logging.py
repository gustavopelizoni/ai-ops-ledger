from __future__ import annotations

import json
import logging
from typing import Any


def configure_logging(verbose: bool = False) -> logging.Logger:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(message)s")
    return logging.getLogger("hermes_auditor")


def event(logger: logging.Logger, name: str, **fields: Any) -> None:
    logger.info(json.dumps({"event": name, **fields}, ensure_ascii=False, sort_keys=True))
