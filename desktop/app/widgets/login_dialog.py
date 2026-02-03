from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class LoginDialog(QDialog):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.token = None
        self.init_ui()
        self.apply_modern_styling()

    def init_ui(self):
        self.setWindowTitle("Login - Chemical Equipment Visualizer")
        self.setFixedSize(400, 300)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        # Title
        title = QLabel("Welcome Back")
        title.setFont(QFont("Inter", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1f2937; margin-bottom: 8px;")
        layout.addWidget(title)

        subtitle = QLabel("Sign in to your account")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #6b7280; font-size: 13px; margin-bottom: 16px;")
        layout.addWidget(subtitle)

        # Form container
        form_frame = QFrame()
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(16)

        # Username field
        username_label = QLabel("Username")
        username_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #374151;")
        form_layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setMinimumHeight(40)
        form_layout.addWidget(self.username_input)

        # Password field
        password_label = QLabel("Password")
        password_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #374151;")
        form_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setMinimumHeight(40)
        form_layout.addWidget(self.password_input)

        layout.addWidget(form_frame)

        # Login button
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setMinimumHeight(44)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)

        # Register link
        register_layout = QHBoxLayout()
        register_layout.addStretch()
        register_label = QLabel("Don't have an account?")
        register_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        register_layout.addWidget(register_label)
        
        register_btn = QPushButton("Sign Up")
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #3b82f6;
                border: none;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 8px;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #2563eb;
            }
        """)
        register_btn.clicked.connect(self.show_register_dialog)
        register_layout.addWidget(register_btn)
        register_layout.addStretch()
        
        layout.addLayout(register_layout)
        layout.addStretch()

        # Set focus to username field
        self.username_input.setFocus()
        self.login_btn.setDefault(True)

    def apply_modern_styling(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            }
            QLineEdit {
                background-color: #f9fafb;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
                color: #1f2937;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                background-color: #ffffff;
                outline: none;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #e5e7eb;
                color: #9ca3af;
            }
        """)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password")
            return

        try:
            result = self.api_client.login(username, password)
            self.token = result.get('token')
            if self.token:
                self.accept()
            else:
                QMessageBox.critical(self, "Login Failed", "Invalid username or password")
        except Exception as e:
            QMessageBox.critical(self, "Login Error", f"Failed to login: {str(e)}")

    def show_register_dialog(self):
        dialog = RegisterDialog(self.api_client, self)
        if dialog.exec_() == 1:
            # If registration was successful, populate username field
            self.username_input.setText(dialog.registered_username)

    def get_token(self):
        return self.token


class RegisterDialog(QDialog):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.registered_username = None
        self.init_ui()
        self.apply_modern_styling()

    def init_ui(self):
        self.setWindowTitle("Register - Chemical Equipment Visualizer")
        self.setFixedSize(400, 320)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        # Title
        title = QLabel("Create Account")
        title.setFont(QFont("Inter", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1f2937; margin-bottom: 8px;")
        layout.addWidget(title)

        subtitle = QLabel("Sign up for a new account")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #6b7280; font-size: 13px; margin-bottom: 16px;")
        layout.addWidget(subtitle)

        # Form container
        form_frame = QFrame()
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(16)

        # Username field
        username_label = QLabel("Username")
        username_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #374151;")
        form_layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose a username")
        self.username_input.setMinimumHeight(40)
        form_layout.addWidget(self.username_input)

        # Password field
        password_label = QLabel("Password")
        password_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #374151;")
        form_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Choose a password")
        self.password_input.setMinimumHeight(40)
        form_layout.addWidget(self.password_input)

        # Confirm password field
        confirm_password_label = QLabel("Confirm Password")
        confirm_password_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #374151;")
        form_layout.addWidget(confirm_password_label)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("Confirm your password")
        self.confirm_password_input.setMinimumHeight(40)
        form_layout.addWidget(self.confirm_password_input)

        layout.addWidget(form_frame)

        # Register button
        self.register_btn = QPushButton("Sign Up")
        self.register_btn.setMinimumHeight(44)
        self.register_btn.clicked.connect(self.handle_register)
        layout.addWidget(self.register_btn)

        # Set focus to username field
        self.username_input.setFocus()
        self.register_btn.setDefault(True)

    def apply_modern_styling(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                font-family: 'Inter', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            }
            QLineEdit {
                background-color: #f9fafb;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
                color: #1f2937;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                background-color: #ffffff;
                outline: none;
            }
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
            QPushButton:disabled {
                background-color: #e5e7eb;
                color: #9ca3af;
            }
        """)

    def handle_register(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters long")
            return

        try:
            result = self.api_client.register(username, password)
            self.registered_username = username
            QMessageBox.information(self, "Success", "Account created successfully! You can now sign in.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Registration Error", f"Failed to register: {str(e)}")
