import cv2
import pyautogui
import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPainter, QBrush, QColor

class BlurOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(0, 0, pyautogui.size().width, pyautogui.size().height)
        self.is_blurred = False

    def paintEvent(self, event):
        if self.is_blurred:
            painter = QPainter(self)
            painter.setBrush(QBrush(QColor(0, 0, 0, 255))) # Solid Black Secure Screen
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())

    def show_blur(self):
        if not self.is_blurred:
            self.is_blurred = True
            self.show()
            self.raise_()
            self.update()

    def hide_blur(self):
        if self.is_blurred:
            self.is_blurred = False
            self.hide()

class ThirdEyeSystem:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.overlay = BlurOverlay()
        
        # Built-in XML models load kiye
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.snoop_cooldown_frames = 0
        self.cooldown_limit = 35  # Flicker rokne ke liye hold window

        self.timer = QTimer()
        self.timer.timeout.connect(self.process_frame)
        self.timer.start(16)

    def process_frame(self):
        success, frame = self.cap.read()
        if not success:
            return

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # BALANCED CONFIGURATION: minNeighbors ko 6 kiya taaki real face miss na ho
        detected_faces = self.face_cascade.detectMultiScale(gray, 1.15, 6, minSize=(80, 80))
        current_frame_snooper = False

        # Agar frame me 1 se zyada chehre hain (Aapke alawa koi aur hai)
        if len(detected_faces) > 1:
            # Sort kiya taaki camera ke sabse paas wala chehra (Index 0) AAP raho
            faces = sorted(detected_faces, key=lambda b: b[2] * b[3], reverse=True)
            
            # Piche wale snoopers par check lagao
            for (x, y, w, h) in faces[1:]:
                roi_gray = gray[y:y+h, x:x+w]
                
                # Optimized Eye Check: Piche wale bande ki kam se kam ek aankh camera ko dikhni chahiye
                eyes = self.eye_cascade.detectMultiScale(roi_gray, 1.1, 4, minSize=(18, 18))
                
                if len(eyes) >= 1:
                    current_frame_snooper = True
                    break

        # Purely screen manipulation (No screenshots, No webcam photos saved)
        if current_frame_snooper:
            self.snoop_cooldown_frames = self.cooldown_limit
            self.overlay.show_blur()
        else:
            if self.snoop_cooldown_frames > 0:
                self.snoop_cooldown_frames -= 1
                self.overlay.show_blur()
            else:
                self.overlay.hide_blur()

    def run(self):
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    system = ThirdEyeSystem()
    system.run()