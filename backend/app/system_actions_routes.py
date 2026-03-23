"""
Routes for strict, allowlisted, user-approved system actions.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import encryption_utils

from .database import get_db
from .routes import get_current_user_required
from . import crud, schemas, system_actions

router = APIRouter(prefix="/system", tags=["system"])


ALLOWED_ACTIONS = {
    "file_list",
    "file_read_text",
    "file_write_text",
    "file_delete",
    "reveal_in_explorer",
    "set_chat_history_retention_days",
}


def _validate_preview(action_type: str, params: Any) -> Dict[str, Any]:
    if action_type not in ALLOWED_ACTIONS:
        raise HTTPException(status_code=400, detail="Unsupported action_type")
    if not isinstance(params, dict):
        raise HTTPException(status_code=400, detail="params must be an object")

    # Basic parameter validation (avoid heavy schema libs).
    if action_type == "file_list":
        # params: { relative_dir?: string }
        if "relative_dir" in params and not isinstance(params["relative_dir"], str):
            raise HTTPException(status_code=400, detail="relative_dir must be a string")
        return params

    if action_type == "file_read_text":
        if "relative_path" not in params or not isinstance(params["relative_path"], str):
            raise HTTPException(status_code=400, detail="relative_path (string) is required")
        if "max_bytes" in params:
            try:
                int(params["max_bytes"])
            except Exception:
                raise HTTPException(status_code=400, detail="max_bytes must be an int")
        return params

    if action_type == "file_write_text":
        if "relative_path" not in params or not isinstance(params["relative_path"], str):
            raise HTTPException(status_code=400, detail="relative_path (string) is required")
        if "content" not in params or not isinstance(params["content"], str):
            raise HTTPException(status_code=400, detail="content (string) is required")
        if len(params["content"]) > 200_000:
            raise HTTPException(status_code=400, detail="content too large")
        return params

    if action_type == "file_delete":
        if "relative_path" not in params or not isinstance(params["relative_path"], str):
            raise HTTPException(status_code=400, detail="relative_path (string) is required")
        return params

    if action_type == "reveal_in_explorer":
        if "relative_path" not in params or not isinstance(params["relative_path"], str):
            raise HTTPException(status_code=400, detail="relative_path (string) is required")
        return params

    if action_type == "set_chat_history_retention_days":
        if "days" not in params:
            raise HTTPException(status_code=400, detail="days is required")
        try:
            int(params["days"])
        except Exception:
            raise HTTPException(status_code=400, detail="days must be an int")
        return params

    raise HTTPException(status_code=400, detail="Invalid action_type")


@router.get("/capabilities")
def get_system_capabilities(current_user=Depends(get_current_user_required)):
    # capabilities are static, kept minimal to avoid a heavy UI.
    return {
        "actions": [
            {"action_type": a, "description": system_actions.build_action_summary(a, {})}
            for a in sorted(ALLOWED_ACTIONS)
        ]
    }


@router.post("/actions/preview", response_model=schemas.SystemActionPreviewResponse)
def preview_system_action(
    req: schemas.SystemActionPreviewRequest,
    current_user=Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    params = _validate_preview(req.action_type, req.params)

    summary = system_actions.build_action_summary(req.action_type, params)
    approval = crud.create_system_action_approval(
        db,
        user_id=current_user.id,
        action_type=req.action_type,
        params=params,
        summary=summary,
        expires_minutes=5,
    )

    return schemas.SystemActionPreviewResponse(
        approval_id=approval.id,
        action_type=approval.action_type,
        summary=approval.summary,
        expires_at=approval.expires_at,
    )


@router.post("/actions/commit")
def commit_system_action(
    req: schemas.SystemActionCommitRequest,
    current_user=Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    approval = crud.get_system_action_approval_for_user(db, current_user.id, req.approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail=f"Approval already {approval.status}")
    if approval.expires_at and approval.expires_at < datetime.utcnow():
        approval.status = "expired"
        approval.decided_at = datetime.utcnow()
        db.commit()
        return {"ok": False, "status": "expired", "error": "Approval expired"}

    if not req.approve:
        approval = crud.decide_system_action(db, approval, approve=False, status_if_denied="denied")
        return {"ok": True, "status": "denied", "approval_id": approval.id}

    # Approve and execute.
    try:
        params_json = encryption_utils.decrypt_data(approval.params_encrypted.decode("utf-8"))
        params = json.loads(params_json) if params_json else {}
    except Exception:
        return {"ok": False, "status": "failed", "error": "Failed to load action parameters"}

    result = system_actions.execute_system_action(
        db=db,
        user_id=current_user.id,
        action_type=approval.action_type,
        params=params,
    )

    if result.get("ok"):
        approval = crud.mark_system_action_executed(
            db,
            approval,
            status="executed",
            result_preview=str(result),
            error_preview=None,
        )
        return {"ok": True, "status": "executed", "approval_id": approval.id, "result": result}

    approval = crud.mark_system_action_executed(
        db,
        approval,
        status="failed",
        result_preview=None,
        error_preview=result.get("error") or "Execution failed",
    )
    return {"ok": False, "status": "failed", "approval_id": approval.id, "error": result.get("error")}

