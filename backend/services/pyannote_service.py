import os

try:  # 重型可选依赖：未安装时后端仍可导入，走离线分支
    from pyannote.audio import Pipeline

    PYANNOTE_AVAILABLE = True
except ImportError:  # pragma: no cover - 取决于运行环境
    Pipeline = None
    PYANNOTE_AVAILABLE = False
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()


class PyannoteService:
    def __init__(self):
        self.hf_token = os.getenv("HF_TOKEN")
        self.pipeline = None

    def load_pipeline(self):
        if not PYANNOTE_AVAILABLE:
            raise RuntimeError("pyannote.audio is not installed")
        if self.pipeline is None:
            if not self.hf_token:
                raise ValueError("HF_TOKEN not set in environment variables")

            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.hf_token
            )
        return self.pipeline

    def diarize(self, audio_path: str) -> List[Dict[str, Any]]:
        pipeline = self.load_pipeline()

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        diarization = pipeline(audio_path)

        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "speaker": speaker,
                "start": turn.start,
                "end": turn.end,
                "duration": turn.end - turn.start
            })

        return segments

    def merge_with_transcript(
        self,
        diarization_segments: List[Dict[str, Any]],
        transcript_segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        merged = []

        for transcript_seg in transcript_segments:
            trans_start = transcript_seg["start"]
            trans_end = transcript_seg["end"]
            trans_text = transcript_seg["text"]

            best_speaker = None
            max_overlap = 0

            for diar_seg in diarization_segments:
                diar_start = diar_seg["start"]
                diar_end = diar_seg["end"]

                overlap_start = max(trans_start, diar_start)
                overlap_end = min(trans_end, diar_end)
                overlap_duration = max(0, overlap_end - overlap_start)

                if overlap_duration > max_overlap:
                    max_overlap = overlap_duration
                    best_speaker = diar_seg["speaker"]

            merged.append({
                "speaker": best_speaker or "SPEAKER_UNKNOWN",
                "start": trans_start,
                "end": trans_end,
                "text": trans_text
            })

        return merged

    def get_speaker_statistics(self, merged_segments: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        stats = {}

        for seg in merged_segments:
            speaker = seg["speaker"]
            duration = seg["end"] - seg["start"]

            if speaker not in stats:
                stats[speaker] = {
                    "total_duration": 0,
                    "segment_count": 0,
                    "total_words": 0
                }

            stats[speaker]["total_duration"] += duration
            stats[speaker]["segment_count"] += 1
            stats[speaker]["total_words"] += len(seg["text"].split())

        return stats
