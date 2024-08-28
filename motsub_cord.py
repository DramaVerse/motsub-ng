import sys
import cv2
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QMessageBox
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
from PyQt5.QtCore import Qt, QTimer, QRect

MAX_WINDOW_HEIGHT = 600
CONTROLS_HEIGHT = 100  # Estimated height for slider and buttons

class VideoPlayer(QMainWindow):
    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.cap = cv2.VideoCapture(self.video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.current_frame = 0
        self.playing = False
        self.subtitle_rect = [0, 0, 0, 0]  # [x, y, w, h]
        self.selected_coordinates = None
        self.drawing = False

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Video Subtitle Region Selector')

        # Calculate the maximum video height to fit within the window
        max_video_height = MAX_WINDOW_HEIGHT - CONTROLS_HEIGHT
        scale_factor = min(max_video_height / self.video_height, 1)
        self.display_width = int(self.video_width * scale_factor)
        self.display_height = int(self.video_height * scale_factor)

        # Set window size
        self.setGeometry(100, 100, self.display_width, self.display_height + CONTROLS_HEIGHT)
        self.setFixedSize(self.display_width, self.display_height + CONTROLS_HEIGHT)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Video display
        self.video_label = QLabel()
        self.video_label.setFixedSize(self.display_width, self.display_height)
        self.video_label.setAlignment(Qt.AlignCenter)
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
            q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)

            # Scale pixmap to fit the label
            scaled_pixmap = pixmap.scaled(self.display_width, self.display_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Draw subtitle rectangle
            if self.subtitle_rect[2] > 0 and self.subtitle_rect[3] > 0:
                painter = QPainter(scaled_pixmap)
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                painter.drawRect(QRect(*self.subtitle_rect))
                painter.end()

            self.video_label.setPixmap(scaled_pixmap)
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
        if self.video_label.geometry().contains(event.pos()):
            self.drawing = True
            pos = self.video_label.mapFrom(self, event.pos())
            self.subtitle_rect[0] = pos.x()
            self.subtitle_rect[1] = pos.y()

    def mouseMoveEvent(self, event):
        if self.drawing and self.video_label.geometry().contains(event.pos()):
            pos = self.video_label.mapFrom(self, event.pos())
            self.subtitle_rect[2] = pos.x() - self.subtitle_rect[0]
            self.subtitle_rect[3] = pos.y() - self.subtitle_rect[1]
            self.update_frame()

    def mouseReleaseEvent(self, event):
        self.drawing = False

    def confirm_selection(self):
        if self.subtitle_rect[2] > 0 and self.subtitle_rect[3] > 0:
            scale_factor = self.video_width / self.display_width
            x1, y1, w, h = self.subtitle_rect
            x2, y2 = x1 + w, y1 + h
            x1, y1 = int(x1 * scale_factor), int(y1 * scale_factor)
            x2, y2 = int(x2 * scale_factor), int(y2 * scale_factor)
            self.selected_coordinates = f"{x1} {y1} {x2} {y2}"
            self.close()
        else:
            QMessageBox.warning(self, "Warning", "Please select a region before confirming.")

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