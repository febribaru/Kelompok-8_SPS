# main.py
import sys
import requests
import numpy as np
import csv
import os
import datetime
from io import StringIO

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QMessageBox,
    QFileDialog, QApplication
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from edit_panel import EditPanel
import pandas as pd


class SignalGeneratorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Signal Generator - Real-Time Oscilloscope")
        self.setGeometry(50, 50, 1400, 850)

        self.is_running = False
        self.current_signal = "x1"
        self.t_end = self.t_duration = 2.0
        self.last_data = None  # Simpan semua data
        self.last_signals = None  # Simpan sinyal yang sedang ditampilkan

        # Main Layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 20, 30, 30)

        # Input Panel
        self.edit_panel = EditPanel(self)
        layout.addWidget(self.edit_panel)

        # Controls
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setSpacing(15)
        controls_layout.addWidget(QLabel("Tampilkan:"))

        self.signal_combo = QComboBox()
        self.signal_combo.addItems([
            "x1(t)", "x2(t)",
            "y1(t) = x1 + x2", "y2(t) = x1 - x2", "y3(t) = x1 × x2"
        ])
        self.signal_combo.currentTextChanged.connect(self.on_signal_change)
        controls_layout.addWidget(self.signal_combo, stretch=1)

        # Tombol START
        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("startBtn")
        self.start_button.clicked.connect(self.toggle_realtime)
        controls_layout.addWidget(self.start_button)

        # Tombol RESET
        reset_btn = QPushButton("Reset Waktu")
        reset_btn.setObjectName("resetBtn")
        reset_btn.clicked.connect(self.reset_time)
        controls_layout.addWidget(reset_btn)

        # Tombol EXPORT EXCEL
        self.export_btn = QPushButton("Export to Excel")
        self.export_btn.setObjectName("exportBtn")
        self.export_btn.clicked.connect(self.export_to_excel_smart)
        self.export_btn.setEnabled(False)
        controls_layout.addWidget(self.export_btn)

        controls_layout.addStretch()
        layout.addWidget(controls_container)

        # Status
        self.status_label = QLabel("Status: Stopped")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.status_label)

        # Plot
        self.figure = Figure(figsize=(12, 6), dpi=100, facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Styles + Timer
        self.apply_styles()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.setInterval(100)

    def apply_styles(self):
        self.setStyleSheet("""
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d0e3ff, stop:1 #d0d0d0);
        }
        QLabel {
            color: #2c3e50; font-size: 14px; font-weight: bold;
        }
        QLineEdit {
            background: white; color: #2c3e50; border: 2px solid #cbd5e0;
            border-radius: 8px; padding: 8px 10px; font-size: 14px; font-weight: bold;
        }
        QPushButton {
            color: white; border: none; border-radius: 8px;
            padding: 10px 20px; font-size: 13px; font-weight: bold; min-width: 140px;
        }
        QPushButton#startBtn {
            background-color: #3182ce;
        }
        QPushButton#startBtn:hover {
            background-color: #2b6cb0;
        }
        QPushButton#resetBtn {
            background-color: #e53e3e;
        }
        QPushButton#resetBtn:hover {
            background-color: #c53030;
        }
        QPushButton#exportBtn {
            background-color: #27ae60;
        }
        QPushButton#exportBtn:hover {
            background-color: #219653;
        }
        QPushButton#exportBtn:disabled {
            background-color: #95a5a6;
            color: #bdc3c7;
        }
        """)

    def on_signal_change(self, text):
        mapping = {
            "x1(t)": "x1", "x2(t)": "x2",
            "y1(t) = x1 + x2": "y1",
            "y2(t) = x1 - x2": "y2",
            "y3(t) = x1 × x2": "y3"
        }
        self.current_signal = mapping.get(text, "x1")
        if self.is_running:
            self.update_plot()

    def toggle_realtime(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.start_button.setText("Stop")
            self.status_label.setText("Status: Running (Real-Time)")
            self.status_label.setStyleSheet("color: #38a169; font-size: 13px; font-weight: bold;")
            self.timer.start()
        else:
            self.start_button.setText("Start")
            self.status_label.setText("Status: Stopped")
            self.status_label.setStyleSheet("color: #718096; font-size: 13px;")
            self.timer.stop()

    def reset_time(self):
        self.t_end = self.t_duration
        if self.is_running:
            self.update_plot()

    def update_plot(self):
        params = self.edit_panel.get_params(self.t_end, self.t_duration)
        if not params:
            return
        try:
            response = requests.post("http://127.0.0.1:8080/generate", json=params, timeout=1.0)
            response.raise_for_status()
            csv_data = response.text

            # Parse semua data
            data = {"t": [], "x1": [], "x2": [], "y1": [], "y2": [], "y3": []}
            csv_reader = csv.DictReader(StringIO(csv_data))
            for row in csv_reader:
                for key in data:
                    data[key].append(float(row[key]))

            self.last_data = data
            self.last_signals = self.current_signal  # Simpan sinyal yang sedang ditampilkan
            self.export_btn.setEnabled(True)

            self.t_end += 0.01

            t = np.array(data["t"])
            signals = {k: np.array(data[k]) for k in ["x1", "x2", "y1", "y2", "y3"]}
            y = signals[self.current_signal]

            self.figure.clear()
            ax = self.figure.add_subplot(111, facecolor='white')
            ax.plot(t, signals["x1"], label="x1(t)", color="#ef5350", alpha=0.5, linewidth=2, linestyle='--')
            ax.plot(t, signals["x2"], label="x2(t)", color="#42a5f5", alpha=0.5, linewidth=2, linestyle='--')
            ax.plot(t, y, label=self.signal_combo.currentText(),
                    color={
                        "x1":"#ef5350","x2":"#42a5f5","y1":"#66bb6a",
                        "y2":"#ab47bc","y3":"#ffa726"
                    }[self.current_signal],
                    linewidth=3)
            ax.set_title(f"Real-Time: {self.signal_combo.currentText()}", fontsize=14, fontweight='bold', color="#4383c3", pad=15)
            ax.set_xlabel("Waktu (s)", fontsize=11, color="#4b72c4")
            ax.set_ylabel("Amplitudo", fontsize=11, color="#6267ba")
            ax.legend(loc="upper right", framealpha=0.95, fontsize=10)
            ax.grid(True, alpha=0.3, linestyle="-", color="#b3b549")
            ax.set_xlim(params["t_start"], params["t_end"])
            self.canvas.draw()

        except Exception as e:
            print(f"Error: {e}")
            self.export_btn.setEnabled(False)

    def export_to_excel_smart(self):
        if not self.last_data or not self.last_signals:
            QMessageBox.warning(self, "Tidak Ada Data", "Jalankan simulasi terlebih dahulu.")
            return

        # Tentukan kolom yang akan diekspor
        signal = self.last_signals
        export_cols = ["t"]
        filename_parts = []

        if signal == "x1":
            export_cols += ["x1"]
            filename_parts = ["x1"]
        elif signal == "x2":
            export_cols += ["x2"]
            filename_parts = ["x2"]
        elif signal == "y1":
            export_cols += ["x1", "x2", "y1"]
            filename_parts = ["y1", "x1_plus_x2"]
        elif signal == "y2":
            export_cols += ["x1", "x2", "y2"]
            filename_parts = ["y2", "x1_minus_x2"]
        elif signal == "y3":
            export_cols += ["x1", "x2", "y3"]
            filename_parts = ["y3", "x1_times_x2"]

        # Buat nama file otomatis
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"{'_'.join(filename_parts)}_{timestamp}.xlsx"

        # Dialog Save As
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan File Excel",
            default_filename,
            "Excel Files (*.xlsx);;All Files (*)"
        )

        if not file_path:
            return

        if not file_path.lower().endswith('.xlsx'):
            file_path += '.xlsx'

        # Ambil hanya kolom yang dipilih
        export_data = {k: self.last_data[k] for k in export_cols}
        df = pd.DataFrame(export_data)

        try:
            df.to_excel(file_path, index=False, engine='openpyxl')
            QMessageBox.information(
                self,
                "Berhasil",
                f"Data berhasil diekspor ke:\n{file_path}\n\nKolom: {', '.join(export_cols)}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Gagal", f"Error: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
    window = SignalGeneratorWindow()
    window.show()
    sys.exit(app.exec())