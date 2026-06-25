import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from backend.model_manager import ModelManager
from backend.services.translation import LANGUAGES, TranslationService

try:
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    mic_recorder = None

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

if "translation_service" not in st.session_state:
    st.session_state.translation_service = TranslationService()

if "loaded_model" not in st.session_state:
    st.session_state.loaded_model = None

if "audio_path" not in st.session_state:
    st.session_state.audio_path = None

if "transcript" not in st.session_state:
    st.session_state.transcript = None

if "translation" not in st.session_state:
    st.session_state.translation = None

if "translation_target_language" not in st.session_state:
    st.session_state.translation_target_language = None

model_options = {
    "Model 3 - Whisper Seq2Seq Encoder-Decoder": "model3_whisper",
    "Model 1 - CNN + BiLSTM + CTC (Coming soon)": "model1_cnn_bilstm_ctc",
    "Model 2 - Simplified DeepSpeech (Coming soon)": "model2_deepspeech",
}

selected_label = st.selectbox("Chọn mô hình ASR", list(model_options.keys()))
selected_model = model_options[selected_label]

translation_mode = st.selectbox(
    "Translation mode",
    ["Translate automatically", "Do not translate automatically"],
)
translation_enabled = translation_mode == "Translate automatically"

target_language_label = st.selectbox(
    "Target translation language",
    list(LANGUAGES.keys()),
)
target_language = LANGUAGES[target_language_label]

if st.session_state.translation_target_language != target_language:
    st.session_state.translation = None
    st.session_state.translation_target_language = target_language

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

    if mic_recorder is None:
        st.warning(
            "Microphone recording is unavailable because streamlit-mic-recorder "
            "is not installed. Use audio upload or install the project dependencies."
        )
        audio = None
    else:
        audio = mic_recorder(
            start_prompt="Báº¯t Ä‘áº§u thu Ã¢m",
            stop_prompt="Dá»«ng thu Ã¢m",
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
        st.session_state.transcript = None
        st.session_state.translation = None
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
        st.session_state.transcript = None
        st.session_state.translation = None
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

                st.session_state.transcript = transcript
                st.session_state.translation = None

                if translation_enabled and transcript.strip():
                    translation_status = st.empty()

                    def update_translation_status(message):
                        translation_status.info(message)

                    with st.spinner("Translating transcript..."):
                        st.session_state.translation_service.load(
                            progress_callback=update_translation_status,
                        )
                        st.session_state.translation = (
                            st.session_state.translation_service.translate(
                                transcript,
                                target_lang=target_language,
                            )
                        )

                    translation_status.success("Translation ready.")

            except Exception as e:
                st.error(str(e))

    if st.session_state.transcript:
        transcript_column, translation_column = st.columns(2)

        with transcript_column:
            st.subheader("Vietnamese Transcript")
            st.text_area(
                "Transcript",
                st.session_state.transcript,
                height=220,
                label_visibility="collapsed",
            )

        with translation_column:
            st.subheader(f"{target_language_label} Translation")

            if st.session_state.translation:
                st.text_area(
                    "Translation",
                    st.session_state.translation,
                    height=220,
                    label_visibility="collapsed",
                )
            else:
                st.info("No translation yet.")

            if st.button("Translate latest transcript"):
                try:
                    translation_status = st.empty()

                    def update_translation_status(message):
                        translation_status.info(message)

                    with st.spinner("Translating transcript..."):
                        st.session_state.translation_service.load(
                            progress_callback=update_translation_status,
                        )
                        st.session_state.translation = (
                            st.session_state.translation_service.translate(
                                st.session_state.transcript,
                                target_lang=target_language,
                            )
                        )
                    translation_status.success("Translation ready.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
else:
    st.info("Hãy thu âm hoặc upload file audio trước.")
