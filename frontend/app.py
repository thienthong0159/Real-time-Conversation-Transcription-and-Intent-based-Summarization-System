import sys
from pathlib import Path

import streamlit as st
from streamlit_mic_recorder import mic_recorder

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from backend.model_manager import ModelManager

import warnings

warnings.filterwarnings("ignore", category=UserWarning)

UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="Conversation Transcription",
    page_icon="🎙️",
    layout="wide",
)

st.title("🎙️ Conversation Transcription Demo")
st.caption("Giai đoạn 1: Thu âm hoặc upload audio, sau đó nhận dạng bằng Whisper")

if "model_manager" not in st.session_state:
    st.session_state.model_manager = ModelManager()

if "loaded_model" not in st.session_state:
    st.session_state.loaded_model = None

if "audio_path" not in st.session_state:
    st.session_state.audio_path = None

model_options = {
    "Model 3 - Whisper Seq2Seq Encoder-Decoder": "model3_whisper",
    "Model 1 - CNN + BiLSTM + CTC (Coming soon)": "model1_cnn_bilstm_ctc",
    "Model 2 - Simplified DeepSpeech (Coming soon)": "model2_deepspeech",
}

selected_label = st.selectbox("Chọn mô hình ASR", list(model_options.keys()))
selected_model = model_options[selected_label]

status_box = st.empty()

if st.button("Load Selected Model"):

    def update_status(message):
        status_box.info(message)

    try:
        with st.spinner("Đang load model..."):
            st.session_state.model_manager.load_model(
                selected_model,
                progress_callback=update_status,
            )

        st.session_state.loaded_model = selected_model
        status_box.success(f"{selected_label} đã được load thành công.")

    except Exception as e:
        status_box.error(str(e))

if st.session_state.loaded_model is not None:
    st.success(f"Model đang được load: {st.session_state.loaded_model}")
else:
    st.info("Chưa có model nào được load. Hãy chọn model và bấm Load Selected Model.")

st.divider()

input_mode = st.radio(
    "Chọn nguồn audio",
    ["Thu âm trực tiếp", "Upload file audio"],
    horizontal=True,
)

audio_path = None

if input_mode == "Thu âm trực tiếp":
    st.subheader("Thu âm từ microphone")

    audio = mic_recorder(
        start_prompt="Bắt đầu thu âm",
        stop_prompt="Dừng thu âm",
        just_once=False,
        use_container_width=True,
        format="wav",
    )

    if audio is not None:
        audio_bytes = audio["bytes"]
        audio_path = UPLOAD_DIR / "recorded_audio.wav"

        with open(audio_path, "wb") as f:
            f.write(audio_bytes)

        st.session_state.audio_path = str(audio_path)
        st.audio(audio_bytes, format="audio/wav")

elif input_mode == "Upload file audio":
    st.subheader("Upload file audio")

    uploaded_file = st.file_uploader(
        "Upload file audio tiếng Việt",
        type=["wav", "mp3", "m4a", "flac"],
    )

    if uploaded_file is not None:
        audio_path = UPLOAD_DIR / uploaded_file.name

        with open(audio_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.session_state.audio_path = str(audio_path)
        st.audio(str(audio_path))

st.divider()

if st.session_state.audio_path is not None:
    st.write(f"Audio hiện tại: `{st.session_state.audio_path}`")

    if st.button("Transcribe"):

        if st.session_state.loaded_model is None:
            st.warning("Hãy load model trước.")
        else:
            try:
                with st.spinner("Đang nhận dạng..."):
                    transcript = st.session_state.model_manager.transcribe(
                        st.session_state.audio_path
                    )

                st.subheader("Vietnamese Transcript")
                st.success(transcript)

            except Exception as e:
                st.error(str(e))
else:
    st.info("Hãy thu âm hoặc upload file audio trước.")