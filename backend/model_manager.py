import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HF_CACHE = PROJECT_ROOT / "checkpoints" / "hf_cache"
HF_CACHE.mkdir(parents=True, exist_ok=True)

os.environ["HF_HOME"] = str(HF_CACHE)
os.environ["HF_HUB_CACHE"] = str(HF_CACHE)
os.environ["TRANSFORMERS_CACHE"] = str(HF_CACHE)


class ModelManager:
    def __init__(self):
        self.current_model = None
        self.current_model_name = None

    def load_model(self, model_name, progress_callback=None):
        if self.current_model_name == model_name and self.current_model is not None:
            if progress_callback:
                progress_callback("Model is already loaded.")
            return self.current_model

        self.unload_current_model()

        if progress_callback:
            progress_callback("Importing model...")

        if model_name == "model1_cnn_bilstm_ctc":
            from backend.models.model_1.infer import Model1ASR

            self.current_model = Model1ASR()
        elif model_name == "model2_deepspeech":
            from backend.models.model2_wav2vec2 import Wav2Vec2ASR

            self.current_model = Wav2Vec2ASR()
        elif model_name == "model3_whisper":
            from backend.models.model3_whisper import WhisperASR

            self.current_model = WhisperASR()
        else:
            raise ValueError(f"Model '{model_name}' is not supported.")

        if progress_callback:
            progress_callback("Loading checkpoint...")

        self.current_model.load()
        self.current_model_name = model_name

        if progress_callback:
            progress_callback("Model is ready.")

        return self.current_model

    def unload_current_model(self):
        if self.current_model is not None:
            self.current_model.unload()

        self.current_model = None
        self.current_model_name = None

    def transcribe(self, audio_path):
        if self.current_model is None:
            raise RuntimeError("No model is loaded.")

        return self.current_model.transcribe(audio_path)
