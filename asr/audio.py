from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import librosa
import numpy as np
import soundfile as sf

TARGET_SAMPLE_RATE = 16_000


def load_audio_mono(audio: str | Path | tuple[int, Any]) -> np.ndarray:
    """Decode an audio path or Streamlit microphone tuple to 16 kHz mono float32."""
    if isinstance(audio, tuple):
        sample_rate, samples = audio
        data = np.asarray(samples, dtype=np.float32)
        if data.ndim == 2:
            # PyAV frames are usually (channels, samples); other callers often
            # provide (samples, channels).
            data = data.mean(axis=0 if data.shape[0] <= data.shape[1] else 1)
        if np.issubdtype(np.asarray(samples).dtype, np.integer):
            data /= np.iinfo(np.asarray(samples).dtype).max
        if sample_rate != TARGET_SAMPLE_RATE:
            data = librosa.resample(data, orig_sr=sample_rate, target_sr=TARGET_SAMPLE_RATE)
        return np.ascontiguousarray(data, dtype=np.float32)

    samples, _ = librosa.load(str(audio), sr=TARGET_SAMPLE_RATE, mono=True, dtype=np.float32)
    if not samples.size:
        raise ValueError("The audio contains no samples.")
    return np.ascontiguousarray(samples, dtype=np.float32)


def write_temp_wav(samples: np.ndarray) -> str:
    """Persist normalized audio for backends that expect a filename."""
    handle = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    handle.close()
    sf.write(handle.name, samples, TARGET_SAMPLE_RATE, subtype="PCM_16")
    return handle.name


def write_uploaded_audio(data: bytes, suffix: str = ".wav") -> str:
    """Save uploaded bytes and return a path suitable for decoder libraries."""
    handle = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    handle.write(data)
    handle.close()
    return handle.name


def remove_temp_audio(path: str | None) -> None:
    if path:
        try:
            os.unlink(path)
        except OSError:
            pass
