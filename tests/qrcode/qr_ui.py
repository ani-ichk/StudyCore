import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    OPENCV_AVAILABLE = False

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from server.data.db.qr_service import QRCodeService


class QRCodeApp(QWidget):
    """SПростой пользовательский интерфейс на PyQt6 для генерации и сканирования QR-кодов."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генератор/сканер QR-кодов")
        self.setMinimumSize(860, 520)

        self._last_qr_bytes = None
        self._camera_timer = None
        self._camera_cap = None
        self._qr_detector = None

        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)

        layout.addWidget(self._build_generator_group(), 1)
        layout.addWidget(self._build_scanner_group(), 1)

        self.setLayout(layout)

    def _build_generator_group(self) -> QGroupBox:
        group = QGroupBox("Сгенерировать QR-код")
        v = QVBoxLayout(group)

        form_layout = QHBoxLayout()

        self.user_id_input = QLineEdit()
        self.user_id_input.setPlaceholderText("ID пользователя")
        self.user_id_input.setFixedWidth(100)

        self.purpose_input = QLineEdit()
        self.purpose_input.setPlaceholderText("Назначение (посещение, библиотека, еда)")
        self.purpose_input.setText("посещение")

        self.generate_btn = QPushButton("Генерировать")
        self.generate_btn.clicked.connect(self._on_generate)

        form_layout.addWidget(QLabel("ID пользователя:"))
        form_layout.addWidget(self.user_id_input)
        form_layout.addWidget(QLabel("Цель:"))
        form_layout.addWidget(self.purpose_input)
        form_layout.addWidget(self.generate_btn)

        v.addLayout(form_layout)

        self.qr_image_label = QLabel()
        self.qr_image_label.setMinimumSize(320, 320)
        self.qr_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_image_label.setStyleSheet("border: 1px solid #ccc; background: #fff;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.qr_image_label)
        scroll.setMinimumHeight(340)
        v.addWidget(scroll)

        self.generated_info = QLabel("")
        self.generated_info.setWordWrap(True)
        v.addWidget(self.generated_info)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить PNG")
        self.save_btn.clicked.connect(self._on_save_png)
        self.save_btn.setEnabled(False)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.save_btn)
        v.addLayout(btn_layout)

        return group

    def _build_scanner_group(self) -> QGroupBox:
        group = QGroupBox("Сканировать QR-код")
        v = QVBoxLayout(group)

        btn_layout = QHBoxLayout()
        self.open_btn = QPushButton("Открыть изображение...")
        self.open_btn.clicked.connect(self._on_open_image)
        btn_layout.addWidget(self.open_btn)

        self.camera_btn = QPushButton("Запустить камеру")
        self.camera_btn.clicked.connect(self._on_start_camera)
        btn_layout.addWidget(self.camera_btn)

        self.stop_camera_btn = QPushButton("Остановить камеру")
        self.stop_camera_btn.clicked.connect(self._on_stop_camera)
        self.stop_camera_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_camera_btn)

        btn_layout.addStretch(1)
        v.addLayout(btn_layout)

        self.scan_image_label = QLabel()
        self.scan_image_label.setMinimumSize(320, 320)
        self.scan_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scan_image_label.setStyleSheet("border: 1px solid #ccc; background: #fff;")

        scan_scroll = QScrollArea()
        scan_scroll.setWidgetResizable(True)
        scan_scroll.setWidget(self.scan_image_label)
        scan_scroll.setMinimumHeight(340)
        v.addWidget(scan_scroll)

        self.scan_result = QLabel("")
        self.scan_result.setWordWrap(True)
        v.addWidget(self.scan_result)

        return group

    def _on_generate(self):
        user_id_text = self.user_id_input.text().strip()
        if not user_id_text.isdigit():
            QMessageBox.warning(self, "Validation", "ID пользователя должен быть числом.")
            return

        user_id = int(user_id_text)
        purpose = self.purpose_input.text().strip() or "посещение"

        qr_data = QRCodeService.generate_qr_data(user_id, purpose)
        qr_bytes = QRCodeService.generate_qr_code_image(qr_data).getvalue()
        self._last_qr_bytes = qr_bytes

        pixmap = QPixmap()
        pixmap.loadFromData(qr_bytes, "PNG")
        self.qr_image_label.setPixmap(pixmap.scaled(self.qr_image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        self.generated_info.setText(
            f"QR Data: {qr_data}\n" +
            f"Purpose: {purpose}\n" +
            f"User ID: {user_id}\n" +
            "(Вы можете сохранить изображение и затем отсканировать его с помощью вкладки сканера.)"
        )
        self.save_btn.setEnabled(True)

    def _on_save_png(self):
        if not self._last_qr_bytes:
            return

        path, _ = QFileDialog.getSaveFileName(self, "Сохранить QR-код", "qrcode.png", "PNG Files (*.png)")
        if not path:
            return

        try:
            Path(path).write_bytes(self._last_qr_bytes)
            QMessageBox.information(self, "Saved", f"Сохранен QR-код в {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Не удалось сохранить файл: {e}")

    def _on_open_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть изображение", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not path:
            return

        pixmap = QPixmap(path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Error", "Не удалось загрузить изображение")
            return

        self.scan_image_label.setPixmap(pixmap.scaled(self.scan_image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        try:
            decoded = QRCodeService.decode_qr_from_image_path(path)
        except ImportError as e:
            self.scan_result.setText(str(e))
            return

        if not decoded:
            self.scan_result.setText("QR-код не распознан или изображение не содержит QR-кода.")
            return

        valid, data = QRCodeService.validate_qr_code(decoded)
        if valid:
            self.scan_result.setText(
                "<b>QR-код валиден</b><br>" +
                "<br>".join(f"{k}: {v}" for k, v in data.items())
            )
        else:
            self.scan_result.setText(f"<b>Ошибка:</b> {data.get('error')}")

    def _on_start_camera(self):
        if not OPENCV_AVAILABLE:
            QMessageBox.warning(self, "Camera", "OpenCV не установлен — нельзя использовать камеру.")
            return

        if self._camera_cap is not None:
            return

        self._camera_cap = cv2.VideoCapture(0)
        if not self._camera_cap.isOpened():
            QMessageBox.warning(self, "Camera", "Не удалось открыть камеру")
            self._camera_cap = None
            return

        self._qr_detector = cv2.QRCodeDetector()
        self._camera_timer = QTimer(self)
        self._camera_timer.timeout.connect(self._camera_frame)
        self._camera_timer.start(30)

        self.camera_btn.setEnabled(False)
        self.stop_camera_btn.setEnabled(True)

    def _on_stop_camera(self):
        if self._camera_timer:
            self._camera_timer.stop()
            self._camera_timer = None

        if self._camera_cap:
            self._camera_cap.release()
            self._camera_cap = None

        self.camera_btn.setEnabled(True)
        self.stop_camera_btn.setEnabled(False)

    def _camera_frame(self):
        if not self._camera_cap:
            return

        ret, frame = self._camera_cap.read()
        if not ret:
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.scan_image_label.setPixmap(
            pixmap.scaled(
                self.scan_image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

        data, points, _ = self._qr_detector.detectAndDecode(frame)
        if data:
            valid, parsed = QRCodeService.validate_qr_code(data)
            if valid:
                self.scan_result.setText(
                    "<b>QR-код валиден</b><br>" +
                    "<br>".join(f"{k}: {v}" for k, v in parsed.items())
                )
            else:
                self.scan_result.setText(f"<b>Ошибка:</b> {parsed.get('error')}")
            self._on_stop_camera()

    def closeEvent(self, event):
        self._on_stop_camera()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = QRCodeApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()