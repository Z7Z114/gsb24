from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import shutil

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/brainstorm", tags=["brainstorm"])

UPLOAD_DIR = os.getenv("BRAINSTORM_UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/discussions", response_model=schemas.Discussion)
def create_discussion(
    discussion: schemas.DiscussionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_discussion = models.Discussion(
        **discussion.dict(),
        owner_id=current_user.id
    )
    db.add(db_discussion)
    db.commit()
    db.refresh(db_discussion)
    return db_discussion


@router.get("/discussions", response_model=List[schemas.Discussion])
def get_discussions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.Discussion).filter(
        models.Discussion.owner_id == current_user.id
    ).all()


@router.get("/discussions/{discussion_id}", response_model=schemas.Discussion)
def get_discussion(
    discussion_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    discussion = db.query(models.Discussion).filter(
        models.Discussion.id == discussion_id,
        models.Discussion.owner_id == current_user.id
    ).first()
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
    return discussion


@router.post("/discussions/{discussion_id}/upload-audio", response_model=schemas.AudioFile)
async def upload_audio(
    discussion_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    discussion = db.query(models.Discussion).filter(
        models.Discussion.id == discussion_id,
        models.Discussion.owner_id == current_user.id
    ).first()
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")

    file_location = os.path.join(UPLOAD_DIR, f"{discussion_id}_{file.filename}")
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_audio = models.AudioFile(
        filename=file.filename,
        file_path=file_location,
        discussion_id=discussion_id
    )
    db.add(db_audio)
    db.commit()
    db.refresh(db_audio)
    return db_audio


@router.get("/discussions/{discussion_id}/world-settings", response_model=List[schemas.WorldSetting])
def get_world_settings(
    discussion_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    discussion = db.query(models.Discussion).filter(
        models.Discussion.id == discussion_id,
        models.Discussion.owner_id == current_user.id
    ).first()
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")

    return db.query(models.WorldSetting).filter(
        models.WorldSetting.discussion_id == discussion_id
    ).all()


@router.post("/world-settings", response_model=schemas.WorldSetting)
def create_world_setting(
    setting: schemas.WorldSettingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    discussion = db.query(models.Discussion).filter(
        models.Discussion.id == setting.discussion_id,
        models.Discussion.owner_id == current_user.id
    ).first()
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")

    db_setting = models.WorldSetting(**setting.dict())
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting


@router.get("/discussions/{discussion_id}/concept-arts", response_model=List[schemas.ConceptArt])
def get_concept_arts(
    discussion_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    discussion = db.query(models.Discussion).filter(
        models.Discussion.id == discussion_id,
        models.Discussion.owner_id == current_user.id
    ).first()
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")

    return db.query(models.ConceptArt).filter(
        models.ConceptArt.discussion_id == discussion_id
    ).all()


@router.post("/concept-arts", response_model=schemas.ConceptArt)
def create_concept_art(
    concept_art: schemas.ConceptArtCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    discussion = db.query(models.Discussion).filter(
        models.Discussion.id == concept_art.discussion_id,
        models.Discussion.owner_id == current_user.id
    ).first()
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")

    db_concept_art = models.ConceptArt(**concept_art.dict())
    db.add(db_concept_art)
    db.commit()
    db.refresh(db_concept_art)
    return db_concept_art
