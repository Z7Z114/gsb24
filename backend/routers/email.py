from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas, auth
from ..database import get_db
from ..services.email_service import EmailService

router = APIRouter(prefix="/api/email", tags=["email"])

email_service = EmailService()


@router.post("/send-summary")
async def send_summary_email(
    request: schemas.EmailRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    summary = db.query(models.Summary).filter(
        models.Summary.id == request.summary_id
    ).first()

    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    discussion = db.query(models.Discussion).filter(
        models.Discussion.id == summary.discussion_id,
        models.Discussion.owner_id == current_user.id
    ).first()

    if not discussion:
        raise HTTPException(status_code=403, detail="Permission denied")

    result = await email_service.send_summary_email(
        recipients=request.recipients,
        subject=request.subject,
        summary_content=summary.content,
        markdown_content=summary.markdown_content,
        discussion_title=discussion.title,
        tech_principles=summary.tech_principles,
        social_structure=summary.social_structure,
        timeline=summary.timeline
    )

    for recipient in request.recipients:
        log = models.EmailLog(
            summary_id=summary.id,
            recipient=recipient,
            subject=request.subject or f"[世界观设定] {discussion.title}",
            status=result["status"]
        )
        db.add(log)
    db.commit()

    return result


@router.post("/send-notification")
async def send_notification(
    recipients: List[str],
    subject: str,
    message: str,
    current_user: models.User = Depends(auth.get_current_user)
):
    result = await email_service.send_notification(
        recipients=recipients,
        subject=subject,
        message=message
    )
    return result


@router.get("/logs/{summary_id}")
def get_email_logs(
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

    logs = db.query(models.EmailLog).filter(
        models.EmailLog.summary_id == summary_id
    ).all()

    return logs
