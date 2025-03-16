from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class ConfigWidget(QWidget):
    save_config_signal = pyqtSignal(str, str, str)
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.init_ui()
        
        # Connect API client signals
        self.api_client.api_status_changed.connect(self.on_api_status_changed)
        self.api_client.clients_loaded.connect(self.on_clients_loaded)
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # API Configuration group
        api_group = QGroupBox("API Configuration")
        api_layout = QFormLayout()
        api_group.setLayout(api_layout)
        
        # API URL
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("https://your-foundry-server.com/api")
        api_layout.addRow("API URL:", self.api_url_input)
        
        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Your API key")
        api_layout.addRow("API Key:", self.api_key_input)
        
        # Test connection button
        test_button_layout = QHBoxLayout()
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        test_button_layout.addWidget(self.test_button)
        test_button_layout.addStretch()
        api_layout.addRow("", test_button_layout)
        
        # Connection status
        self.status_label = QLabel("Not connected")
        api_layout.addRow("Status:", self.status_label)
        
        # Client Configuration group
        client_group = QGroupBox("Client Configuration")
        client_layout = QFormLayout()
        client_group.setLayout(client_layout)
        
        # Client selection
        self.client_combo = QComboBox()
        self.client_combo.setEnabled(False)
        client_layout.addRow("Select Client:", self.client_combo)
        
        # Refresh clients button
        refresh_button_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh Clients")
        self.refresh_button.clicked.connect(self.fetch_clients)
        refresh_button_layout.addWidget(self.refresh_button)
        refresh_button_layout.addStretch()
        client_layout.addRow("", refresh_button_layout)
        
        # Save configuration button
        save_button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Configuration")
        self.save_button.clicked.connect(self.save_config)
        save_button_layout.addWidget(self.save_button)
        save_button_layout.addStretch()
        
        # Add all to main layout
        main_layout.addWidget(api_group)
        main_layout.addWidget(client_group)
        main_layout.addLayout(save_button_layout)
        main_layout.addStretch()
        
        # Load existing configuration
        self.load_config()
    
    def load_config(self):
        """Load existing configuration"""
        self.api_url_input.setText(self.api_client.api_url)
        self.api_key_input.setText(self.api_client.api_key)
    
    def test_connection(self):
        """Test API connection"""
        url = self.api_url_input.text().strip()
        key = self.api_key_input.text().strip()
        
        if not url or not key:
            QMessageBox.warning(self, "Missing Information", 
                              "Please enter both API URL and API Key")
            return
        
        self.status_label.setText("Testing connection...")
        self.api_client.set_api_config(url, key)
        # The result will be handled by the on_api_status_changed slot
    
    def on_api_status_changed(self, success, message):
        """Handle API connection status changes"""
        if success:
            self.status_label.setText(f"Connected: {message}")
            self.status_label.setStyleSheet("color: green")
            self.client_combo.setEnabled(True)
        else:
            self.status_label.setText(f"Error: {message}")
            self.status_label.setStyleSheet("color: red")
            self.client_combo.setEnabled(False)
    
    def fetch_clients(self):
        """Fetch clients from the API"""
        self.api_client.fetch_clients()
    
    def on_clients_loaded(self, clients):
        """Handle loaded clients"""
        self.client_combo.clear()
        self.client_combo.addItem("Select a client", "")
        
        for client in clients:
            # Client is now a string ID like "foundry-rQLkX9c1U2Tzkyh8"
            self.client_combo.addItem(client, client)
        
        # Select current client if it exists
        if self.api_client.client_id:
            index = self.client_combo.findData(self.api_client.client_id)
            if index != -1:
                self.client_combo.setCurrentIndex(index)
    
    def save_config(self):
        """Save API configuration"""
        url = self.api_url_input.text().strip()
        key = self.api_key_input.text().strip()
        client_id = self.client_combo.currentData()
        
        if not url or not key:
            QMessageBox.warning(self, "Missing Information", 
                              "Please enter both API URL and API Key")
            return
        
        self.save_config_signal.emit(url, key, client_id)
        QMessageBox.information(self, "Configuration Saved", 
                             "API configuration has been saved.")
