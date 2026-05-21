from dataclasses import dataclass
import threading
import json

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout, QApplication

import cv2
import requests


@dataclass
class QRScannerConfig:
    base_url: str = "http://127.0.0.1:8080" # базовый URL сервера для отправки данных сканирования
    scan_path: str = "/api/v1/scan" # путь на сервере для отправки данных сканирования
    camera_index: int = 0 # индекс камеры (0 - обычно встроенная, 1 - внешняя)
    frame_interval_ms: int = 30 # частота обновления кадров
    api_key: str | None = None # ключ для авторизации на сервере
    close_after_result: bool = True  # автоматически закрывать окно


class QRPopup(QWidget):
    scanned = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, config: QRScannerConfig | None = None):
        super().__init__()
        self.cfg = config or QRScannerConfig()
        self.setWindowTitle("QR Scanner")
        self._label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self._label.setMinimumSize(320, 320)
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._read_frame)
        self._detector = cv2.QRCodeDetector()
        self._last = ""
        self._cap = None

        self.error.connect(lambda e: self._schedule_close() if self.cfg.close_after_result else None)

    def showEvent(self, event):
        super().showEvent(event)
        self.start()

    def closeEvent(self, event):
        self.stop()
        super().closeEvent(event)

    def start(self):
        if self._cap is not None:
            return
        cap = cv2.VideoCapture(self.cfg.camera_index)
        if not cap.isOpened():
            self.error.emit("Не удалось открыть камеру")
            return
        self._cap = cap
        self._timer.start(self.cfg.frame_interval_ms)

    def stop(self):
        if self._cap is None:
            return
        self._timer.stop()
        try:
            self._cap.release()
        finally:
            self._cap = None

    def _read_frame(self):
        if not self._cap:
            return
        ok, frame = self._cap.read()
        if not ok or frame is None:
            return

        h, w = frame.shape[:2]
        s = min(h, w)
        x0 = (w - s) // 2
        y0 = (h - s) // 2
        square = frame[y0 : y0 + s, x0 : x0 + s]

        rgb = cv2.cvtColor(square, cv2.COLOR_BGR2RGB)
        hh, ww = rgb.shape[:2]
        qimg = QImage(rgb.data, ww, hh, 3 * ww, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(self._label.size(),
                                             Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
        self._label.setPixmap(pix)

        data, _, _ = self._detector.detectAndDecode(square)
        if data and data != self._last:
            self._last = data
            self._post_async(data)

    def _post_async(self, qr_data: str):
        def worker():
            headers = {}
            if self.cfg.api_key:
                headers["Authorization"] = f"Bearer {self.cfg.api_key}"
            try:
                resp = requests.post(
                    f"{self.cfg.base_url.rstrip('/')}{self.cfg.scan_path}",
                    headers=headers,
                    json={"qr_data": qr_data},
                    timeout=8,
                    verify=True,
                )
            except Exception as e:
                self.error.emit(f"Ошибка запроса: {e}")
                return

            if resp.status_code != 200:
                self.error.emit(f"Сервер вернул {resp.status_code}: {resp.text}")
                return

            try:
                payload = resp.json()
            except json.JSONDecodeError:
                payload = resp.text or ""
            self.scanned.emit(payload)
            if self.cfg.close_after_result:
                self._schedule_close()
            self.stop()

        threading.Thread(target=worker, daemon=True).start()

    def _schedule_close(self):
        QTimer.singleShot(0, self.close)
