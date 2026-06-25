# Speech Processing

Real-time Speech Translation and Conversation Summarization using AI.

## Features

* Automatic Speech Recognition (ASR)
* Real-time Speech Translation
* Conversation Summarization
* Evaluation Metrics

  * WER (Word Error Rate)
  * RTF (Real-Time Factor)
  * BLEU Score

---

## Requirements

* Python 3.12
* CUDA 12.4 (recommended)
* NVIDIA GPU (recommended)

---

## Installation


### 1. Install uv (if not installed)

```bash
pip install uv
```

Check installation:

```bash
uv --version
```

### 2. Create a virtual environment

```bash
uv venv
```

### 3. Install dependencies

```bash
uv sync
```

All required packages defined in `pyproject.toml` will be installed automatically.

---

## Hugging Face Token

Create a `.env` file in the project root.

```env
HF_TOKEN=your_huggingface_token
```

The token is only required when downloading the models for the first time.

---

## Run the application

```bash
uv run streamlit run frontend/app.py
```

---

## Models

| Model   | Description         |
| ------- | ------------------- |
| Model 1 | SpeechBrain ASR     |
| Model 2 | Wav2Vec2 Vietnamese |
| Model 3 | Whisper Base        |

---

## Evaluation Metrics

### WER

Measures speech recognition accuracy.

Lower is better.

---

### RTF

Measures real-time processing speed.

```
RTF < 1
```

means the system processes audio faster than real time.

---

### BLEU

Measures machine translation quality.

Higher is better.

---
### Note:
The first time you select a model, it may take a few minutes to download the required files from Hugging Face. Once the download is complete, subsequent runs will load the model from the local `checkpoints/` directory and start much faster.

