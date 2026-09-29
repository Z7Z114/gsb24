"""冒烟测试：只覆盖顺利路径，确认项目能启动、主流程能跑通。"""
import io
import os

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.routers import audio as audio_router
from backend.routers import email as email_router
from backend.routers import summary as summary_router


class _FakeWhisper:
    def transcribe(self, audio_path):
        return {
            "text": "量子意识上传 戴森球文明",
            "language": "zh",
            "segments": [
                {"id": 0, "start": 0.0, "end": 4.0, "text": "量子意识上传", "words": []},
                {"id": 1, "start": 4.0, "end": 9.0, "text": "戴森球文明", "words": []},
            ],
        }


class _FakePyannote:
    def diarize(self, audio_path):
        return [
            {"speaker": "SPEAKER_00", "start": 0.0, "end": 4.0, "duration": 4.0},
            {"speaker": "SPEAKER_01", "start": 4.0, "end": 9.0, "duration": 5.0},
        ]

    def merge_with_transcript(self, diarization_segments, transcript_segments):
        return [
            {
                "speaker": diarization_segments[i]["speaker"],
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
            }
            for i, seg in enumerate(transcript_segments)
        ]


class _Msg:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Msg(content)


class _Resp:
    def __init__(self, content):
        self.choices = [_Choice(content)]


class _Completions:
    def __init__(self, content):
        self._content = content

    def create(self, *args, **kwargs):
        return _Resp(self._content)


class _Chat:
    def __init__(self, content):
        self.completions = _Completions(content)


class _FakeOpenAI:
    def __init__(self, content):
        self.chat = _Chat(content)


SUMMARY_CONTENT = """## 核心设定摘要
一个由量子意识上传驱动的星际文明。

## 技术原理
反物质湮灭引擎。

## 社会结构
铁腕行会制。

## 时间线
```json
[{"year": 2087, "event": "大崩坏", "description": "地表文明毁灭"}]
```
"""


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def auth(client):
    client.post("/register", json={"email": "smoke@example.com", "name": "冒烟", "password": "pw123456"})
    resp = client.post("/token", data={"username": "smoke@example.com", "password": "pw123456"})
    assert resp.status_code == 200
    return {"Authorization": "Bearer " + resp.json()["access_token"]}


def _new_discussion(client, auth, title="新的世界观"):
    resp = client.post("/api/brainstorm/discussions", json={"title": title, "description": "d"}, headers=auth)
    assert resp.status_code == 200
    return resp.json()["id"]


def test_root_serves_frontend(client):
    assert client.get("/").status_code == 200


def test_register_login_and_me(client, auth):
    resp = client.get("/users/me", headers=auth)
    assert resp.status_code == 200
    assert resp.json()["email"] == "smoke@example.com"


def test_create_and_list_discussion(client, auth):
    did = _new_discussion(client, auth, "蒸汽朋克星球")
    listed = client.get("/api/brainstorm/discussions", headers=auth).json()
    assert any(d["id"] == did and d["title"] == "蒸汽朋克星球" for d in listed)


def test_upload_audio_happy_path(client, auth):
    did = _new_discussion(client, auth)
    files = {"file": ("第一幕讨论.wav", io.BytesIO(b"RIFF....WAVEfmt "), "audio/wav")}
    resp = client.post(f"/api/brainstorm/discussions/{did}/upload-audio", files=files, headers=auth)
    assert resp.status_code == 200
    body = resp.json()
    assert body["filename"] == "第一幕讨论.wav"
    assert os.path.exists(body["file_path"])


def test_world_settings_and_concept_arts(client, auth):
    did = _new_discussion(client, auth)
    resp = client.post(
        "/api/brainstorm/world-settings",
        json={"discussion_id": did, "category": "科技", "key": "曲率引擎", "value": "折叠时空"},
        headers=auth,
    )
    assert resp.status_code == 200
    settings = client.get(f"/api/brainstorm/discussions/{did}/world-settings", headers=auth).json()
    assert [s["key"] for s in settings] == ["曲率引擎"]

    resp = client.post(
        "/api/brainstorm/concept-arts",
        json={"discussion_id": did, "title": "戴森球", "category": "场景", "image_url": "data:image/png;base64,AA"},
        headers=auth,
    )
    assert resp.status_code == 200
    arts = client.get(f"/api/brainstorm/discussions/{did}/concept-arts", headers=auth).json()
    assert [a["title"] for a in arts] == ["戴森球"]


def _upload_and_process(client, auth, did, monkeypatch):
    files = {"file": ("第一幕讨论.wav", io.BytesIO(b"RIFF....WAVEfmt "), "audio/wav")}
    audio = client.post(f"/api/brainstorm/discussions/{did}/upload-audio", files=files, headers=auth).json()
    monkeypatch.setattr(audio_router, "whisper_service", _FakeWhisper())
    monkeypatch.setattr(audio_router, "pyannote_service", _FakePyannote())
    resp = client.post(
        "/api/audio/process",
        json={"audio_file_id": audio["id"], "discussion_id": did},
        headers=auth,
    )
    assert resp.status_code == 200
    return audio


def test_transcribe_pipeline(client, auth, monkeypatch):
    did = _new_discussion(client, auth)
    _upload_and_process(client, auth, did, monkeypatch)

    transcripts = client.get(f"/api/audio/transcripts/{did}", headers=auth).json()
    assert len(transcripts) == 1
    assert transcripts[0]["full_text"]

    segments = client.get(f"/api/audio/transcripts/{transcripts[0]['id']}/segments", headers=auth).json()
    assert len(segments) == 2
    assert segments[0]["speaker_label"] == "SPEAKER_00"


def test_generate_summary_and_extract_settings(client, auth, monkeypatch):
    did = _new_discussion(client, auth)
    _upload_and_process(client, auth, did, monkeypatch)

    monkeypatch.setattr(summary_router.openai_service, "client", _FakeOpenAI(SUMMARY_CONTENT))
    resp = client.post("/api/summary/generate", json={"discussion_id": did}, headers=auth)
    assert resp.status_code == 200

    summaries = client.get(f"/api/summary/{did}", headers=auth).json()
    assert len(summaries) == 1
    assert summaries[0]["tech_principles"]
    assert summaries[0]["timeline"][0]["event"] == "大崩坏"

    settings_json = '[{"category": "科技", "key": "量子意识上传", "value": "v", "description": "d", "owner_name": "张工"}]'
    monkeypatch.setattr(summary_router.openai_service, "client", _FakeOpenAI(settings_json))
    resp = client.post(f"/api/summary/extract-settings/{did}", headers=auth)
    assert resp.status_code == 200
    assert resp.json()["extracted_count"] >= 1


def test_send_summary_email(client, auth, monkeypatch):
    did = _new_discussion(client, auth)
    _upload_and_process(client, auth, did, monkeypatch)
    monkeypatch.setattr(summary_router.openai_service, "client", _FakeOpenAI(SUMMARY_CONTENT))
    client.post("/api/summary/generate", json={"discussion_id": did}, headers=auth)
    summary_id = client.get(f"/api/summary/{did}", headers=auth).json()[0]["id"]

    async def _ok(**kwargs):
        return {"status": "success", "recipients": kwargs["recipients"], "message": "sent"}

    monkeypatch.setattr(email_router.email_service, "send_summary_email", _ok)
    resp = client.post(
        "/api/email/send-summary",
        json={"summary_id": summary_id, "recipients": ["team@example.com"], "subject": "纲要"},
        headers=auth,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    logs = client.get(f"/api/email/logs/{summary_id}", headers=auth).json()
    assert [log["status"] for log in logs] == ["success"]
