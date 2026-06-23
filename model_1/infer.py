import argparse
import json
import mimetypes
import sys

import torch

from features import MfccExtractor, pad_feature_batch
from metrics import Timer, real_time_factor
from model import load_model
from text import TextTransform


def suffix_for_mime(mime_type):
    if not mime_type:
        return ".webm"
    return mimetypes.guess_extension(mime_type.split(";")[0]) or ".webm"


def transcribe(payload):
    checkpoint_path = payload.get("checkpoint")
    if not checkpoint_path:
        raise ValueError("checkpoint is required")

    device = payload.get("device") or ("cuda" if torch.cuda.is_available() else "cpu")
    model, checkpoint = load_model(checkpoint_path, device=device)
    text = TextTransform(checkpoint.get("vocab"))
    extractor = MfccExtractor(
        sample_rate=checkpoint.get("sample_rate", 16000),
        n_mfcc=checkpoint.get("config", {}).get("n_mfcc", 40),
    )

    if payload.get("audio_base64"):
        features = extractor.from_base64(payload["audio_base64"], suffix_for_mime(payload.get("mime_type")))
    elif payload.get("audio_path"):
        features = extractor.from_file(payload["audio_path"])
    else:
        raise ValueError("audio_base64 or audio_path is required")

    batch, lengths = pad_feature_batch([features])
    with Timer() as timer, torch.no_grad():
        log_probs, _ = model(batch.to(device), lengths.to(device))
        prediction = log_probs.argmax(dim=-1)[:, 0].detach().cpu().tolist()

    transcript = text.decode_greedy(prediction)
    return {
        "provider": "model_1",
        "isMock": False,
        "transcript": transcript,
        "metrics": {
            "rtf": real_time_factor(timer.elapsed_seconds, payload.get("audio_seconds")),
            "processing_seconds": timer.elapsed_seconds,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint")
    args = parser.parse_args()
    payload = json.load(sys.stdin)
    if args.checkpoint:
        payload["checkpoint"] = args.checkpoint
    try:
        print(json.dumps({"success": True, "data": transcribe(payload)}, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc)}), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
