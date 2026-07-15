"""Run the project Whisper Streaming backend from a terminal microphone.

Example:
    uv run python scripts/test_treaming.py --device auto

Stop with Ctrl+C to flush the final, unconfirmed hypothesis.
"""

from __future__ import annotations

import argparse
import queue
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from asr.common import TranscriptionResult
from asr.whisper_streaming_backend import WhisperStreamingSession


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Live Vietnamese Whisper Streaming transcription.")
    parser.add_argument("--model-path", default="checkpoints/phowhisper-base-ct2")
    parser.add_argument("--device", choices=("auto", "cuda", "cpu"), default="cuda")
    parser.add_argument("--compute-type", choices=("auto", "float16", "int8"), default="auto")
    parser.add_argument("--beam-size", type=int, choices=range(1, 11), default=3)
    parser.add_argument("--chunk-seconds", type=float, default=1.0)
    parser.add_argument(
        "--queue-size", type=int, default=512,
        help="Maximum pending microphone frames. Oldest frames are discarded when full (default: 512).",
    )
    parser.add_argument("--input-device", help="Sounddevice input device name or numeric ID.")
    parser.add_argument("--no-vad", action="store_true", help="Disable faster-whisper VAD filtering.")
    return parser


def print_new_segments(result: TranscriptionResult, printed: int) -> int:
    for segment in result.segments[printed:]:
        print(f"[{segment.start:.2f} - {segment.end:.2f}] {segment.text}", flush=True)
    return len(result.segments)


def main() -> int:
    args = build_parser().parse_args()
    if args.chunk_seconds <= 0:
        raise ValueError("--chunk-seconds must be greater than zero.")
    if args.queue_size <= 0:
        raise ValueError("--queue-size must be greater than zero.")
    if not Path(args.model_path).exists():
        raise FileNotFoundError(f"Model checkpoint not found: {args.model_path}")

    try:
        import sounddevice as sd
    except ImportError as error:
        raise RuntimeError("Install sounddevice before using terminal microphone streaming.") from error

    audio_queue: queue.Queue[tuple[int, np.ndarray]] = queue.Queue(maxsize=args.queue_size)
    dropped_frames = 0

    def capture(indata: np.ndarray, frames: int, time_info, status) -> None:
        nonlocal dropped_frames
        del frames, time_info
        if status:
            print(f"Audio warning: {status}", file=sys.stderr)
        try:
            audio_queue.put_nowait((int(stream.samplerate), indata.copy()))
        except queue.Full:
            # Preserve the most recent speech. Keeping stale audio would make
            # the transcript increasingly delayed after a slow model update.
            try:
                audio_queue.get_nowait()
                audio_queue.put_nowait((int(stream.samplerate), indata.copy()))
                dropped_frames += 1
                if dropped_frames == 1 or dropped_frames % 25 == 0:
                    print(
                        f"Audio processing is behind realtime; replaced {dropped_frames} oldest frame(s).",
                        file=sys.stderr,
                    )
            except queue.Empty:
                pass

    print("Loading Whisper Streaming model…", flush=True)
    session = WhisperStreamingSession(
        model_path=args.model_path,
        device=args.device,
        compute_type=args.compute_type,
        beam_size=args.beam_size,
        vad_filter=not args.no_vad,
        min_chunk_seconds=args.chunk_seconds,
    )
    printed = 0
    print("Listening. Speak Vietnamese; press Ctrl+C to stop.", flush=True)
    with sd.InputStream(
        device=args.input_device,
        channels=1,
        dtype="float32",
        callback=capture,
    ) as stream:
        try:
            while True:
                sample_rate, samples = audio_queue.get()
                # Process all already-received frames together. This catches up
                # after model inference without asking Whisper to decode each
                # tiny device callback independently.
                chunks = [samples]
                while True:
                    try:
                        queued_rate, queued_samples = audio_queue.get_nowait()
                    except queue.Empty:
                        break
                    if queued_rate == sample_rate:
                        chunks.append(queued_samples)
                    else:
                        result = session.push_audio((queued_rate, queued_samples))
                        printed = print_new_segments(result, printed)
                result = session.push_audio((sample_rate, np.concatenate(chunks, axis=0)))
                printed = print_new_segments(result, printed)
        except KeyboardInterrupt:
            print("\nFinalizing…", flush=True)

    final_result = session.finish()
    printed = print_new_segments(final_result, printed)
    if final_result.partial:
        print(f"[partial] {final_result.partial}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
