import os
from pathlib import Path

import torch
import librosa
from dotenv import load_dotenv
from transformers import WhisperProcessor, WhisperForConditionalGeneration

from backend.utils.device import get_device, get_torch_dtype


ROOT_DIR = Path(__file__).resolve().parents[2]
LOCAL_MODEL_DIR = ROOT_DIR / "checkpoints" / "whisper-base"

load_dotenv(ROOT_DIR / ".env")
HF_TOKEN = os.getenv("HF_TOKEN")


class WhisperASR:
    def __init__(self, model_name="openai/whisper-base"):
        self.model_name = model_name
        self.processor = None
        self.model = None
        self.device = get_device()
        self.torch_dtype = get_torch_dtype()

    def _load_from_local(self):
        self.processor = WhisperProcessor.from_pretrained(
            LOCAL_MODEL_DIR,
            language="Vietnamese",
            task="transcribe",
            local_files_only=True,
        )

        self.model = WhisperForConditionalGeneration.from_pretrained(
            LOCAL_MODEL_DIR,
            torch_dtype=self.torch_dtype,
            local_files_only=True,
        )

    def _download_and_save_once(self):
        LOCAL_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        hf_token = os.getenv("HF_TOKEN")

        print("Local model not found. Downloading Whisper once...")

        processor = WhisperProcessor.from_pretrained(
            self.model_name,
            language="Vietnamese",
            task="transcribe",
            token=hf_token,
        )

        model = WhisperForConditionalGeneration.from_pretrained(
            self.model_name,
            torch_dtype=self.torch_dtype,
            token=hf_token,
        )

        processor.save_pretrained(LOCAL_MODEL_DIR)
        model.save_pretrained(LOCAL_MODEL_DIR)

        print(f"Saved Whisper to: {LOCAL_MODEL_DIR}")

        del processor
        del model

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def load(self):
        if self.model is not None:
            return

        try:
            print(f"Trying to load Whisper from local folder: {LOCAL_MODEL_DIR}")
            self._load_from_local()
            print("Loaded Whisper from local folder.")
        except Exception as e:
            print("Cannot load local Whisper.")
            print("Reason:", e)

            self._download_and_save_once()

            print("Loading Whisper again from local folder...")
            self._load_from_local()

        self.model.to(self.device)
        self.model.eval()

        forced_decoder_ids = self.processor.get_decoder_prompt_ids(
            language="Vietnamese",
            task="transcribe",
        )
        self.model.config.forced_decoder_ids = forced_decoder_ids

        print("Whisper ready.")
        print("Device:", self.device)
        print("Dtype:", self.torch_dtype)

    def transcribe(self, audio_path: str) -> str:
        if self.model is None:
            self.load()

        audio, _ = librosa.load(audio_path, sr=16000)

        inputs = self.processor(
            audio,
            sampling_rate=16000,
            return_tensors="pt",
        )

        input_features = inputs.input_features.to(
            device=self.device,
            dtype=self.torch_dtype,
        )

        with torch.no_grad():
            predicted_ids = self.model.generate(
                input_features,
                max_length=128,
            )

        text = self.processor.batch_decode(
            predicted_ids,
            skip_special_tokens=True,
        )[0]

        return text.strip()

    def unload(self):
        if self.model is not None:
            del self.model

        if self.processor is not None:
            del self.processor

        self.model = None
        self.processor = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
