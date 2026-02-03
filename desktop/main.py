#!/usr/bin/env python3
import sys
import os

# Add the desktop directory to Python path to import app modules
desktop_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, desktop_dir)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from app.windows.main_window import MainWindow

def main():
    # Enable high DPI scaling before QApplication is created
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Chemical Equipment Parameter Visualizer")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Chemical Equipment Visualizer")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
