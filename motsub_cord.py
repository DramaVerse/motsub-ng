import sys
import cv2
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QMessageBox
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
from PyQt5.QtCore import Qt, QTimer


class VideoPlayer(QMainWindow):
    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.cap = cv2.VideoCapture(self.video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        self.current_frame = 0
        self.playing = False
        self.subtitle_rect = [0, 0, 0, 0]  # [x, y, w, h]
        self.selected_coordinates = None

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Video Subtitle Region Selector')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Video display
        self.video_label = QLabel()
        layout.addWidget(self.video_label)

        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, self.total_frames - 1)
        self.slider.valueChanged.connect(self.slider_value_changed)
        layout.addWidget(self.slider)

        # Controls
        controls_layout = QHBoxLayout()
        self.play_button = QPushButton('Play/Pause')
        self.play_button.clicked.connect(self.toggle_play)
        controls_layout.addWidget(self.play_button)

        self.confirm_button = QPushButton('Confirm Selection')
        self.confirm_button.clicked.connect(self.confirm_selection)
        controls_layout.addWidget(self.confirm_button)

        layout.addLayout(controls_layout)

        central_widget.setLayout(layout)

        # Timer for video playback
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        self.show()
        self.update_frame()

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_image = QImage(frame.data, w, h, bytes_per_line,
                             QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)

            # Draw subtitle rectangle
            if self.subtitle_rect[2] > 0 and self.subtitle_rect[3] > 0:
                painter = QPainter(pixmap)
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                painter.drawRect(*self.subtitle_rect)
                painter.end()

            self.video_label.setPixmap(pixmap)
            self.current_frame += 1
            self.slider.blockSignals(True)
            self.slider.setValue(self.current_frame)
            self.slider.blockSignals(False)

            if self.current_frame >= self.total_frames:
                self.current_frame = 0
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        else:
            self.timer.stop()
            self.playing = False

    def slider_value_changed(self, value):
        if value != self.current_frame:
            self.current_frame = value
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, value)
            self.update_frame()

    def toggle_play(self):
        if self.playing:
            self.timer.stop()
        else:
            self.timer.start(int(1000 / self.fps))
        self.playing = not self.playing

    def mousePressEvent(self, event):
        self.subtitle_rect[0] = event.x() - self.video_label.x()
        self.subtitle_rect[1] = event.y() - self.video_label.y()

    def mouseMoveEvent(self, event):
        self.subtitle_rect[2] = event.x(
        ) - self.video_label.x() - self.subtitle_rect[0]
        self.subtitle_rect[3] = event.y(
        ) - self.video_label.y() - self.subtitle_rect[1]
        self.update_frame()

    def confirm_selection(self):
        x1, y1, w, h = self.subtitle_rect
        x2, y2 = x1 + w, y1 + h
        self.selected_coordinates = f"{x1} {y1} {x2} {y2}"
        self.close()


def get_subtitle_coordinates(video_path):
    app = QApplication(sys.argv)
    player = VideoPlayer(video_path)
    app.exec_()
    return player.selected_coordinates


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 motsub_cord.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    coordinates = get_subtitle_coordinates(video_path)
    print(f"Selected coordinates: {coordinates}")
