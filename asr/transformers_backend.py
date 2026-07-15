from __future__ import annotations

import torch


def resolve_device(device: str) -> str:
    """Resolve an application device setting without coupling inference to the UI."""
    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        return "cpu"
    return device
