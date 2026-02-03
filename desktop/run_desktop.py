#!/usr/bin/env python3
import sys
import os

# Add the desktop directory to Python path
desktop_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, desktop_dir)

# Enable high DPI scaling before QApplication is created
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# Create QApplication
app = QApplication(sys.argv)
app.setApplicationName("Chemical Equipment Parameter Visualizer")

# Import and create main window
try:
    from app.windows.main_window import MainWindow
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
