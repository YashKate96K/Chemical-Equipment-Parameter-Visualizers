#!/usr/bin/env python3
import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    try:
        # Import Qt modules first
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        
        # Set application attributes BEFORE creating QApplication
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("Chemical Equipment Parameter Visualizer")
        
        # Import and create main window
        from app.windows.main_window import MainWindow
        window = MainWindow()
        window.show()
        
        # Run the application
        return app.exec_()
        
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Please install required packages: pip install PyQt5 matplotlib numpy scipy requests")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
