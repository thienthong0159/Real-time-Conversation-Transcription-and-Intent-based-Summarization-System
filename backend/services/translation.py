import os
import re
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
LOCAL_MODEL_DIR = ROOT_DIR / "checkpoints" / "nllb-200-distilled-600M"

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(ROOT_DIR / ".env")

HF_TOKEN = os.getenv("HF_TOKEN")


LANGUAGES = {
    "English": "eng_Latn",
    "French": "fra_Latn",
    "Japanese": "jpn_Jpan",
    "Korean": "kor_Hang",
    "Chinese": "zho_Hans",
}


class TranslationService:
    def __init__(self, model_name="facebook/nllb-200-distilled-600M"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = None
        self.torch_dtype = None
        self.torch = None
        self.auto_model = None
        self.auto_tokenizer = None

    def _ensure_dependencies(self):
        if self.torch is not None:
            return

        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "Translation requires torch and transformers. "
                "Install the project dependencies with `uv sync` before using translation."
            ) from exc

        from backend.utils.device import get_device, get_torch_dtype

        self.torch = torch
        self.auto_model = AutoModelForSeq2SeqLM
        self.auto_tokenizer = AutoTokenizer
        self.device = get_device()
        self.torch_dtype = get_torch_dtype()

    def _load_from_local(self):
        self.tokenizer = self.auto_tokenizer.from_pretrained(
            LOCAL_MODEL_DIR,
            local_files_only=True,
        )
        self.model = self.auto_model.from_pretrained(
            LOCAL_MODEL_DIR,
            torch_dtype=self.torch_dtype,
            local_files_only=True,
        )

    def _download_and_save_once(self):
        LOCAL_MODEL_DIR.mkdir(parents=True, exist_ok=True)

        self.tokenizer = self.auto_tokenizer.from_pretrained(
            self.model_name,
            token=HF_TOKEN,
        )
        self.model = self.auto_model.from_pretrained(
            self.model_name,
            torch_dtype=self.torch_dtype,
            token=HF_TOKEN,
        )

        self.tokenizer.save_pretrained(LOCAL_MODEL_DIR)
        self.model.save_pretrained(LOCAL_MODEL_DIR, safe_serialization=True)

    def load(self, progress_callback=None):
        if self.model is not None:
            return

        self._ensure_dependencies()

        if progress_callback:
            progress_callback("Loading translation model...")

        try:
            self._load_from_local()
        except Exception:
            if progress_callback:
                progress_callback("Downloading translation model...")
            self._download_and_save_once()

        self.model.to(self.device)
        self.model.eval()

        if progress_callback:
            progress_callback("Translation model ready.")

    def translate(self, text, target_lang="eng_Latn", source_lang="vie_Latn"):
        if not text or not text.strip():
            return ""

        if self.model is None:
            self.load()

        self.tokenizer.src_lang = source_lang
        forced_bos_token_id = self.tokenizer.convert_tokens_to_ids(target_lang)

        translated_chunks = [
            self._translate_chunk(chunk.strip(), forced_bos_token_id)
            for chunk in self._chunk_text(text)
            if chunk.strip()
        ]
        return " ".join(translated_chunks).strip()

    def _translate_chunk(self, text, forced_bos_token_id):
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        with self.torch.no_grad():
            generated_tokens = self.model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_length=512,
                num_beams=4,
            )

        return self.tokenizer.batch_decode(
            generated_tokens,
            skip_special_tokens=True,
        )[0]

    def _chunk_text(self, text, max_chars=900):
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        chunks = []
        current = ""

        for sentence in sentences:
            if not sentence:
                continue

            next_chunk = f"{current} {sentence}".strip()
            if len(next_chunk) <= max_chars:
                current = next_chunk
                continue

            if current:
                chunks.append(current)

            if len(sentence) <= max_chars:
                current = sentence
            else:
                chunks.extend(
                    sentence[index:index + max_chars]
                    for index in range(0, len(sentence), max_chars)
                )
                current = ""

        if current:
            chunks.append(current)

        return chunks

    def unload(self):
        if self.model is not None:
            del self.model

        if self.tokenizer is not None:
            del self.tokenizer

        self.model = None
        self.tokenizer = None

        if self.torch is not None and self.torch.cuda.is_available():
            self.torch.cuda.empty_cache()
