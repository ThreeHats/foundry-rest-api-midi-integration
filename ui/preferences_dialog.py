#!/usr/bin/env python3
# ui/preferences_dialog.py - User preferences dialog
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, 
    QGroupBox, QDialogButtonBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
import logging

logger = logging.getLogger(__name__)

class PreferencesDialog(QDialog):
    """Dialog for configuring application preferences."""
    
    preferences_changed = pyqtSignal(dict)  # Emit when preferences change
    
    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        self.init_ui()
        self.load_preferences()
    
    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Update settings group
        update_group = QGroupBox("Update Settings")
        update_layout = QVBoxLayout()
        
        # Auto-check for updates
        self.auto_check_checkbox = QCheckBox("Automatically check for updates on startup")
        self.auto_check_checkbox.setToolTip(
            "When enabled, the application will check for updates automatically "
            "when it starts (once per day maximum)."
        )
        update_layout.addWidget(self.auto_check_checkbox)
        
        # Include pre-release updates
        self.prerelease_checkbox = QCheckBox("Include pre-release versions")
        self.prerelease_checkbox.setToolTip(
            "When enabled, the update checker will also notify you about "
            "beta and alpha versions."
        )
        self.prerelease_checkbox.setEnabled(False)  # Not implemented yet
        update_layout.addWidget(self.prerelease_checkbox)
        
        update_group.setLayout(update_layout)
        layout.addWidget(update_group)
        
        # General settings group
        general_group = QGroupBox("General Settings")
        general_layout = QVBoxLayout()
        
        # Minimize to system tray
        self.minimize_tray_checkbox = QCheckBox("Minimize to system tray")
        self.minimize_tray_checkbox.setToolTip(
            "When enabled, closing the window will minimize the application "
            "to the system tray instead of exiting."
        )
        self.minimize_tray_checkbox.setEnabled(False)  # Not implemented yet
        general_layout.addWidget(self.minimize_tray_checkbox)
        
        # Start with Windows
        self.startup_checkbox = QCheckBox("Start with Windows")
        self.startup_checkbox.setToolTip(
            "When enabled, the application will start automatically "
            "when Windows boots."
        )
        self.startup_checkbox.setEnabled(False)  # Not implemented yet
        general_layout.addWidget(self.startup_checkbox)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Add spacer
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacer)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        
        button_box.accepted.connect(self.accept_changes)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_changes)
        
        layout.addWidget(button_box)
    
    def load_preferences(self):
        """Load preferences from settings."""
        if not self.settings:
            return
        
        # Load update preferences
        auto_check = self.settings.value("updates/auto_check", True, type=bool)
        self.auto_check_checkbox.setChecked(auto_check)
        
        # Load other preferences (when implemented)
        # prerelease = self.settings.value("updates/include_prerelease", False, type=bool)
        # self.prerelease_checkbox.setChecked(prerelease)
        
        logger.debug("Loaded preferences: auto_check=%s", auto_check)
    
    def save_preferences(self):
        """Save preferences to settings."""
        if not self.settings:
            return
        
        # Save update preferences
        auto_check = self.auto_check_checkbox.isChecked()
        self.settings.setValue("updates/auto_check", auto_check)
        
        # Save other preferences (when implemented)
        # prerelease = self.prerelease_checkbox.isChecked()
        # self.settings.setValue("updates/include_prerelease", prerelease)
        
        logger.info("Saved preferences: auto_check=%s", auto_check)
        
        # Emit signal with changed preferences
        preferences = {
            "auto_check_updates": auto_check,
            # "include_prerelease": prerelease,
        }
        self.preferences_changed.emit(preferences)
    
    def apply_changes(self):
        """Apply changes without closing the dialog."""
        self.save_preferences()
    
    def accept_changes(self):
        """Accept and save changes, then close the dialog."""
        self.save_preferences()
        self.accept()
    
    def get_current_preferences(self):
        """Get current preferences as a dictionary."""
        return {
            "auto_check_updates": self.auto_check_checkbox.isChecked(),
            # "include_prerelease": self.prerelease_checkbox.isChecked(),
        }
