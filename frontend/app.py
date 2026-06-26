from concurrent.futures import ThreadPoolExecutor
import os
import sys
import tempfile
import time
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

try:
    import numpy as np
    import soundfile as sf
    from streamlit_webrtc import WebRtcMode, webrtc_streamer
except ImportError:
    np = None
    sf = None
    WebRtcMode = None
    webrtc_streamer = None

import warnings

warnings.filterwarnings("ignore", category=UserWarning)

UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def audio_frames_to_wav(frames):
    arrays = []
    sample_rate = None

    for frame in frames:
        array = frame.to_ndarray()
        if array.ndim == 2:
            array = array.mean(axis=0)
        arrays.append(array.astype("float32"))
        sample_rate = frame.sample_rate

    if not arrays or sample_rate is None:
        return None

    audio = np.concatenate(arrays)
    max_value = np.max(np.abs(audio)) if audio.size else 0
    if max_value > 1:
        audio = audio / max_value

    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_path = Path(temp_file.name)
    temp_file.close()
    sf.write(temp_path, audio, sample_rate)
    return temp_path


def transcribe_and_translate_chunk(audio_path, target_language, translation_enabled):
    transcript = st.session_state.model_manager.transcribe(str(audio_path))
    translation = ""

    if translation_enabled and transcript.strip():
        st.session_state.translation_service.load()
        translation = st.session_state.translation_service.translate(
            transcript,
            target_lang=target_language,
        )

    return transcript, translation

st.set_page_config(
    page_title="Conversation Transcription",
    page_icon="🎙️",
    layout="wide",
)

st.title("🎙️ Conversation Transcription Demo")
st.caption("Giai đoạn 1: Thu âm hoặc upload audio, sau đó nhận dạng bằng Whisper")

if sys.version_info[:2] != (3, 12):
    st.warning(
        "This project is configured for Python 3.12. "
        f"You are running Python {sys.version_info.major}.{sys.version_info.minor}. "
        "Create a Python 3.12 virtual environment before loading speech models."
    )

with st.sidebar:
    st.subheader("Hugging Face")
    hf_token = st.text_input(
        "HF token",
        value=os.getenv("HF_TOKEN", ""),
        type="password",
        help="Used only for this running app session when downloading models.",
    )

    if hf_token:
        os.environ["HF_TOKEN"] = hf_token.strip()
        st.success("HF token is set for this session.")
    else:
        os.environ.pop("HF_TOKEN", None)
        st.info("Paste a token if model downloads require authentication.")

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

if "translation_model_loaded" not in st.session_state:
    st.session_state.translation_model_loaded = False

if "realtime_transcript" not in st.session_state:
    st.session_state.realtime_transcript = ""

if "realtime_translation" not in st.session_state:
    st.session_state.realtime_translation = ""

if "realtime_running" not in st.session_state:
    st.session_state.realtime_running = False

if "realtime_pending_translation" not in st.session_state:
    st.session_state.realtime_pending_translation = ""

if "realtime_last_translation_at" not in st.session_state:
    st.session_state.realtime_last_translation_at = time.time()

model_options = {
    "Model 3 - Whisper Seq2Seq Encoder-Decoder": "model3_whisper",
    "Model 1 - CNN + BiLSTM + CTC": "model1_cnn_bilstm_ctc",
    "Model 2 - Simplified DeepSpeech": "model2_deepspeech",
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

translator_available_locally = (
    st.session_state.translation_service.local_model_exists()
)

if translation_enabled:
    if translator_available_locally:
        st.info("Translator checkpoint found locally.")
    else:
        st.warning(
            "Translator checkpoint was not found locally. It will be downloaded "
            "automatically when you click Load Selected Model."
        )

status_box = st.empty()

if st.button("Load Selected Model"):
    try:
        if translation_enabled:
            if translator_available_locally:
                load_message = "Loading speech-to-text and local translation models..."
            else:
                load_message = (
                    "Loading speech-to-text model and downloading translation model..."
                )

            status_box.info(load_message)
            with st.spinner(load_message):
                with ThreadPoolExecutor(max_workers=2) as executor:
                    asr_future = executor.submit(
                        st.session_state.model_manager.load_model,
                        selected_model,
                    )
                    translation_future = executor.submit(
                        st.session_state.translation_service.load,
                    )

                    asr_future.result()
                    translation_future.result()

            st.session_state.translation_model_loaded = True
            status_box.success(
                f"{selected_label} and translator model are ready."
            )
        else:
            status_box.info("Loading speech-to-text model...")
            with st.spinner("Loading speech-to-text model..."):
                st.session_state.model_manager.load_model(selected_model)

            status_box.success(f"{selected_label} loaded successfully.")

        st.session_state.loaded_model = selected_model

    except Exception as e:
        status_box.error(str(e))

if st.session_state.loaded_model is not None:
    st.success(f"Model đang được load: {st.session_state.loaded_model}")
else:
    st.info("Chưa có model nào được load. Hãy chọn model và bấm Load Selected Model.")

if st.session_state.translation_model_loaded:
    st.success("Translation model is loaded.")

st.divider()

st.subheader("Real-time microphone transcription")

realtime_mode = st.selectbox(
    "Realtime microphone mode",
    ["Off", "On"],
)

if realtime_mode == "Off":
    st.info("Realtime microphone streaming is off.")
elif webrtc_streamer is None or WebRtcMode is None or np is None or sf is None:
    st.warning(
        "Real-time microphone mode requires streamlit-webrtc, numpy, and soundfile. "
        "Install the project dependencies, then restart Streamlit."
    )
else:
    realtime_chunk_seconds = int(
        st.selectbox(
            "Realtime chunk length",
            ["1", "2", "3", "5", "8", "10"],
            index=1,
        )
    )
    realtime_translation_seconds = int(
        st.selectbox(
            "Realtime translation interval",
            ["3", "4", "5", "8", "10"],
            index=1,
        )
    )

    realtime_ctx = webrtc_streamer(
        key="realtime-transcription",
        mode=WebRtcMode.SENDONLY,
        media_stream_constraints={"audio": True, "video": False},
        audio_receiver_size=4096,
        async_processing=True,
    )

    realtime_controls = st.columns(3)
    start_realtime = realtime_controls[0].button("Start live transcription")
    stop_realtime = realtime_controls[1].button("Stop live transcription")
    clear_realtime = realtime_controls[2].button("Clear live text")

    if start_realtime:
        st.session_state.realtime_running = True
        st.session_state.realtime_last_translation_at = time.time()

    if stop_realtime:
        st.session_state.realtime_running = False

    if clear_realtime:
        st.session_state.realtime_transcript = ""
        st.session_state.realtime_translation = ""
        st.session_state.realtime_pending_translation = ""
        st.rerun()

    realtime_status = st.empty()
    realtime_transcript_column, realtime_translation_column = st.columns(2)
    realtime_transcript_column.markdown("**Live Vietnamese Transcript**")
    realtime_translation_column.markdown(f"**Live {target_language_label} Translation**")
    realtime_transcript_placeholder = realtime_transcript_column.empty()
    realtime_translation_placeholder = realtime_translation_column.empty()

    def render_realtime_text():
        realtime_transcript_placeholder.code(
            st.session_state.realtime_transcript or " ",
            language=None,
        )
        realtime_translation_placeholder.code(
            st.session_state.realtime_translation or " ",
            language=None,
        )

    render_realtime_text()

    if st.session_state.realtime_running:
        if st.session_state.loaded_model is None:
            realtime_status.warning("Load the speech-to-text model first.")
            st.session_state.realtime_running = False
        elif realtime_ctx.audio_receiver is None:
            realtime_status.warning("Start the microphone stream first.")
            st.session_state.realtime_running = False
        elif not realtime_ctx.state.playing:
            realtime_status.warning("Microphone stream is stopped.")
            st.session_state.realtime_running = False
        else:
            realtime_status.info(
                "Listening continuously. Click Stop live transcription to end."
            )
            frames = []
            started_at = time.time()

            while time.time() - started_at < realtime_chunk_seconds:
                if not realtime_ctx.state.playing:
                    st.session_state.realtime_running = False
                    break
                try:
                    frames.extend(
                        realtime_ctx.audio_receiver.get_frames(timeout=1)
                    )
                except Exception:
                    pass

            if frames:
                temp_audio_path = audio_frames_to_wav(frames)

                if temp_audio_path is not None:
                    try:
                        chunk_transcript = st.session_state.model_manager.transcribe(
                            str(temp_audio_path)
                        )
                        chunk_translation = ""

                        if chunk_transcript:
                            st.session_state.realtime_transcript = (
                                f"{st.session_state.realtime_transcript} "
                                f"{chunk_transcript}"
                            ).strip()
                            st.session_state.realtime_pending_translation = (
                                f"{st.session_state.realtime_pending_translation} "
                                f"{chunk_transcript}"
                            ).strip()

                        should_translate = (
                            translation_enabled
                            and st.session_state.realtime_pending_translation
                            and time.time() - st.session_state.realtime_last_translation_at
                            >= realtime_translation_seconds
                        )

                        if should_translate:
                            st.session_state.translation_service.load()
                            chunk_translation = st.session_state.translation_service.translate(
                                st.session_state.realtime_pending_translation,
                                target_lang=target_language,
                            )
                            st.session_state.realtime_pending_translation = ""
                            st.session_state.realtime_last_translation_at = time.time()

                            if chunk_translation:
                                st.session_state.realtime_translation = (
                                    f"{st.session_state.realtime_translation} "
                                    f"{chunk_translation}"
                                ).strip()

                        render_realtime_text()
                        realtime_status.success(
                            f"Updated at {time.strftime('%H:%M:%S')}"
                        )
                    except Exception as e:
                        realtime_status.error(str(e))
                        st.session_state.realtime_running = False
                    finally:
                        temp_audio_path.unlink(missing_ok=True)

            if st.session_state.realtime_running:
                st.rerun()
    else:
        realtime_status.info("Live transcription is stopped.")

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
            start_prompt="Start Recording",
            stop_prompt="Stop Recording",
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
