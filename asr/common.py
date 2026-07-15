from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ASRSegment:
    """A timestamped piece of recognized speech."""

    start: float
    end: float
    text: str
    confirmed: bool = True


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    segments: list[ASRSegment]
    partial: str = ""

    @property
    def text(self) -> str:
        return " ".join(segment.text for segment in self.segments).strip()
