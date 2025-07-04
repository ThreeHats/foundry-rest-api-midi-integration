import os
import logging
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import QSettings, Qt, QTimer
from ui.main_window import MainWindow
from midi_handler import MidiHandler
from api_client import ApiClient
from config_manager import ConfigManager
from update_checker import UpdateManager

logger = logging.getLogger(__name__)

class MidiRestApp(QMainWindow):
    def __init__(self, dev_mode=False):
        super().__init__()
        
        # Store dev mode flag
        self.dev_mode = dev_mode
        logger.info("Initializing application components")
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.api_client = ApiClient()
        self.midi_handler = MidiHandler(auto_connect=False)  # Don't auto-connect
        
        # Load settings
        logger.debug("Loading application settings")
        self.settings = QSettings("FoundryVTT", "MidiRestIntegration")
        self.load_settings()
        
        # Setup UI
        logger.debug("Setting up UI")
        self.ui = MainWindow(self)
        self.setCentralWidget(self.ui)
        self.setWindowTitle("MIDI to Foundry VTT REST API")
          # Initialize update manager early to check for updates during startup
        logger.debug("Initializing update manager")
        self.update_manager = UpdateManager(self)
        
        # Load style sheet
        self.load_stylesheet()
        
        # Connect signals
        self.connect_signals()
        
        # Setup automatic update checking immediately
        QTimer.singleShot(1000, lambda: self.update_manager.check_for_updates_async(silent=True))
        
        logger.info("Application initialization complete")
        
    def load_stylesheet(self):
        qss_path = os.path.join(os.path.dirname(__file__), "ui", "style.qss")
        try:
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
                logger.debug("Stylesheet loaded successfully")
        except Exception as e:
            logger.error("Failed to load stylesheet: %s", str(e))
    
    def load_settings(self):
        api_url = self.settings.value("api/url", "")
        api_key = self.settings.value("api/key", "")
        client_id = self.settings.value("api/client_id", "")
        
        logger.info("Loading settings: API URL=%s, Client ID=%s", api_url, client_id)
        self.api_client.set_api_config(api_url, api_key, client_id)
        
        # Load MIDI mappings
        mappings = self.config_manager.load_mappings()
        logger.info("Loaded %d MIDI mappings", len(mappings))
        self.midi_handler.set_mappings(mappings)
        
        # Load window state
        if self.settings.contains("window/geometry"):
            self.restoreGeometry(self.settings.value("window/geometry"))
        
        if self.settings.contains("window/state"):
            self.restoreState(self.settings.value("window/state"))
        else:
            # Default to maximized
            self.setWindowState(self.windowState() | Qt.WindowState.WindowMaximized)
        
    def save_settings(self):
        logger.debug("Saving application settings")
        self.settings.setValue("api/url", self.api_client.api_url)
        self.settings.setValue("api/key", self.api_client.api_key)
        self.settings.setValue("api/client_id", self.api_client.client_id)
        
        # Save MIDI mappings
        self.config_manager.save_mappings(self.midi_handler.mappings)
        logger.info("Settings saved successfully")
        
        # Save window state
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("window/state", self.saveState())
    
    def connect_signals(self):
        # Connect UI signals to handlers
        self.ui.config_widget.save_config_signal.connect(self.on_config_changed)
        self.ui.mapping_widget.mapping_changed_signal.connect(self.on_mapping_changed)
        
        # Connect MIDI handler to API client with parameters support
        self.midi_handler.midi_signal_received.connect(self.on_midi_signal)
        logger.debug("All signals connected")
    
    def on_config_changed(self, url, key, client_id):
        logger.info("Configuration changed: URL=%s, Client ID=%s", url, client_id)
        self.api_client.set_api_config(url, key, client_id)
        self.save_settings()
        
        # Refresh client list
        self.ui.refresh_clients()
    
    def on_mapping_changed(self, mappings):
        logger.info("MIDI mappings updated: %d mappings", len(mappings))
        self.midi_handler.set_mappings(mappings)
        self.save_settings()
    
    def on_midi_signal(self, midi_event, endpoint, query_params, body_params, path_params):
        """Optimized handler for MIDI signals triggering API calls"""
        try:
            # Extract HTTP method if present in endpoint string
            method = None
            if " " in endpoint and endpoint.split(" ")[0] in ["GET", "POST", "PUT", "DELETE"]:
                method, endpoint_path = endpoint.split(" ", 1)
            else:
                endpoint_path = endpoint
                
            # Only log in dev mode to avoid performance overhead
            if self.dev_mode:
                logger.debug("MIDI signal triggered API call: %s%s with params: %s, %s, path: %s", 
                           f"{method} " if method else "", endpoint_path, query_params, body_params, path_params)
            
            # Make the API call directly with method
            response = self.api_client.call_endpoint(
                endpoint_path,
                params=query_params, 
                data=body_params,
                path_params=path_params,
                method=method
            )
            
            # Update UI status in a non-blocking way
            self.ui.show_status_nonblocking(f"API call: {f'{method} ' if method else ''}{endpoint_path}")
            
            # Minimal feedback in production mode
            if self.dev_mode:
                logger.debug("API call succeeded: %s, Response: %s", endpoint_path, response)
        except Exception as e:
            if self.dev_mode:
                logger.error("API call failed: %s, Error: %s", endpoint_path, str(e))
            self.ui.show_status_nonblocking(f"Error: {str(e)}")
    
    def check_for_updates(self):
        """Manually check for updates."""
        logger.info("Manual update check requested")
        self.update_manager.check_for_updates_async(silent=False)
    
    def show_status(self, message):
        """Show status message in UI."""
        if hasattr(self.ui, 'show_status'):
            self.ui.show_status(message)
    
    def closeEvent(self, event):
        logger.info("Application closing")
        self.save_settings()
        self.midi_handler.close()
        event.accept()
