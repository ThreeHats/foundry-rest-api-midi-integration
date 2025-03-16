import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QGroupBox, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

logger = logging.getLogger(__name__)

class ConfigWidget(QWidget):
    save_config_signal = pyqtSignal(str, str, str)
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        logger.debug("Initializing config widget")
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
        self.status_label.setWordWrap(True)  # Enable word wrapping
        self.status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
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
        logger.debug("Loading existing API configuration")
        self.api_url_input.setText(self.api_client.api_url)
        self.api_key_input.setText(self.api_client.api_key)
    
    def test_connection(self):
        """Test API connection"""
        url = self.api_url_input.text().strip()
        key = self.api_key_input.text().strip()
        
        if not url or not key:
            logger.warning("Missing API URL or key for connection test")
            QMessageBox.warning(self, "Missing Information", 
                              "Please enter both API URL and API Key")
            return
        
        logger.info("Testing connection to API: %s", url)
        self.status_label.setText("Testing connection...")
        self.api_client.set_api_config(url, key)
        # The result will be handled by the on_api_status_changed slot
    
    def on_api_status_changed(self, success, message):
        """Handle API connection status changes"""
        if success:
            logger.info("API connection succeeded: %s", message)
            self.status_label.setText(f"Connected: {message}")
            self.status_label.setStyleSheet("color: green")
            self.client_combo.setEnabled(True)
        else:
            logger.warning("API connection failed: %s", message)
            self.status_label.setText(f"Error: {message}")
            self.status_label.setStyleSheet("color: red")
            self.client_combo.setEnabled(False)
        
        # Make sure the status label doesn't expand the layout
        self.status_label.setMinimumWidth(200)  # Set a reasonable minimum width
        self.adjustSize()  # Adjust the size of the widget to fit contents
    
    def fetch_clients(self):
        """Fetch clients from the API"""
        logger.debug("Requesting client list from API")
        self.api_client.fetch_clients()
    
    def on_clients_loaded(self, clients):
        """Handle loaded clients"""
        logger.info("Received %d clients from API", len(clients))
        self.client_combo.clear()
        self.client_combo.addItem("Select a client", "")
        
        for client in clients:
            # Client is now a dictionary with id, instanceId, lastSeen, etc.
            if isinstance(client, dict) and "id" in client:
                client_id = client["id"]
                instance_id = client.get("instanceId", "")
                
                # Use instance ID as additional info if available
                display_text = client_id
                if instance_id:
                    display_text = f"{client_id} ({instance_id})"
                    
                logger.debug("Adding client: %s", client_id)
                self.client_combo.addItem(display_text, client_id)
            elif isinstance(client, str):
                # Handle legacy format where client is just a string
                logger.debug("Adding client (legacy format): %s", client)
                self.client_combo.addItem(client, client)
        
        # Select current client if it exists
        if self.api_client.client_id:
            logger.debug("Setting current client to: %s", self.api_client.client_id)
            index = self.client_combo.findData(self.api_client.client_id)
            if index != -1:
                self.client_combo.setCurrentIndex(index)
    
    def save_config(self):
        """Save API configuration"""
        url = self.api_url_input.text().strip()
        key = self.api_key_input.text().strip()
        client_id = self.client_combo.currentData()
        
        if not url or not key:
            logger.warning("Missing API URL or key when saving configuration")
            QMessageBox.warning(self, "Missing Information", 
                              "Please enter both API URL and API Key")
            return
        
        logger.info("Saving API configuration: URL=%s, Client ID=%s", url, client_id)
        self.save_config_signal.emit(url, key, client_id)
        QMessageBox.information(self, "Configuration Saved", 
                             "API configuration has been saved.")
