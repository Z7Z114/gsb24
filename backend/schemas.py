from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Dict, Any


class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DiscussionBase(BaseModel):
    title: str
    description: Optional[str] = None


class DiscussionCreate(DiscussionBase):
    pass


class Discussion(DiscussionBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AudioFileBase(BaseModel):
    filename: str
    duration: Optional[int] = None


class AudioFileCreate(AudioFileBase):
    file_path: str
    discussion_id: int


class AudioFile(AudioFileBase):
    id: int
    file_path: str
    discussion_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TranscriptSegmentBase(BaseModel):
    speaker_label: str
    start_time: int
    end_time: int
    text: str


class TranscriptSegmentCreate(TranscriptSegmentBase):
    transcript_id: int
    speaker_id: Optional[int] = None


class TranscriptSegment(TranscriptSegmentBase):
    id: int
    transcript_id: int
    speaker_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TranscriptBase(BaseModel):
    audio_file_id: int
    discussion_id: int
    full_text: str


class TranscriptCreate(TranscriptBase):
    pass


class Transcript(TranscriptBase):
    id: int
    created_at: datetime
    segments: List[TranscriptSegment] = []

    class Config:
        from_attributes = True


class WorldSettingBase(BaseModel):
    category: str
    key: str
    value: str
    description: Optional[str] = None
    owner_name: Optional[str] = None


class WorldSettingCreate(WorldSettingBase):
    discussion_id: int


class WorldSetting(WorldSettingBase):
    id: int
    discussion_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SummaryBase(BaseModel):
    content: str
    markdown_content: str
    tech_principles: str
    social_structure: str
    timeline: List[Dict[str, Any]]


class SummaryCreate(SummaryBase):
    discussion_id: int


class Summary(SummaryBase):
    id: int
    discussion_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ConceptArtBase(BaseModel):
    title: str
    category: str
    description: Optional[str] = None
    image_url: str


class ConceptArtCreate(ConceptArtBase):
    discussion_id: int


class ConceptArt(ConceptArtBase):
    id: int
    discussion_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AudioProcessingRequest(BaseModel):
    audio_file_id: int
    discussion_id: int


class SummaryRequest(BaseModel):
    discussion_id: int
    custom_prompt: Optional[str] = None


class EmailRequest(BaseModel):
    summary_id: int
    recipients: List[EmailStr]
    subject: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
