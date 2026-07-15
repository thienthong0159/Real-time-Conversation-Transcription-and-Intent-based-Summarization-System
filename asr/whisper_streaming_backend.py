from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Callable

import numpy as np

from .audio import TARGET_SAMPLE_RATE, load_audio_mono
from .common import ASRSegment, TranscriptionResult
from .transformers_backend import resolve_device

_STREAMING_FILE = Path(__file__).parents[1] / "external" / "whisper_streaming" / "whisper_online.py"


def _streaming_module():
    """Load the vendored engine lazily, so other modes have no streaming cost."""
    module_name = "vendored_whisper_online"
    if module_name in sys.modules:
        return sys.modules[module_name]
    if not _STREAMING_FILE.exists():
        raise FileNotFoundError(f"Whisper Streaming source not found: {_STREAMING_FILE}")
    source_dir = str(_STREAMING_FILE.parent)
    if source_dir not in sys.path:
        sys.path.insert(0, source_dir)
    spec = importlib.util.spec_from_file_location(module_name, _STREAMING_FILE)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the bundled Whisper Streaming engine.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def transcribe_whisper_streaming(
    audio: str | tuple[int, object],
    model_path: str,
    device: str = "auto",
    compute_type: str = "auto",
    beam_size: int = 5,
    vad_filter: bool = True,
    chunk_seconds: float = 1.0,
    on_update: Callable[[TranscriptionResult], None] | None = None,
) -> TranscriptionResult:
    """Run the vendored local-agreement pipeline over an audio recording.

    Confirmed output comes directly from ``OnlineASRProcessor``.  The final
    unconfirmed hypothesis is returned as a partial transcript.
    """
    session = WhisperStreamingSession(
        model_path, device, compute_type, beam_size, vad_filter,
    )
    samples = load_audio_mono(audio)
    size = max(1, int(chunk_seconds * TARGET_SAMPLE_RATE))
    for start in range(0, len(samples), size):
        result = session.push_audio((TARGET_SAMPLE_RATE, samples[start : start + size]))
        if on_update:
            on_update(result)
    result = session.finish()
    if on_update:
        on_update(result)
    return result


class WhisperStreamingSession:
    """Stateful adapter for a real microphone stream.

    Keep one instance per active browser stream.  It owns the vendored
    ``OnlineASRProcessor`` so its local-agreement buffer survives Streamlit
    reruns and only confirmed text is emitted.
    """

    def __init__(
        self,
        model_path: str,
        device: str = "auto",
        compute_type: str = "auto",
        beam_size: int = 5,
        vad_filter: bool = True,
        min_chunk_seconds: float = 1.0,
    ) -> None:
        self.online = _create_online_processor(
            model_path, device, compute_type, beam_size, vad_filter,
        )
        self.confirmed: list[ASRSegment] = []
        self.min_chunk_samples = max(1, int(min_chunk_seconds * TARGET_SAMPLE_RATE))
        self.pending_audio = np.array([], dtype=np.float32)

    @property
    def buffered_seconds(self) -> float:
        return len(self.pending_audio) / TARGET_SAMPLE_RATE

    def push_audio(self, audio: tuple[int, object]) -> TranscriptionResult:
        samples = load_audio_mono(audio)
        if not samples.size:
            return TranscriptionResult(list(self.confirmed))
        self.pending_audio = np.concatenate((self.pending_audio, samples))
        # WebRTC emits very short frames.  Decoding every frame gives Whisper
        # almost no acoustic context and makes local agreement unstable.
        if len(self.pending_audio) < self.min_chunk_samples:
            return TranscriptionResult(list(self.confirmed))
        self.online.insert_audio_chunk(self.pending_audio)
        self.pending_audio = np.array([], dtype=np.float32)
        begin, end, text = self.online.process_iter()
        if text and begin is not None and end is not None:
            self.confirmed.append(ASRSegment(float(begin), float(end), text.strip()))
        return TranscriptionResult(list(self.confirmed))

    def finish(self) -> TranscriptionResult:
        if self.pending_audio.size:
            self.online.insert_audio_chunk(self.pending_audio)
            self.pending_audio = np.array([], dtype=np.float32)
            begin, end, text = self.online.process_iter()
            if text and begin is not None and end is not None:
                self.confirmed.append(ASRSegment(float(begin), float(end), text.strip()))
        begin, end, text = self.online.finish()
        partial = text.strip() if text and begin is not None and end is not None else ""
        return TranscriptionResult(list(self.confirmed), partial=partial)


def _create_online_processor(
    model_path: str,
    device: str,
    compute_type: str,
    beam_size: int,
    vad_filter: bool,
):
    engine = _streaming_module()
    selected_device = resolve_device(device)
    selected_compute = compute_type if compute_type != "auto" else ("float16" if selected_device == "cuda" else "int8")

    class ConfiguredFasterWhisper(engine.FasterWhisperASR):
        def load_model(self, modelsize=None, cache_dir=None, model_dir=None):
            from faster_whisper import WhisperModel

            source = model_dir or modelsize
            if not source:
                raise ValueError("Choose a model path for Whisper Streaming.")
            return WhisperModel(source, device=selected_device, compute_type=selected_compute)

        def transcribe(self, samples, init_prompt=""):
            segments, _ = self.model.transcribe(
                samples, language="vi", initial_prompt=init_prompt,
                beam_size=beam_size, word_timestamps=True,
                condition_on_previous_text=True, vad_filter=vad_filter,
            )
            return list(segments)

    asr = ConfiguredFasterWhisper(lan="vi", model_dir=model_path)
    return engine.OnlineASRProcessor(
        asr, tokenizer=None, buffer_trimming=("segment", 15),
    )
