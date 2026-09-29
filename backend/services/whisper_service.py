import os
from typing import List, Dict, Any

try:  # 重型可选依赖：未安装时后端仍可导入，走离线分支
    import whisper

    WHISPER_AVAILABLE = True
except ImportError:  # pragma: no cover - 取决于运行环境
    whisper = None
    WHISPER_AVAILABLE = False

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover - 取决于运行环境
    torch = None
    TORCH_AVAILABLE = False

class WhisperService:
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.device = "cuda" if (torch is not None and torch.cuda.is_available()) else "cpu"
        self.model = None

    def load_model(self):
        if not WHISPER_AVAILABLE:
            raise RuntimeError("whisper model is not installed")
        if self.model is None:
            self.model = whisper.load_model(self.model_size, device=self.device)
        return self.model

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        model = self.load_model()

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        result = model.transcribe(
            audio_path,
            verbose=False,
            word_timestamps=True
        )

        return {
            "text": result["text"],
            "language": result.get("language", "unknown"),
            "segments": [
                {
                    "id": seg["id"],
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                    "words": seg.get("words", [])
                }
                for seg in result.get("segments", [])
            ]
        }

    def transcribe_to_segments(self, audio_path: str) -> List[Dict[str, Any]]:
        result = self.transcribe(audio_path)
        return result["segments"]
