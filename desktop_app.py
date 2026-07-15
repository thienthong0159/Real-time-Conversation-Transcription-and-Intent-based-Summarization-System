"""Native Qt desktop application for Vietnamese realtime transcription."""

from __future__ import annotations

import queue
import sys
from pathlib import Path

import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QSlider,
    QSpinBox, QSplitter, QStatusBar, QTabWidget, QTextEdit, QVBoxLayout,
    QWidget,
)

from asr.audio import TARGET_SAMPLE_RATE, load_audio_mono
from asr.common import TranscriptionResult
from asr.transformers_backend import resolve_device
from pipeline import BACKENDS, TranscriptionConfig, run_transcription


def default_model_path(backend: str) -> str:
    return (
        "checkpoints/cascaded_phowhisper_ckpt"
        if backend == "Cascaded PhoWhisper"
        else "checkpoints/phowhisper-base-ct2"
    )


def transcript_text(result: TranscriptionResult) -> str:
    lines = [f"[{item.start:.2f} - {item.end:.2f}]\n{item.text}" for item in result.segments]
    if result.partial:
        lines.extend(("", "[Partial transcript]", result.partial))
    return "\n\n".join(lines)


class FileTranscriptionWorker(QThread):
    completed = Signal(object, object)
    failed = Signal(str)

    def __init__(self, path: str, config: TranscriptionConfig) -> None:
        super().__init__()
        self.path = path
        self.config = config

    def run(self) -> None:
        try:
            samples = load_audio_mono(self.path)
            metrics = run_transcription(self.path, self.config, len(samples) / TARGET_SAMPLE_RATE)
            self.completed.emit(metrics.result, metrics)
        except Exception as error:
            self.failed.emit(str(error))


class LiveTranscriptionWorker(QThread):
    updated = Signal(object)
    status = Signal(str)
    failed = Signal(str)
    finished_stream = Signal(object)

    def __init__(self, config: TranscriptionConfig, chunk_seconds: float) -> None:
        super().__init__()
        self.config = config
        self.chunk_seconds = chunk_seconds
        self._stop_requested = False

    def stop(self) -> None:
        self._stop_requested = True

    def run(self) -> None:
        try:
            import sounddevice as sd
            from asr.whisper_streaming_backend import WhisperStreamingSession

            frames: queue.Queue[tuple[int, np.ndarray]] = queue.Queue(maxsize=512)
            stream: sd.InputStream | None = None

            def capture(indata: np.ndarray, _frames: int, _time, _status) -> None:
                if stream is None:
                    return
                item = (int(stream.samplerate), indata.copy())
                try:
                    frames.put_nowait(item)
                except queue.Full:
                    try:
                        frames.get_nowait()  # Keep fresh speech rather than stale audio.
                        frames.put_nowait(item)
                    except queue.Empty:
                        pass

            self.status.emit("Loading Whisper Streaming model…")
            session = WhisperStreamingSession(
                self.config.model_path, self.config.device, self.config.compute_type,
                self.config.beam_size, self.config.enable_vad, self.chunk_seconds,
            )
            self.status.emit("Listening to microphone…")
            with sd.InputStream(channels=1, dtype="float32", callback=capture) as stream:
                while not self._stop_requested:
                    try:
                        sample_rate, samples = frames.get(timeout=0.25)
                    except queue.Empty:
                        continue
                    chunks = [samples]
                    while True:
                        try:
                            queued_rate, queued_samples = frames.get_nowait()
                        except queue.Empty:
                            break
                        if queued_rate == sample_rate:
                            chunks.append(queued_samples)
                    result = session.push_audio((sample_rate, np.concatenate(chunks, axis=0)))
                    self.updated.emit(result)
            self.finished_stream.emit(session.finish())
        except Exception as error:
            self.failed.emit(str(error))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.worker: QThread | None = None
        self.audio_path = ""
        self.setWindowTitle("Realtime Transcription")
        self.resize(1180, 760)
        self._build_ui()
        self._on_backend_changed()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(14, 14, 14, 14)

        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar.setFixedWidth(300)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.addWidget(QLabel("<h2>Configuration</h2>"))
        form = QFormLayout()
        self.backend = QComboBox()
        self.backend.addItems(BACKENDS)
        self.backend.currentTextChanged.connect(self._on_backend_changed)
        self.device = QComboBox()
        self.device.addItems(("auto", "cuda", "cpu"))
        self.compute_type = QComboBox()
        self.compute_type.addItems(("auto", "float16", "int8"))
        self.beam_size = QSpinBox()
        self.beam_size.setRange(1, 10)
        self.beam_size.setValue(5)
        self.vad = QCheckBox("Enable VAD")
        self.vad.setChecked(True)
        self.model_path = QTextEdit()
        self.model_path.setFixedHeight(55)
        self.live_interval = QSlider()
        self.live_interval.setRange(5, 20)
        self.live_interval.setValue(10)
        self.live_interval.setTickInterval(5)
        self.live_interval.valueChanged.connect(self._update_interval_label)
        self.interval_label = QLabel()
        form.addRow("Backend", self.backend)
        form.addRow("Device", self.device)
        form.addRow("Compute type", self.compute_type)
        form.addRow("Beam size", self.beam_size)
        form.addRow(self.vad)
        form.addRow("Model path", self.model_path)
        form.addRow("Live interval", self.live_interval)
        form.addRow("", self.interval_label)
        sidebar_layout.addLayout(form)
        sidebar_layout.addStretch()
        layout.addWidget(sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(QLabel("<h1>Realtime Transcription</h1>"))
        self.tabs = QTabWidget()
        self.file_tab = QWidget()
        file_layout = QVBoxLayout(self.file_tab)
        row = QHBoxLayout()
        self.file_label = QLabel("Choose an audio file (wav, mp3, m4a, flac, ogg).")
        self.file_label.setWordWrap(True)
        browse = QPushButton("Choose audio file")
        browse.clicked.connect(self._choose_file)
        self.file_start = QPushButton("Start transcription")
        self.file_start.clicked.connect(self._start_file)
        row.addWidget(browse)
        row.addWidget(self.file_start)
        file_layout.addWidget(self.file_label)
        file_layout.addLayout(row)
        file_layout.addStretch()
        self.live_tab = QWidget()
        live_layout = QVBoxLayout(self.live_tab)
        live_layout.addWidget(QLabel("Use your default microphone for realtime Vietnamese transcription."))
        self.live_start = QPushButton("Start live microphone")
        self.live_start.clicked.connect(self._toggle_live)
        live_layout.addWidget(self.live_start)
        live_layout.addStretch()
        self.tabs.addTab(self.file_tab, "Audio file")
        self.tabs.addTab(self.live_tab, "Live microphone")
        content_layout.addWidget(self.tabs)
        content_layout.addWidget(QLabel("<h2>Transcript</h2>"))
        self.transcript = QTextEdit(readOnly=True)
        self.transcript.setPlaceholderText("Confirmed transcript segments will appear here.")
        content_layout.addWidget(self.transcript, stretch=1)
        layout.addWidget(content, stretch=1)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

    def _update_interval_label(self, _value: int | None = None) -> None:
        self.interval_label.setText(f"{self.live_interval.value() / 10:.1f} seconds")

    def _on_backend_changed(self) -> None:
        backend = self.backend.currentText()
        self.model_path.setPlainText(default_model_path(backend))
        cascaded = backend == "Cascaded PhoWhisper"
        self.compute_type.setEnabled(not cascaded)
        self.tabs.setTabEnabled(1, backend == "Whisper Streaming")
        if cascaded and self.tabs.currentIndex() == 1:
            self.tabs.setCurrentIndex(0)
        self._update_interval_label()

    def _config(self) -> TranscriptionConfig:
        return TranscriptionConfig(
            self.backend.currentText(), self.model_path.toPlainText().strip(),
            self.device.currentText(), self.beam_size.value(),
            self.compute_type.currentText(), self.vad.isChecked(),
        )

    def _choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose audio", "", "Audio files (*.wav *.mp3 *.m4a *.flac *.ogg)",
        )
        if path:
            self.audio_path = path
            self.file_label.setText(path)

    def _check_model_path(self, config: TranscriptionConfig) -> bool:
        if Path(config.model_path).exists():
            return True
        QMessageBox.warning(self, "Missing checkpoint", f"Model checkpoint not found:\n{config.model_path}")
        return False

    def _start_file(self) -> None:
        if not self.audio_path:
            QMessageBox.information(self, "Choose audio", "Choose an audio file first.")
            return
        config = self._config()
        if not self._check_model_path(config):
            return
        self.transcript.clear()
        self.file_start.setEnabled(False)
        self.statusBar().showMessage("Transcribing audio…")
        self.worker = FileTranscriptionWorker(self.audio_path, config)
        self.worker.completed.connect(self._file_completed)
        self.worker.failed.connect(self._worker_failed)
        self.worker.start()

    def _file_completed(self, result: TranscriptionResult, metrics) -> None:
        self.transcript.setPlainText(transcript_text(result))
        self.file_start.setEnabled(True)
        self.statusBar().showMessage(
            f"Completed: {len(result.segments)} segments | {metrics.inference_seconds:.2f}s | {metrics.processing_speed:.2f}× realtime"
        )

    def _toggle_live(self) -> None:
        if isinstance(self.worker, LiveTranscriptionWorker) and self.worker.isRunning():
            self.statusBar().showMessage("Stopping live microphone stream…")
            self.worker.stop()
            self.live_start.setEnabled(False)
            return
        config = self._config()
        if not self._check_model_path(config):
            return
        self.transcript.clear()
        self.live_start.setText("Stop live microphone")
        self.statusBar().showMessage("Starting live microphone stream…")
        self.worker = LiveTranscriptionWorker(config, self.live_interval.value() / 10)
        self.worker.updated.connect(self._live_updated)
        self.worker.status.connect(self.statusBar().showMessage)
        self.worker.failed.connect(self._worker_failed)
        self.worker.finished_stream.connect(self._live_finished)
        self.worker.start()

    def _live_updated(self, result: TranscriptionResult) -> None:
        self.transcript.setPlainText(transcript_text(result))
        self.transcript.verticalScrollBar().setValue(self.transcript.verticalScrollBar().maximum())

    def _live_finished(self, result: TranscriptionResult) -> None:
        self._live_updated(result)
        self.live_start.setText("Start live microphone")
        self.live_start.setEnabled(True)
        self.statusBar().showMessage("Live microphone stream stopped")

    def _worker_failed(self, error: str) -> None:
        self.file_start.setEnabled(True)
        self.live_start.setText("Start live microphone")
        self.live_start.setEnabled(True)
        self.statusBar().showMessage("Transcription failed")
        QMessageBox.critical(self, "Transcription error", error)

    def closeEvent(self, event) -> None:
        if isinstance(self.worker, LiveTranscriptionWorker) and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)
        event.accept()


def main() -> int:
    application = QApplication(sys.argv)
    application.setApplicationName("Realtime Transcription")
    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
