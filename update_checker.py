#!/usr/bin/env python3
# update_checker.py - Update checker and auto-update functionality
import json
import re
import os
import sys
import platform
import tempfile
import subprocess
import webbrowser
from urllib.request import Request, urlopen
from urllib.error import URLError
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QApplication, QSpacerItem, QSizePolicy
import logging

logger = logging.getLogger(__name__)

# Import version information from central location
from version import VERSION as CURRENT_VERSION
from version import GITHUB_REPO

def parse_version(version_str):
    """Parse a version string into a tuple for comparison."""
    # Extract version numbers from the string
    match = re.search(r'(\d+)\.(\d+)\.(\d+)', version_str)
    if match:
        return tuple(map(int, match.groups()))
    return (0, 0, 0)  # Default if parsing fails

class UpdateChecker(QThread):
    """Background thread for checking updates without blocking the UI."""
    
    update_available = pyqtSignal(str, str, str)  # version, download_url, release_notes
    no_update = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, current_version=None, repo=None):
        super().__init__()
        self.current_version = current_version or CURRENT_VERSION
        self.repo = repo or GITHUB_REPO
        
    def run(self):
        """Check for updates in background thread."""
        try:
            logger.info(f"Checking for updates from {self.repo}")
            has_update, latest_version, download_url, release_notes = self.check_for_updates()
            
            if has_update:
                logger.info(f"Update available: {latest_version}")
                self.update_available.emit(latest_version, download_url, release_notes)
            else:
                logger.info("No updates available")
                self.no_update.emit()
                
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            self.error_occurred.emit(str(e))
    
    def check_for_updates(self):
        """
        Check if updates are available from GitHub releases.
        
        Returns:
            (bool, str, str, str): Tuple containing:
                - Whether an update is available
                - Latest version string
                - Download URL
                - Release notes
        """
        try:
            # Form the GitHub API URL for releases
            api_url = f"https://api.github.com/repos/{self.repo}/releases/latest"
            
            # Set up the request with a user agent (GitHub API requires this)
            headers = {
                'User-Agent': f'MIDI-REST-Integration/{self.current_version}'
            }
            request = Request(api_url, headers=headers)
            
            # Fetch the latest release info
            with urlopen(request, timeout=10) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    latest_version = data.get('tag_name', '').lstrip('v')
                    release_notes = data.get('body', 'No release notes available.')
                    
                    # Find the appropriate download URL for the current platform
                    download_url = self._get_platform_download_url(data.get('assets', []))
                    if not download_url:
                        download_url = data.get('html_url', '')
                    
                    # Compare versions
                    current_version_tuple = parse_version(self.current_version)
                    latest_version_tuple = parse_version(latest_version)
                    
                    if latest_version_tuple > current_version_tuple:
                        return True, latest_version, download_url, release_notes
                        
        except URLError as e:
            logger.error(f"Network error checking for updates: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error checking for updates: {e}")
            raise
            
        return False, self.current_version, "", ""
    
    def _get_platform_download_url(self, assets):
        """Get the download URL for the current platform."""
        current_os = platform.system().lower()
        
        # Map platform names to expected file patterns
        platform_patterns = {
            'windows': [r'.*windows.*\.exe$', r'.*win.*\.exe$', r'.*\.exe$'],
            'darwin': [r'.*macos.*\.dmg$', r'.*mac.*\.dmg$', r'.*\.dmg$', r'.*darwin.*'],
            'linux': [r'.*linux.*\.tar\.gz$', r'.*linux.*\.zip$', r'.*\.AppImage$']
        }
        
        patterns = platform_patterns.get(current_os, [])
        
        for asset in assets:
            asset_name = asset.get('name', '').lower()
            for pattern in patterns:
                if re.match(pattern, asset_name):
                    return asset.get('browser_download_url', '')
        
        return ""

class UpdateManager:
    """Manages update checking and installation for the application."""
    
    def __init__(self, parent_widget=None):
        self.parent = parent_widget
        self.settings = None
        if parent_widget and hasattr(parent_widget, 'settings'):
            self.settings = parent_widget.settings
        
        self.update_checker = None
        
    def check_for_updates_async(self, silent=False):
        """
        Check for updates asynchronously.
        
        Args:
            silent: If True, don't show "no updates" dialog
        """
        if self.update_checker and self.update_checker.isRunning():
            logger.warning("Update check already in progress")
            return
            
        self.silent_check = silent
        self.update_checker = UpdateChecker()
        
        # Connect signals
        self.update_checker.update_available.connect(self._on_update_available)
        self.update_checker.no_update.connect(self._on_no_update)
        self.update_checker.error_occurred.connect(self._on_error_occurred)
        
        # Start the check
        self.update_checker.start()
        
        if not silent:
            # Show a simple message that we're checking
            if self.parent:
                self.parent.show_status("Checking for updates...")
    
    def _on_update_available(self, version, download_url, release_notes):
        """Handle when an update is available."""
        if self.parent:
            self.parent.show_status(f"Update available: v{version}")
        
        # Show update dialog
        self._show_update_dialog(version, download_url, release_notes)
    
    def _on_no_update(self):
        """Handle when no update is available."""
        if self.parent:
            self.parent.show_status("Application is up to date")
        
        if not self.silent_check:
            QMessageBox.information(
                self.parent,
                "No Updates",
                "You are running the latest version of MIDI REST Integration."
            )
    
    def _on_error_occurred(self, error_message):
        """Handle when an error occurs during update check."""
        if self.parent:
            self.parent.show_status("Failed to check for updates")
        
        if not self.silent_check:
            QMessageBox.warning(
                self.parent,
                "Update Check Failed",
                f"Failed to check for updates:\n{error_message}\n\n"
                "Please check your internet connection and try again."
            )
    
    def _show_update_dialog(self, version, download_url, release_notes):
        """Show dialog asking user if they want to update."""
        msg_box = QMessageBox(self.parent)
        msg_box.setWindowTitle("Update Available")
        msg_box.setIcon(QMessageBox.Icon.Information)
        
        text = f"A new version (v{version}) is available!\n\n"
        text += "What would you like to do?"
        msg_box.setText(text)
        
        # Truncate release notes if too long
        notes = release_notes[:500]
        if len(release_notes) > 500:
            notes += "..."
        msg_box.setDetailedText(f"Release Notes:\n{notes}")
        
        # Add custom buttons
        download_button = msg_box.addButton("Download", QMessageBox.ButtonRole.AcceptRole)
        remind_button = msg_box.addButton("Remind Later", QMessageBox.ButtonRole.RejectRole)
        skip_button = msg_box.addButton("Skip This Version", QMessageBox.ButtonRole.DestructiveRole)
        
        # Force the dialog to be wider using a layout spacer
        spacer = QSpacerItem(500, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout = msg_box.layout()
        if layout:
            layout.addItem(spacer, layout.rowCount(), 0, 1, layout.columnCount())
        
        msg_box.exec()
        
        clicked_button = msg_box.clickedButton()
        
        if clicked_button == download_button:
            self._download_update(download_url)
        elif clicked_button == skip_button:
            self._skip_version(version)
        # If "Remind Later", do nothing (will check again next time)
    
    def _download_update(self, download_url):
        """Handle downloading the update."""
        try:
            # Open the download URL in the default browser
            webbrowser.open(download_url)
            
            # Show instructions
            QMessageBox.information(
                self.parent,
                "Download Started",
                "The download page has been opened in your browser.\n\n"
                "Please download and install the new version, then restart the application."
            )
            
        except Exception as e:
            logger.error(f"Failed to open download URL: {e}")
            QMessageBox.warning(
                self.parent,
                "Download Failed",
                f"Failed to open download page: {e}\n\n"
                f"You can manually visit:\n{download_url}"
            )
    
    def _skip_version(self, version):
        """Mark a version as skipped."""
        if self.settings:
            self.settings.setValue("updates/skipped_version", version)
            logger.info(f"Skipped version {version}")
    
    def should_check_automatically(self):
        """Check if we should automatically check for updates."""
        if not self.settings:
            return True  # Default to checking
            
        # Check if automatic updates are enabled (default: True)
        auto_check = self.settings.value("updates/auto_check", True, type=bool)
        if not auto_check:
            return False
        
        # Check if enough time has passed since last check
        from PyQt6.QtCore import QDateTime
        last_check = self.settings.value("updates/last_check", QDateTime())
        if isinstance(last_check, QDateTime) and last_check.isValid():
            # Check once per day
            if last_check.addDays(1) > QDateTime.currentDateTime():
                return False
        
        return True
    
    def update_last_check_time(self):
        """Update the last check time."""
        if self.settings:
            from PyQt6.QtCore import QDateTime
            self.settings.setValue("updates/last_check", QDateTime.currentDateTime())
    
    def is_version_skipped(self, version):
        """Check if a version was skipped by the user."""
        if not self.settings:
            return False
        
        skipped_version = self.settings.value("updates/skipped_version", "")
        return skipped_version == version
    
    def setup_automatic_checking(self):
        """Set up automatic update checking with a timer."""
        # Always check on startup, regardless of when the last check was
        # If auto-check is disabled in settings, respect that setting
        auto_check = True
        if self.settings:
            auto_check = self.settings.value("updates/auto_check", True, type=bool)
            
        if auto_check:
            # Check for updates on startup (after a delay)
            startup_timer = QTimer()
            startup_timer.setSingleShot(True)
            startup_timer.timeout.connect(lambda: self.check_for_updates_async(silent=True))
            startup_timer.start(3000)  # Check 3 seconds after startup
            
            # Update last check time
            self.update_last_check_time()
    
    def on_preferences_changed(self, preferences):
        """Handle preferences changes."""
        logger.info("Update preferences changed: %s", preferences)
        
        # If auto-check was just enabled, we might want to check immediately
        if preferences.get("auto_check_updates", False):
            if self.should_check_automatically():
                # Check for updates after a short delay
                QTimer.singleShot(2000, lambda: self.check_for_updates_async(silent=True))
