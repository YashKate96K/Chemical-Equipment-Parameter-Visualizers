from PyQt5.QtWidgets import (QListWidget, QListWidgetItem, QVBoxLayout, 
                             QHBoxLayout, QWidget, QPushButton, QMessageBox,
                             QInputDialog, QMenu, QAction, QLabel)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from datetime import datetime, timedelta

class DatasetListWidget(QWidget):
    dataset_selected = pyqtSignal(dict)
    dataset_deleted = pyqtSignal(int)

    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.datasets = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header with refresh button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Datasets")
        title.setFont(QFont("Inter", 12, QFont.Bold))
        title.setStyleSheet("color: #1f2937; background: transparent; border: none;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Refresh dataset list")
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.clicked.connect(self.refresh_datasets)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)

        # Dataset list
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.list_widget)

        # Upload button
        self.upload_btn = QPushButton("📁 Upload Dataset")
        self.upload_btn.clicked.connect(self.upload_dataset)
        layout.addWidget(self.upload_btn)

        self.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px;
                font-weight: 500;
                padding: 4px;
            }
            QListWidget::item {
                padding: 12px 16px;
                border-bottom: 1px solid #f3f4f6;
                border-radius: 8px;
                margin: 2px 4px;
            }
            QListWidget::item:selected {
                background-color: #dbeafe;
                color: #1e40af;
                border: 1px solid #93c5fd;
            }
            QListWidget::item:hover {
                background-color: #f9fafb;
            }
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #3b82f6, stop: 1 #2563eb);
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 10px;
                font-weight: 600;
                font-size: 12px;
                font-family: 'Inter', 'SF Pro Display', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                letter-spacing: 0.025em;
                min-height: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2563eb, stop: 1 #1d4ed8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #1d4ed8, stop: 1 #1e40af);
            }
            QPushButton:disabled {
                background: #e5e7eb;
                color: #9ca3af;
            }
        """)

    def refresh_datasets(self):
        try:
            self.datasets = self.api_client.get_datasets()
            self.populate_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch datasets: {str(e)}")

    def populate_list(self):
        self.list_widget.clear()
        
        if not self.datasets:
            item = QListWidgetItem("No datasets available")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.list_widget.addItem(item)
            return

        # Sort by creation date (newest first)
        self.datasets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        for i, dataset in enumerate(self.datasets):
            # Get the original filename to display
            filename = dataset.get('filename', '')
            name = dataset.get('name', '')
            
            # Use the complete original filename as display name
            if filename:
                # Create a more meaningful display name
                clean_filename = filename
                
                # If it's a timestamp-based filename, create a meaningful name
                if '_' in filename and filename.split('_')[0].isdigit():
                    # Extract timestamp and create meaningful name
                    timestamp_part = '_'.join(filename.split('_')[1:])  # Get "1769933150.csv"
                    name_without_ext = timestamp_part.replace('.csv', '')  # Get "1769933150"
                    
                    # Create a more user-friendly name with sequential numbering
                    dataset_number = len(self.datasets) - i  # Reverse order for newest first
                    display_name = f"sample_dataset_{dataset_number}.csv"
                else:
                    # Use the original filename if it's not timestamp-based
                    display_name = clean_filename
            else:
                # Remove default names like "Dataset 5", "Dataset 1", etc.
                # Only show if there's a real name, otherwise skip
                if name and not name.startswith('Dataset '):
                    display_name = name
                else:
                    continue  # Skip this item if no real filename/name
            
            # Add upload time if recent (within last hour)
            created_at = dataset.get('created_at', '')
            time_info = ""
            if created_at:
                try:
                    # Parse ISO datetime
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    now = datetime.now(dt.tzinfo)
                    diff = now - dt
                    if diff < timedelta(hours=1):
                        minutes = int(diff.total_seconds() / 60)
                        time_info = f" ({minutes} min ago)"
                    elif diff < timedelta(days=1):
                        hours = int(diff.total_seconds() / 3600)
                        time_info = f" ({hours}h ago)"
                except:
                    pass
            
            display_text = f"{display_name}{time_info}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, dataset)
            self.list_widget.addItem(item)

    def on_item_clicked(self, item):
        dataset = item.data(Qt.UserRole)
        if dataset:
            self.dataset_selected.emit(dataset)

    def upload_dataset(self):
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Dataset File", "", 
            "CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)"
        )
        
        if file_path:
            try:
                result = self.api_client.upload_dataset(file_path)
                QMessageBox.information(self, "Success", "Dataset uploaded successfully!")
                self.refresh_datasets()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to upload dataset: {str(e)}")

    def show_context_menu(self, position):
        item = self.list_widget.itemAt(position)
        if not item:
            return
        
        dataset = item.data(Qt.UserRole)
        if not dataset:
            return
        
        menu = QMenu(self)
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_dataset(dataset))
        menu.addAction(delete_action)
        
        menu.exec_(self.list_widget.mapToGlobal(position))

    def delete_dataset(self, dataset):
        reply = QMessageBox.question(
            self, 
            'Confirm Delete',
            f"Are you sure you want to delete '{dataset.get('filename', 'this dataset')}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                dataset_id = dataset.get('id')
                if dataset_id:
                    self.api_client.session.delete(f"{self.api_client.base_url}/datasets/{dataset_id}/")
                    self.dataset_deleted.emit(dataset_id)
                    self.refresh_datasets()
                    QMessageBox.information(self, "Success", "Dataset deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete dataset: {str(e)}")
