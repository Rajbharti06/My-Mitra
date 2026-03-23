"""
Allowlisted, permissioned system actions.

Security goals:
- Strict allowlist of action types.
- All filesystem access constrained to a sandbox root.
- User must explicitly confirm each action via approval flow.
"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from .config import settings
from . import crud


def _get_sandbox_root() -> Path:
    root = Path(settings.SANDBOX_ROOT).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def _resolve_within_sandbox(relative_path: str) -> Path:
    """
    Resolve a relative path inside the sandbox root.
    Rejects attempts to escape the sandbox via path traversal.
    """
    if relative_path is None:
        raise ValueError("relative_path is required")
    rel = str(relative_path).replace("\\", "/")
    rel = rel.lstrip("/")  # disallow absolute paths
    rel_path = Path(rel)
    if any(part in ("..", "~") for part in rel_path.parts):
        raise ValueError("Invalid path")

    sandbox_root = _get_sandbox_root()
    resolved = (sandbox_root / rel_path).resolve()
    if not str(resolved).startswith(str(sandbox_root)):
        raise ValueError("Path escapes sandbox")
    return resolved


def _windows_only() -> bool:
    return sys.platform.startswith("win")


def build_action_summary(action_type: str, params: Dict[str, Any]) -> str:
    if action_type == "file_list":
        return f"List files in `{params.get('relative_dir', '')}`"
    if action_type == "file_read_text":
        return f"Read `{params.get('relative_path')}` (text, truncated)"
    if action_type == "file_write_text":
        return f"Write text to `{params.get('relative_path')}`"
    if action_type == "file_delete":
        return f"Delete `{params.get('relative_path')}`"
    if action_type == "reveal_in_explorer":
        return f"Reveal `{params.get('relative_path')}` in file explorer"
    if action_type == "set_chat_history_retention_days":
        return f"Set chat history retention to {params.get('days')} days"
    return f"Perform action `{action_type}`"


def execute_system_action(
    db,
    user_id: int,
    action_type: str,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute a validated action.
    This function assumes the route has already validated action_type and params schema,
    and that the user has explicitly confirmed via approval.
    """
    try:
        if action_type == "file_list":
            relative_dir = str(params.get("relative_dir", "")).strip()
            rel = relative_dir.replace("\\", "/").lstrip("/")
            target_dir = _resolve_within_sandbox(rel)
            if not target_dir.exists() or not target_dir.is_dir():
                raise ValueError("Directory does not exist")
            entries = sorted([p.name for p in target_dir.iterdir()])[:500]
            return {"ok": True, "entries": entries}

        if action_type == "file_read_text":
            relative_path = str(params.get("relative_path", "")).strip()
            max_bytes = int(params.get("max_bytes", 50_000))
            max_bytes = max(1_000, min(max_bytes, 200_000))
            target = _resolve_within_sandbox(relative_path)
            if not target.exists() or not target.is_file():
                raise ValueError("File does not exist")
            if target.is_symlink():
                raise ValueError("Refusing symlink")
            data = target.read_bytes()[:max_bytes]
            text = data.decode("utf-8", errors="replace")
            return {"ok": True, "content": text}

        if action_type == "file_write_text":
            relative_path = str(params.get("relative_path", "")).strip()
            content = params.get("content", "")
            if not isinstance(content, str):
                raise ValueError("content must be a string")
            max_len = 200_000
            if len(content) > max_len:
                raise ValueError("content too large")
            target = _resolve_within_sandbox(relative_path)
            if target.exists() and target.is_symlink():
                raise ValueError("Refusing symlink overwrite")
            if not target.parent.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
            # Text-only writes keep the scope safe for “authorized file management”.
            target.write_text(content, encoding="utf-8")
            return {"ok": True, "written_bytes": len(content.encode("utf-8"))}

        if action_type == "file_delete":
            relative_path = str(params.get("relative_path", "")).strip()
            target = _resolve_within_sandbox(relative_path)
            if not target.exists():
                return {"ok": True, "deleted": False}
            if target.is_symlink():
                raise ValueError("Refusing symlink delete")
            if target.is_dir():
                raise ValueError("Refusing directory delete (use empty directories only)")
            target.unlink()
            return {"ok": True, "deleted": True}

        if action_type == "reveal_in_explorer":
            if not _windows_only():
                raise ValueError("Reveal is only supported on Windows in this build")
            relative_path = str(params.get("relative_path", "")).strip()
            target = _resolve_within_sandbox(relative_path)
            if not target.exists():
                raise ValueError("Target does not exist")
            # os.startfile opens Explorer/target without giving the model arbitrary shell access.
            os.startfile(str(target))  # noqa: S606
            return {"ok": True, "revealed": True}

        if action_type == "set_chat_history_retention_days":
            days = int(params.get("days"))
            days = max(1, min(days, 365))
            settings_obj = crud.get_user_settings(db, user_id)
            settings_obj.chat_history_retention_days = days
            db.commit()
            return {"ok": True, "chat_history_retention_days": days}

        return {"ok": False, "error": "Unsupported action"}

    except Exception as e:
        # Never leak stack traces via API.
        return {"ok": False, "error": str(e)}

