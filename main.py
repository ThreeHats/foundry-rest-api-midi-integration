import sys
from PyQt6.QtWidgets import QApplication
from app import MidiRestApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MidiRestApp()
    window.show()
    sys.exit(app.exec())
