from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import os

from .. import models, schemas, auth
from ..database import get_db
from ..services.openai_service import OpenAIService

router = APIRouter(prefix="/api/summary", tags=["summary"])

openai_service = OpenAIService()
OUTPUT_DIR = os.getenv("BRAINSTORM_OUTPUT_DIR", "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@router.post("/generate", response_model=schemas.Summary)
async def generate_summary(
    request: schemas.SummaryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    discussion = db.query(models.Discussion).filter(
        models.Discussion.id == request.discussion_id,
        models.Discussion.owner_id == current_user.id
    ).first()

    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")

    transcripts = db.query(models.Transcript).filter(
        models.Transcript.discussion_id == request.discussion_id
    ).all()

    if not transcripts:
        raise HTTPException(status_code=400, detail="No transcripts found for this discussion")

    full_text = " ".join([t.full_text for t in transcripts])

    background_tasks.add_task(
        generate_summary_task,
        request.discussion_id,
        discussion.title,
        full_text,
        request.custom_prompt,
        db
    )

    return schemas.Summary(
        id=0,
        discussion_id=request.discussion_id,
        content="Generating...",
        markdown_content="Generating...",
        tech_principles="",
        social_structure="",
        timeline=[],
        created_at=datetime.now()
    )


def generate_summary_task(
    discussion_id: int,
    discussion_title: str,
    full_text: str,
    custom_prompt: str,
    db: Session
):
    try:
        result = openai_service.generate_summary(
            transcript_text=full_text,
            discussion_title=discussion_title,
            custom_prompt=custom_prompt
        )

        summary = models.Summary(
            discussion_id=discussion_id,
            content=result["content"],
            markdown_content=result["markdown_content"],
            tech_principles=result["tech_principles"],
            social_structure=result["social_structure"],
            timeline=result["timeline"]
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)

        output_file = os.path.join(
            OUTPUT_DIR,
            f"summary_{discussion_id}_{summary.id}.md"
        )
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result["markdown_content"])

    except Exception as e:
        db.rollback()
        print(f"Error generating summary: {e}")


@router.post("/extract-settings/{discussion_id}")
async def extract_world_settings(
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

    transcript_segments = db.query(models.TranscriptSegment).join(
        models.Transcript
    ).filter(
        models.Transcript.discussion_id == discussion_id
    ).all()

    if not transcript_segments:
        raise HTTPException(status_code=400, detail="No transcript segments found")

    segments_data = [
        {
            "text": seg.text,
            "speaker": seg.speaker_label
        }
        for seg in transcript_segments
    ]

    settings = openai_service.extract_world_settings(segments_data)

    created_settings = []
    for setting in settings:
        db_setting = models.WorldSetting(
            discussion_id=discussion_id,
            category=setting.get("category", "其他"),
            key=setting.get("key", ""),
            value=setting.get("value", ""),
            description=setting.get("description", ""),
            owner_name=setting.get("owner_name", "")
        )
        db.add(db_setting)
        db.flush()
        created_settings.append(db_setting)

    db.commit()

    return {
        "extracted_count": len(created_settings),
        "settings": created_settings
    }


@router.get("/{discussion_id}", response_model=List[schemas.Summary])
def get_summaries(
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

    summaries = db.query(models.Summary).filter(
        models.Summary.discussion_id == discussion_id
    ).order_by(models.Summary.created_at.desc()).all()

    return summaries


@router.get("/download/{summary_id}")
def download_summary(
    summary_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    summary = db.query(models.Summary).filter(
        models.Summary.id == summary_id
    ).first()

    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    discussion = db.query(models.Discussion).filter(
        models.Discussion.id == summary.discussion_id,
        models.Discussion.owner_id == current_user.id
    ).first()

    if not discussion:
        raise HTTPException(status_code=403, detail="Permission denied")

    from fastapi.responses import FileResponse
    import tempfile

    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".md",
        delete=False,
        encoding="utf-8"
    )
    temp_file.write(summary.markdown_content)
    temp_file.close()

    return FileResponse(
        temp_file.name,
        media_type="text/markdown",
        filename=f"summary_{summary.discussion_id}_{summary_id}.md"
    )
