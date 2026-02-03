from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QSplitter, QMessageBox, QMenuBar, QMenu, QAction,
                             QStatusBar, QLabel, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import sys
import os

# Import from app modules (assuming path is set correctly in main entry point)
from app.utils.api_client import APIClient
from app.widgets.dataset_list import DatasetListWidget
from app.widgets.visualization_fixed import VisualizationWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_client = APIClient()
        self.current_user = "Guest"
        self.init_ui()
        self.apply_modern_styling()
        self.setup_direct_access()

    def init_ui(self):
        self.setWindowTitle("Chemical Equipment Parameter Visualizer - Desktop")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left panel - Dataset list
        self.dataset_list = DatasetListWidget(self.api_client)
        self.dataset_list.setMaximumWidth(400)
        self.dataset_list.setMinimumWidth(300)
        splitter.addWidget(self.dataset_list)

        # Right panel - Visualization
        self.visualization = VisualizationWidget(self.api_client)
        splitter.addWidget(self.visualization)

        # Set splitter proportions
        splitter.setStretchFactor(0, 0)  # Dataset list - fixed size
        splitter.setStretchFactor(1, 1)  # Visualization - expandable
        splitter.setSizes([350, 1050])

        main_layout.addWidget(splitter)

        # Create menu bar
        self.create_menu_bar()

        # Create status bar
        self.create_status_bar()

        # Connect signals
        print("Connecting signals...")  # Debug line
        self.dataset_list.dataset_selected.connect(self.on_dataset_selected)
        self.dataset_list.dataset_deleted.connect(self.on_dataset_deleted)
        print("Signals connected")  # Debug line

    def create_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e5e7eb;
                padding: 4px 8px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #f3f4f6;
            }
            QMenu {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 4px 0;
            }
            QMenu::item {
                padding: 8px 20px;
            }
            QMenu::item:selected {
                background-color: #f3f4f6;
            }
        """)

        # File menu
        file_menu = menubar.addMenu("File")

        upload_action = QAction("📁 Upload Dataset", self)
        upload_action.triggered.connect(self.dataset_list.upload_btn.click)
        file_menu.addAction(upload_action)

        file_menu.addSeparator()

        refresh_action = QAction("🔄 Refresh", self)
        refresh_action.triggered.connect(self.dataset_list.refresh_datasets)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("🚪 Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("View")

        clear_chart_action = QAction("🗑️ Clear Chart", self)
        clear_chart_action.triggered.connect(self.visualization.clear_chart)
        view_menu.addAction(clear_chart_action)

        export_chart_action = QAction("💾 Export Chart", self)
        export_chart_action.triggered.connect(self.visualization.export_chart)
        view_menu.addAction(export_chart_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("ℹ️ About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #f8fafc;
                border-top: 1px solid #e5e7eb;
                padding: 4px 8px;
            }
            QLabel {
                color: #6b7280;
                font-size: 11px;
            }
        """)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        # User label
        self.user_label = QLabel(f"User: {self.current_user}")
        self.status_bar.addPermanentWidget(self.user_label)

    def apply_modern_styling(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
                font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            }
            QSplitter::handle {
                background-color: #e5e7eb;
                width: 1px;
            }
            QSplitter::handle:hover {
                background-color: #d1d5db;
            }
        """)

    def setup_direct_access(self):
        """Setup app without login - direct access"""
        # Set user as guest
        self.user_label.setText(f"User: {self.current_user}")
        self.status_label.setText("Ready - Direct Access Mode")
        
        # Enable UI components
        self.dataset_list.api_client = self.api_client
        self.visualization.api_client = self.api_client
        
        # Load datasets
        try:
            self.dataset_list.refresh_datasets()
        except Exception as e:
            self.status_label.setText(f"Error loading datasets: {str(e)}")

    def on_dataset_selected(self, dataset):
        """Handle dataset selection"""
        print(f"Dataset selected: {dataset}")  # Debug line
        self.status_label.setText(f"Loaded dataset: {dataset.get('filename', 'Unknown')}")
        self.visualization.load_dataset(dataset)
        # Force enable controls
        self.visualization.force_enable_controls()
        print(f"Current dataset in visualization: {self.visualization.current_dataset}")  # Debug line

    def on_dataset_deleted(self, dataset_id):
        """Handle dataset deletion"""
        # If the deleted dataset was currently loaded, clear the visualization
        if (self.visualization.current_dataset and 
            self.visualization.current_dataset.get('id') == dataset_id):
            self.visualization.clear_chart()
            self.visualization.current_dataset = None
            self.visualization.set_controls_enabled(False)
            self.status_label.setText("Dataset deleted")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Chemical Equipment Parameter Visualizer",
            """<b>Chemical Equipment Parameter Visualizer</b><br><br>
            Version: 1.0.0<br>
            A desktop application for visualizing and analyzing<br>
            chemical equipment parameter datasets.<br><br>
            <b>Features:</b><br>
            • Upload and explore CSV/XLSX datasets<br>
            • Interactive charts and visualizations<br>
            • Statistical analysis and insights<br>
            • Outlier detection<br>
            • Export charts and reports<br><br>
            <b>Technologies:</b><br>
            • Backend: Django + DRF<br>
            • Frontend: React + Vite<br>
            • Desktop: PyQt5 + matplotlib<br><br>
            © 2024 Chemical Equipment Visualizer"""
        )

    def closeEvent(self, event):
        """Handle application close event"""
        reply = QMessageBox.question(
            self, 'Confirm Exit',
            'Are you sure you want to exit the application?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
