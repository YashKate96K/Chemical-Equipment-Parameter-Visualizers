#!/usr/bin/env python3
import sys
import os

# Add the desktop directory to Python path
desktop_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, desktop_dir)

# Enable high DPI scaling BEFORE creating QApplication
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# Create QApplication
app = QApplication(sys.argv)

# Import and create main window
try:
    from app.windows.main_window import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
