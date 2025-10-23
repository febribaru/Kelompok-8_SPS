import sys
import requests
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFormLayout, QWidget, QVBoxLayout,
    QLineEdit, QPushButton, QLabel, QComboBox, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class SignalGeneratorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Signal Generator - Real-Time Oscilloscope")
        self.setGeometry(100, 100, 1000, 700)

        # === State ===
        self.is_running = False
        self.current_signal = "x1"
        self.t_end = 2.0
        self.t_duration = 2.0  # Lebar jendela waktu

        # === UI Setup ===
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # --- Input Form ---
        form_layout = QFormLayout()

        self.a1_input = QLineEdit("1.0"); form_layout.addRow("A1 (x1):", self.a1_input)
        self.a2_input = QLineEdit("0.5"); form_layout.addRow("A2 (x2):", self.a2_input)
        self.f1_input = QLineEdit("1.0"); form_layout.addRow("f1 (Hz):", self.f1_input)
        self.f2_input = QLineEdit("2.0"); form_layout.addRow("f2 (Hz):", self.f2_input)
        self.phi1_input = QLineEdit("0.0"); form_layout.addRow("φ1 (rad):", self.phi1_input)
        self.phi2_input = QLineEdit("0.0"); form_layout.addRow("φ2 (rad):", self.phi2_input)
        self.samples_input = QLineEdit("200"); form_layout.addRow("Samples:", self.samples_input)

        layout.addLayout(form_layout)

        # --- Control Panel ---
        control_layout = QHBoxLayout()

        # Dropdown sinyal
        self.signal_combo = QComboBox()
        self.signal_combo.addItems([
            "x1(t)", "x2(t)",
            "y1(t) = x1 + x2",
            "y2(t) = x1 - x2",
            "y3(t) = x1 × x2"
        ])
        self.signal_combo.currentTextChanged.connect(self.on_signal_change)
        control_layout.addWidget(QLabel("Tampilkan:"))
        control_layout.addWidget(self.signal_combo)

        # Start/Stop Button
        self.start_button = QPushButton("Start Real-Time")
        self.start_button.clicked.connect(self.toggle_realtime)
        control_layout.addWidget(self.start_button)

        # Reset Waktu
        reset_button = QPushButton("Reset Waktu")
        reset_button.clicked.connect(self.reset_time)
        control_layout.addWidget(reset_button)

        layout.addLayout(control_layout)

        # --- Status ---
        self.status_label = QLabel("Status: Stopped")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.status_label)

        # --- Plot Canvas ---
        self.figure = Figure(figsize=(10, 5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # --- Timer (Update 10x per detik → SUPER SMOOTH) ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.setInterval(100)  # 100ms = 10 FPS

    # ==============================
    # EVENT HANDLERS
    # ==============================

    def on_signal_change(self, text):
        mapping = {
            "x1(t)": "x1",
            "x2(t)": "x2",
            "y1(t) = x1 + x2": "y1",
            "y2(t) = x1 - x2": "y2",
            "y3(t) = x1 × x2": "y3"
        }
        self.current_signal = mapping.get(text, "x1")
        if self.is_running:
            self.update_plot()

    def toggle_realtime(self):
        if not self.is_running:
            self.is_running = True
            self.start_button.setText("Stop")
            self.status_label.setText("Status: Running (Real-Time)")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.timer.start()
            self.update_plot()
        else:
            self.is_running = False
            self.start_button.setText("Start Real-Time")
            self.status_label.setText("Status: Stopped")
            self.status_label.setStyleSheet("color: gray; font-style: italic;")
            self.timer.stop()

    def reset_time(self):
        self.t_end = self.t_duration
        self.status_label.setText("Waktu direset!")
        if self.is_running:
            self.update_plot()

    # ==============================
    # CORE LOGIC
    # ==============================

    def get_params(self):
        try:
            return {
                "a1": float(self.a1_input.text()),
                "a2": float(self.a2_input.text()),
                "f1": float(self.f1_input.text()),
                "f2": float(self.f2_input.text()),
                "phi1": float(self.phi1_input.text()),
                "phi2": float(self.phi2_input.text()),
                "t_start": max(0.0, self.t_end - self.t_duration),
                "t_end": self.t_end,
                "samples": max(50, int(self.samples_input.text()))
            }
        except ValueError as e:
            QMessageBox.critical(self, "Input Error", f"Nilai tidak valid: {e}")
            return None

    def update_plot(self):
        params = self.get_params()
        if not params:
            return

        try:
            response = requests.post(
                "http://127.0.0.1:8080/generate",
                json=params,
                timeout=1.0
            )
            response.raise_for_status()
            data = response.json()

            # === Maju waktu HALUS ===
            self.t_end += 0.01  # 0.01 detik per update → 100 ms = 10 langkah

            # === Data ===
            t = np.array(data["t"])
            signals = {k: np.array(data[k]) for k in ["x1", "x2", "y1", "y2", "y3"]}
            y = signals[self.current_signal]

            # === Plot ===
            self.figure.clear()
            ax = self.figure.add_subplot(111)

            # Tampilkan x1 dan x2 (latar belakang)
            ax.plot(t, signals["x1"], label="x1(t)", color="red", alpha=0.5, linewidth=1.2)
            ax.plot(t, signals["x2"], label="x2(t)", color="blue", alpha=0.5, linewidth=1.2)

            # Tampilkan hasil operasi (tebal)
            ax.plot(t, y, label=self.signal_combo.currentText(),
                    color=self.get_color(self.current_signal), linewidth=2.8)

            # Styling
            ax.set_title(f"Real-Time: {self.signal_combo.currentText()}", fontsize=14, fontweight='bold')
            ax.set_xlabel("Waktu (s)")
            ax.set_ylabel("Amplitudo")
            ax.legend(loc="upper right")
            ax.grid(True, alpha=0.3, linestyle="--")
            ax.set_xlim(params["t_start"], params["t_end"])

            self.canvas.draw()

        except requests.RequestException as e:
            self.status_label.setText(f"Backend Error: {str(e)[:50]}...")
            self.status_label.setStyleSheet("color: red;")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Plot gagal: {str(e)}")

    def get_color(self, key):
        colors = {
            "x1": "red",
            "x2": "blue",
            "y1": "green",
            "y2": "purple",
            "y3": "orange"
        }
        return colors.get(key, "black")

# ==============================
# RUN APP
# ==============================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SignalGeneratorWindow()
    window.show()
    sys.exit(app.exec())