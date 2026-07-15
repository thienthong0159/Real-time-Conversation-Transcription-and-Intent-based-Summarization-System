from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Callable

from asr.common import ASRSegment, TranscriptionResult

BACKENDS = ("Faster PhoWhisper", "Cascaded PhoWhisper", "Whisper Streaming")


@dataclass(frozen=True, slots=True)
class TranscriptionConfig:
    backend: str
    model_path: str
    device: str = "auto"
    beam_size: int = 5
    compute_type: str = "auto"
    enable_vad: bool = True


@dataclass(frozen=True, slots=True)
class RunMetrics:
    result: TranscriptionResult
    inference_seconds: float
    audio_seconds: float

    @property
    def processing_speed(self) -> float:
        return self.audio_seconds / self.inference_seconds if self.inference_seconds else 0.0


def run_transcription(
    audio: str | tuple[int, object],
    config: TranscriptionConfig,
    audio_seconds: float,
    on_stream_update: Callable[[TranscriptionResult], None] | None = None,
) -> RunMetrics:
    """Dispatch to a backend while keeping the UI independent of model code."""
    started = perf_counter()
    if config.backend == "Faster PhoWhisper":
        from asr.faster_whisper_backend import transcribe_faster_whisper
        segments = transcribe_faster_whisper(audio, config.model_path, config.device, config.compute_type, config.beam_size, config.enable_vad)
        result = TranscriptionResult(segments)
    elif config.backend == "Cascaded PhoWhisper":
        from asr.cascaded_encoder_backend import transcribe_cascaded_encoder
        segments = transcribe_cascaded_encoder(audio, config.model_path, config.device, config.beam_size)
        result = TranscriptionResult(segments)
    elif config.backend == "Whisper Streaming":
        from asr.whisper_streaming_backend import transcribe_whisper_streaming
        result = transcribe_whisper_streaming(
            audio, config.model_path, config.device, config.compute_type,
            config.beam_size, config.enable_vad, on_update=on_stream_update,
        )
    else:
        raise ValueError(f"Unknown ASR backend: {config.backend}")
    return RunMetrics(result=result, inference_seconds=perf_counter() - started, audio_seconds=audio_seconds)
