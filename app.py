import os
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import QSettings
from ui.main_window import MainWindow
from midi_handler import MidiHandler
from api_client import ApiClient
from config_manager import ConfigManager

class MidiRestApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.api_client = ApiClient()
        self.midi_handler = MidiHandler()
        
        # Load settings
        self.settings = QSettings("FoundryVTT", "MidiRestIntegration")
        self.load_settings()
        
        # Setup UI
        self.ui = MainWindow(self)
        self.setCentralWidget(self.ui)
        self.setWindowTitle("MIDI to Foundry VTT REST API")
        
        # Load style sheet
        self.load_stylesheet()
        
        # Connect signals
        self.connect_signals()
        
    def load_stylesheet(self):
        qss_path = os.path.join(os.path.dirname(__file__), "ui", "style.qss")
        with open(qss_path, "r") as f:
            self.setStyleSheet(f.read())
    
    def load_settings(self):
        api_url = self.settings.value("api/url", "")
        api_key = self.settings.value("api/key", "")
        client_id = self.settings.value("api/client_id", "")
        
        self.api_client.set_api_config(api_url, api_key, client_id)
        
        # Load MIDI mappings
        mappings = self.config_manager.load_mappings()
        self.midi_handler.set_mappings(mappings)
        
    def save_settings(self):
        self.settings.setValue("api/url", self.api_client.api_url)
        self.settings.setValue("api/key", self.api_client.api_key)
        self.settings.setValue("api/client_id", self.api_client.client_id)
        
        # Save MIDI mappings
        self.config_manager.save_mappings(self.midi_handler.mappings)
    
    def connect_signals(self):
        # Connect UI signals to handlers
        self.ui.config_widget.save_config_signal.connect(self.on_config_changed)
        self.ui.mapping_widget.mapping_changed_signal.connect(self.on_mapping_changed)
        
        # Connect MIDI handler to API client
        self.midi_handler.midi_signal_received.connect(self.on_midi_signal)
    
    def on_config_changed(self, url, key, client_id):
        self.api_client.set_api_config(url, key, client_id)
        self.save_settings()
        
        # Refresh client list
        self.ui.refresh_clients()
    
    def on_mapping_changed(self, mappings):
        self.midi_handler.set_mappings(mappings)
        self.save_settings()
    
    def on_midi_signal(self, midi_event, endpoint):
        try:
            response = self.api_client.call_endpoint(endpoint)
            self.ui.show_status(f"API call succeeded: {endpoint}")
        except Exception as e:
            self.ui.show_status(f"API call failed: {str(e)}")
    
    def closeEvent(self, event):
        self.save_settings()
        self.midi_handler.close()
        event.accept()
