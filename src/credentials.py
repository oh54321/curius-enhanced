from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def _default_jwt_path() -> Path:
    return Path.home() / ".credentials" / "curius_jwt"


def read_curius_jwt() -> Optional[str]:
    env_jwt = os.getenv("CURIUS_JWT")
    if env_jwt:
        return env_jwt.strip()

    path = Path(os.getenv("CURIUS_JWT_PATH") or _default_jwt_path())
    if not path.exists():
        return None

    token = path.read_text(encoding="utf-8").strip()
    return token or None
