import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QStatusBar, QPushButton, QSplitter, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from ui.config_widget import ConfigWidget
from ui.mapping_widget import MappingWidget
from ui.midi_monitor_widget import MidiMonitorWidget

logger = logging.getLogger(__name__)

class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        logger.info("Initializing main window UI")
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Create tabs
        logger.debug("Creating UI tabs")
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create configuration widget
        logger.debug("Creating configuration widget")
        self.config_widget = ConfigWidget(self.parent.api_client)
        self.tabs.addTab(self.config_widget, "Configuration")
        
        # Create mapping widget
        logger.debug("Creating mapping widget")
        self.mapping_widget = MappingWidget(
            self.parent.midi_handler,
            self.parent.api_client
        )
        self.tabs.addTab(self.mapping_widget, "MIDI Mappings")
        
        # Create MIDI monitor widget with support for parameters
        logger.debug("Creating MIDI monitor widget")
        self.midi_monitor = MidiMonitorWidget(self.parent.midi_handler)
        self.tabs.addTab(self.midi_monitor, "MIDI Monitor")
        
        # Status bar
        self.status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)  # Enable word wrapping
        self.status_label.setMinimumHeight(20)  # Ensure minimum height for readability
        
        # Set size policy to prevent horizontal expansion
        self.status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        self.status_layout.addWidget(self.status_label)
        
        # Import/Export buttons
        button_layout = QHBoxLayout()
        self.import_button = QPushButton("Import Config")
        self.export_button = QPushButton("Export Config")
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        
        # Connect buttons
        self.import_button.clicked.connect(self.import_config)
        self.export_button.clicked.connect(self.export_config)
        
        # Add status and buttons to main layout
        main_layout.addLayout(button_layout)
        main_layout.addLayout(self.status_layout)
        
        # Size the window
        self.resize(1200, 1000)
        logger.debug("Main window UI initialized")
    
    def show_status(self, message):
        """Show status message"""
        logger.info("Status update: %s", message)
        self.status_label.setText(message)
    
    def show_status_nonblocking(self, message):
        """Show status message in a non-blocking way using a timer"""
        # Use Qt's own event queue to update the UI without blocking the MIDI thread
        QTimer.singleShot(0, lambda: self.status_label.setText(message))
    
    def refresh_clients(self):
        """Refresh client list in config widget"""
        logger.debug("Refreshing client list")
        self.config_widget.fetch_clients()
    
    def import_config(self):
        """Import configuration from file"""
        logger.info("Import config dialog opened")
        from PyQt6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Configuration", "", "JSON Files (*.json)"
        )
        if filename:
            logger.info("Importing configuration from %s", filename)
            mappings = self.parent.config_manager.import_config(filename)
            self.parent.midi_handler.set_mappings(mappings)
            self.mapping_widget.refresh_mappings()
            self.show_status(f"Imported configuration from {filename}")
    
    def export_config(self):
        """Export configuration to file"""
        logger.info("Export config dialog opened")
        from PyQt6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Configuration", "", "JSON Files (*.json)"
        )
        if filename:
            logger.info("Exporting configuration to %s", filename)
            self.parent.config_manager.export_config(filename)
            self.show_status(f"Exported configuration to {filename}")
