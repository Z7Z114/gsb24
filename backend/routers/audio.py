from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime

from .. import models, schemas, auth
from ..database import get_db
from ..services.whisper_service import WhisperService
from ..services.pyannote_service import PyannoteService

router = APIRouter(prefix="/api/audio", tags=["audio"])

whisper_service = WhisperService(model_size="base")
pyannote_service = PyannoteService()


@router.post("/process", response_model=schemas.Transcript)
async def process_audio(
    request: schemas.AudioProcessingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    audio_file = db.query(models.AudioFile).filter(
        models.AudioFile.id == request.audio_file_id,
        models.AudioFile.discussion_id == request.discussion_id
    ).first()

    if not audio_file:
        raise HTTPException(status_code=404, detail="Audio file not found")

    discussion = db.query(models.Discussion).filter(
        models.Discussion.id == request.discussion_id,
        models.Discussion.owner_id == current_user.id
    ).first()

    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")

    background_tasks.add_task(
        process_audio_task,
        request.audio_file_id,
        request.discussion_id,
        audio_file.file_path,
        db
    )

    return schemas.Transcript(
        id=0,
        audio_file_id=request.audio_file_id,
        discussion_id=request.discussion_id,
        full_text="Processing...",
        created_at=datetime.now()
    )


def process_audio_task(
    audio_file_id: int,
    discussion_id: int,
    file_path: str,
    db: Session
):
    try:
        whisper_result = whisper_service.transcribe(file_path)
        diarization_segments = pyannote_service.diarize(file_path)

        merged_segments = pyannote_service.merge_with_transcript(
            diarization_segments,
            whisper_result["segments"]
        )

        full_text = " ".join([seg["text"] for seg in merged_segments])

        transcript = models.Transcript(
            audio_file_id=audio_file_id,
            discussion_id=discussion_id,
            full_text=full_text
        )
        db.add(transcript)
        db.flush()

        for seg in merged_segments:
            segment = models.TranscriptSegment(
                transcript_id=transcript.id,
                speaker_label=seg["speaker"],
                start_time=int(seg["start"] * 1000),
                end_time=int(seg["end"] * 1000),
                text=seg["text"]
            )
            db.add(segment)

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Error processing audio: {e}")


@router.get("/transcripts/{discussion_id}", response_model=List[schemas.Transcript])
def get_transcripts(
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

    transcripts = db.query(models.Transcript).filter(
        models.Transcript.discussion_id == discussion_id
    ).all()

    return transcripts


@router.get("/transcripts/{transcript_id}/segments", response_model=List[schemas.TranscriptSegment])
def get_transcript_segments(
    transcript_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    transcript = db.query(models.Transcript).filter(
        models.Transcript.id == transcript_id
    ).first()

    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    discussion = db.query(models.Discussion).filter(
        models.Discussion.id == transcript.discussion_id,
        models.Discussion.owner_id == current_user.id
    ).first()

    if not discussion:
        raise HTTPException(status_code=403, detail="Permission denied")

    segments = db.query(models.TranscriptSegment).filter(
        models.TranscriptSegment.transcript_id == transcript_id
    ).order_by(models.TranscriptSegment.start_time).all()

    return segments
