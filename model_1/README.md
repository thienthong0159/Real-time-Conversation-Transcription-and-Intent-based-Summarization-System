# Model 1: CNN + Bi-LSTM + CTC

This folder contains the code for the report's first Speech-to-Text candidate:

`Audio -> MFCC -> CNN + Bi-LSTM + CTC -> transcript`

The implementation is intentionally separate from the Express demo so it can be
trained and evaluated in a notebook or CLI workflow, then called by the app once
a checkpoint is available.

## Files

- `model.py`: CNN + Bi-LSTM + CTC acoustic model.
- `text.py`: character vocabulary, CTC encoding, and decoding helpers.
- `features.py`: MFCC extraction from waveform files or base64 audio.
- `metrics.py`: WER and real-time-factor helpers.
- `train.py`: CSV-driven training script.
- `infer.py`: JSON stdin/stdout inference bridge used by the Node app.

## Dataset CSV

Training and evaluation scripts expect a UTF-8 CSV with:

```csv
audio_path,transcript
data/sample_001.wav,hello everyone welcome to the meeting
data/sample_002.wav,we will review the launch plan today
```

Use lowercase normalized transcripts for best CTC convergence.

## Install

Install the ML dependencies in the environment where you train or run inference:

```bash
pip install torch torchaudio
```

## Train

```bash
python model_1/train.py --train_csv data/train.csv --valid_csv data/valid.csv --epochs 30 --checkpoint artifacts/model1.pt
```

## Infer

```bash
echo {"audio_path":"data/example.wav","checkpoint":"artifacts/model1.pt"} | python model_1/infer.py
```

The Express app can call this bridge when these environment variables are set:

```env
MODEL1_STT_ENABLED=true
MODEL1_PYTHON=python
MODEL1_SCRIPT=model_1/infer.py
MODEL1_CHECKPOINT=artifacts/model1.pt
```

If the variables, checkpoint, or real audio payload are missing, the web demo
falls back to the existing mock transcript.
