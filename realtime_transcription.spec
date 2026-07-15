# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build specification for the Realtime Transcription desktop app.

Build from the repository root after installing PyInstaller:
    uv run pyinstaller --clean --noconfirm realtime_transcription.spec

The output executable is ``dist/RealtimeTranscription/RealtimeTranscription.exe``.
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_dynamic_libs


ROOT = Path(SPECPATH).resolve()

# Collect complete packages rather than relying solely on static import analysis:
# model backends and Whisper Streaming load several modules lazily at runtime.
PACKAGES = (
    "PySide6",
    "shiboken6",
    "torch",
    "transformers",
    "faster_whisper",
    "ctranslate2",
    "tokenizers",
    "safetensors",
    "sentencepiece",
    "av",
    "librosa",
    "soundfile",
    "sounddevice",
    "numpy",
    "scipy",
    "numba",
    "llvmlite",
    "huggingface_hub",
    "yaml",
    "regex",
    "tqdm",
    "packaging",
)

datas: list[tuple[str, str]] = []
binaries: list[tuple[str, str]] = []
hiddenimports: list[str] = [
    # Application modules are dispatched dynamically from pipeline.py.
    "asr.audio",
    "asr.common",
    "asr.faster_whisper_backend",
    "asr.cascaded_encoder_backend",
    "asr.transformers_backend",
    "asr.whisper_streaming_backend",
    "pipeline",
    # CTranslate2 / faster-whisper optional runtime providers.
    "ctranslate2",
    "faster_whisper.audio",
    "faster_whisper.feature_extractor",
    "faster_whisper.tokenizer",
    "faster_whisper.transcribe",
]

for package in PACKAGES:
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas.extend(package_datas)
    binaries.extend(package_binaries)
    hiddenimports.extend(package_hiddenimports)

# Ensure CTranslate2 shared libraries are present even if its hook changes.
binaries.extend(collect_dynamic_libs("ctranslate2"))

# The vendored streaming engine is loaded by filename, not as an importable
# package, and both checkpoints must remain at their repository-relative paths.
for folder in ("external/whisper_streaming", "checkpoints"):
    source = ROOT / folder
    if not source.exists():
        raise FileNotFoundError(f"Required bundle directory is missing: {source}")
    datas.append((str(source), folder))

# Eliminate duplicated entries introduced by overlapping PyInstaller hooks.
datas = list(dict.fromkeys(datas))
binaries = list(dict.fromkeys(binaries))
hiddenimports = list(dict.fromkeys(hiddenimports))

a = Analysis(
    [str(ROOT / "app.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["streamlit", "streamlit_webrtc", "pyngrok"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RealtimeTranscription",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Do not compress Qt, Torch, or CTranslate2 native libraries.
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="RealtimeTranscription",
)
