from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QStatusBar, QPushButton, QSplitter
)
from PyQt6.QtCore import Qt
from ui.config_widget import ConfigWidget
from ui.mapping_widget import MappingWidget
from ui.midi_monitor_widget import MidiMonitorWidget

class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Create tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create configuration widget
        self.config_widget = ConfigWidget(self.parent.api_client)
        self.tabs.addTab(self.config_widget, "Configuration")
        
        # Create mapping widget
        self.mapping_widget = MappingWidget(
            self.parent.midi_handler,
            self.parent.api_client
        )
        self.tabs.addTab(self.mapping_widget, "MIDI Mappings")
        
        # Create MIDI monitor widget
        self.midi_monitor = MidiMonitorWidget(self.parent.midi_handler)
        self.tabs.addTab(self.midi_monitor, "MIDI Monitor")
        
        # Status bar
        self.status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
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
        self.resize(800, 600)
    
    def show_status(self, message):
        """Show status message"""
        self.status_label.setText(message)
    
    def refresh_clients(self):
        """Refresh client list in config widget"""
        self.config_widget.fetch_clients()
    
    def import_config(self):
        """Import configuration from file"""
        from PyQt6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Configuration", "", "JSON Files (*.json)"
        )
        if filename:
            mappings = self.parent.config_manager.import_config(filename)
            self.parent.midi_handler.set_mappings(mappings)
            self.mapping_widget.refresh_mappings()
            self.show_status(f"Imported configuration from {filename}")
    
    def export_config(self):
        """Export configuration to file"""
        from PyQt6.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Configuration", "", "JSON Files (*.json)"
        )
        if filename:
            self.parent.config_manager.export_config(filename)
            self.show_status(f"Exported configuration to {filename}")
