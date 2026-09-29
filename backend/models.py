from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    discussions = relationship("Discussion", back_populates="owner")
    transcript_segments = relationship("TranscriptSegment", back_populates="speaker")


class Discussion(Base):
    __tablename__ = "discussions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="discussions")
    audio_files = relationship("AudioFile", back_populates="discussion")
    transcripts = relationship("Transcript", back_populates="discussion")
    world_settings = relationship("WorldSetting", back_populates="discussion")
    summaries = relationship("Summary", back_populates="discussion")
    concept_arts = relationship("ConceptArt", back_populates="discussion")


class AudioFile(Base):
    __tablename__ = "audio_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    duration = Column(Integer)
    discussion_id = Column(Integer, ForeignKey("discussions.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    discussion = relationship("Discussion", back_populates="audio_files")
    transcript = relationship("Transcript", back_populates="audio_file", uselist=False)


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    audio_file_id = Column(Integer, ForeignKey("audio_files.id"))
    discussion_id = Column(Integer, ForeignKey("discussions.id"))
    full_text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    audio_file = relationship("AudioFile", back_populates="transcript")
    discussion = relationship("Discussion", back_populates="transcripts")
    segments = relationship("TranscriptSegment", back_populates="transcript")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"))
    speaker_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    speaker_label = Column(String)
    start_time = Column(Integer)
    end_time = Column(Integer)
    text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    transcript = relationship("Transcript", back_populates="segments")
    speaker = relationship("User", back_populates="transcript_segments")


class WorldSetting(Base):
    __tablename__ = "world_settings"

    id = Column(Integer, primary_key=True, index=True)
    discussion_id = Column(Integer, ForeignKey("discussions.id"))
    category = Column(String)
    key = Column(String)
    value = Column(Text)
    description = Column(Text)
    owner_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    discussion = relationship("Discussion", back_populates="world_settings")


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    discussion_id = Column(Integer, ForeignKey("discussions.id"))
    content = Column(Text)
    markdown_content = Column(Text)
    tech_principles = Column(Text)
    social_structure = Column(Text)
    timeline = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    discussion = relationship("Discussion", back_populates="summaries")


class ConceptArt(Base):
    __tablename__ = "concept_arts"

    id = Column(Integer, primary_key=True, index=True)
    discussion_id = Column(Integer, ForeignKey("discussions.id"))
    title = Column(String)
    category = Column(String)
    description = Column(Text)
    image_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    discussion = relationship("Discussion", back_populates="concept_arts")


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    summary_id = Column(Integer, ForeignKey("summaries.id"))
    recipient = Column(String)
    subject = Column(String)
    status = Column(String)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
