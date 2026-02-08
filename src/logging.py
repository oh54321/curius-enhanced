from __future__ import annotations

import logging
from typing import Optional

try:
    from rich.logging import RichHandler
except Exception:
    RichHandler = None  # type: ignore

_configured = False


def _configure_logging() -> None:
    global _configured
    if _configured:
        return

    handlers = []
    if RichHandler is not None:
        handlers = [RichHandler(rich_tracebacks=True)]

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=handlers or None,
    )
    _configured = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    _configure_logging()
    return logging.getLogger(name or "app")
