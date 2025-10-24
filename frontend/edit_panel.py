# edit_panel.py
from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QMessageBox

class EditPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setHorizontalSpacing(5)
        layout.setVerticalSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        # Inputs
        self.a1_input = self.create_input("1.0")
        self.a2_input = self.create_input("0.5")
        self.f1_input = self.create_input("1.0")
        self.f2_input = self.create_input("2.0")
        self.phi1_input = self.create_input("0.0")
        self.phi2_input = self.create_input("0.0")
        self.samples_input = self.create_input("200")

        layout.addWidget(QLabel("A1 (x1):"), 0, 0)
        layout.addWidget(self.a1_input, 0, 1)
        layout.addWidget(QLabel("A2 (x2):"), 0, 2)
        layout.addWidget(self.a2_input, 0, 3)
        layout.addWidget(QLabel("f1 (Hz):"), 1, 0)
        layout.addWidget(self.f1_input, 1, 1)
        layout.addWidget(QLabel("f2 (Hz):"), 1, 2)
        layout.addWidget(self.f2_input, 1, 3)
        layout.addWidget(QLabel("φ1 (rad):"), 2, 0)
        layout.addWidget(self.phi1_input, 2, 1)
        layout.addWidget(QLabel("φ2 (rad):"), 2, 2)
        layout.addWidget(self.phi2_input, 2, 3)
        layout.addWidget(QLabel("Samples:"), 3, 0)
        layout.addWidget(self.samples_input, 3, 1)

    def create_input(self, default_value):
        input_field = QLineEdit(default_value)
        input_field.setFixedWidth(600)
        return input_field

    def get_params(self, t_end, t_duration):
        """Mengambil parameter input dari user."""
        try:
            return {
                "a1": float(self.a1_input.text()),
                "a2": float(self.a2_input.text()),
                "f1": float(self.f1_input.text()),
                "f2": float(self.f2_input.text()),
                "phi1": float(self.phi1_input.text()),
                "phi2": float(self.phi2_input.text()),
                "t_start": max(0.0, t_end - t_duration),
                "t_end": t_end,
                "samples": max(50, int(self.samples_input.text())),
            }
        except ValueError as e:
            QMessageBox.critical(self, "Error", f"Input tidak valid: {e}")
            return None
