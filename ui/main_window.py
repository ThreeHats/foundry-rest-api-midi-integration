import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QStatusBar, QPushButton, QSplitter, QSizePolicy,
    QMenuBar, QDialog, QDialogButtonBox, QTextBrowser
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
from ui.config_widget import ConfigWidget
from ui.mapping_widget import MappingWidget
from ui.midi_monitor_widget import MidiMonitorWidget

from update_checker import CURRENT_VERSION

logger = logging.getLogger(__name__)

class AboutDialog(QDialog):
    """About dialog with version information and update check."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("About MIDI REST Integration")
        self.setFixedSize(500, 200)
        
        layout = QVBoxLayout()
        
        # App info
        app_info = QLabel()
        app_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_info.setText(
            "<h2>MIDI REST Integration</h2>"
            f"<p><b>Version:</b> {CURRENT_VERSION}</p>"
            "<p><b>Author:</b> ThreeHats</p>"
            "<p>Connect MIDI controllers to Foundry VTT via REST API</p>"
        )
        layout.addWidget(app_info)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.update_button = QPushButton("Check for Updates")
        self.update_button.clicked.connect(self.check_for_updates)
        button_layout.addWidget(self.update_button)
        
        button_layout.addStretch()
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        button_layout.addWidget(button_box)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def check_for_updates(self):
        """Trigger update check."""
        if self.parent and hasattr(self.parent, 'check_for_updates'):
            self.parent.check_for_updates()

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
        
        # Create menu bar
        self.create_menu_bar(main_layout)
        
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
        
        # Size the window - set to maximize on startup
        self.resize(1200, 1000)  # Set default size in case maximize doesn't work
        logger.debug("Main window UI initialized")
    
    def create_menu_bar(self, main_layout):
        """Create menu bar with Help menu."""
        menu_bar = QMenuBar()
        main_layout.setMenuBar(menu_bar)
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        # Preferences action
        preferences_action = QAction("Import Config", self)
        preferences_action.triggered.connect(self.import_config)
        file_menu.addAction(preferences_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Export Config", self)
        exit_action.triggered.connect(self.export_config)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def check_for_updates(self):
        """Trigger manual update check."""
        if self.parent and hasattr(self.parent, 'check_for_updates'):
            self.parent.check_for_updates()
    
    def show_about(self):
        """Show about dialog."""
        dialog = AboutDialog(self.parent)
        dialog.exec()
    
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
