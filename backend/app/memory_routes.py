"""
Adaptive memory opt-in routes.
User can control which categories are allowed to evolve over time.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db
from .routes import get_current_user_required
from . import crud, schemas

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/preferences", response_model=schemas.MemoryPreferences)
def get_memory_preferences(
    current_user=Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    settings_obj = crud.get_user_settings(db, current_user.id)
    return schemas.MemoryPreferences(
        allow_routine_tracking=settings_obj.allow_routine_tracking,
        allow_preference_learning=settings_obj.allow_preference_learning,
        allow_mental_health_inference=settings_obj.allow_mental_health_inference,
        enable_long_term_memory=bool(getattr(settings_obj, "enable_long_term_memory", True)),
    )


@router.put("/preferences", response_model=schemas.MemoryPreferences)
def update_memory_preferences(
    prefs: schemas.MemoryPreferencesUpdate,
    current_user=Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    settings_obj = crud.update_user_memory_preferences(db, current_user.id, prefs)
    return schemas.MemoryPreferences(
        allow_routine_tracking=settings_obj.allow_routine_tracking,
        allow_preference_learning=settings_obj.allow_preference_learning,
        allow_mental_health_inference=settings_obj.allow_mental_health_inference,
        enable_long_term_memory=bool(getattr(settings_obj, "enable_long_term_memory", True)),
    )

