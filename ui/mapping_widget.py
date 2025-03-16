import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QPushButton, QComboBox, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox,
    QSpinBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal

logger = logging.getLogger(__name__)

class MappingWidget(QWidget):
    mapping_changed_signal = pyqtSignal(dict)
    
    def __init__(self, midi_handler, api_client):
        super().__init__()
        self.midi_handler = midi_handler
        self.api_client = api_client
        self.learning_mode = False
        self.current_midi_message = None
        
        logger.info("Initializing MIDI mapping widget")
        
        # Connect signals
        self.midi_handler.midi_devices_changed.connect(self.update_midi_devices)
        self.midi_handler.midi_signal_received.connect(self.on_midi_received)
        self.api_client.endpoints_loaded.connect(self.update_endpoints)
        
        self.init_ui()
        self.refresh_mappings()
    
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # MIDI Device selection
        midi_group = QGroupBox("MIDI Device")
        midi_layout = QHBoxLayout()
        midi_group.setLayout(midi_layout)
        
        midi_layout.addWidget(QLabel("MIDI Input:"))
        self.midi_device_combo = QComboBox()
        midi_layout.addWidget(self.midi_device_combo)
        
        self.refresh_midi_button = QPushButton("Refresh")
        self.refresh_midi_button.clicked.connect(self.refresh_midi_devices)
        midi_layout.addWidget(self.refresh_midi_button)
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_device)
        midi_layout.addWidget(self.connect_button)
        
        main_layout.addWidget(midi_group)
        
        # Add mapping controls
        mapping_group = QGroupBox("Create Mapping")
        mapping_layout = QGridLayout()
        mapping_group.setLayout(mapping_layout)
        
        # MIDI Signal selection
        mapping_layout.addWidget(QLabel("MIDI Signal Type:"), 0, 0)
        self.signal_type_combo = QComboBox()
        self.signal_type_combo.addItems(["note_on", "note_off", "control_change"])
        mapping_layout.addWidget(self.signal_type_combo, 0, 1)
        
        # Channel, note/control
        mapping_layout.addWidget(QLabel("Channel:"), 0, 2)
        self.channel_spin = QSpinBox()
        self.channel_spin.setRange(0, 15)
        mapping_layout.addWidget(self.channel_spin, 0, 3)
        
        mapping_layout.addWidget(QLabel("Note/Control:"), 1, 0)
        self.note_control_spin = QSpinBox()
        self.note_control_spin.setRange(0, 127)
        mapping_layout.addWidget(self.note_control_spin, 1, 1)
        
        # API Endpoint selection
        mapping_layout.addWidget(QLabel("API Endpoint:"), 1, 2)
        self.endpoint_combo = QComboBox()
        self.endpoint_combo.setEditable(True)
        mapping_layout.addWidget(self.endpoint_combo, 1, 3)
        
        # MIDI Learn function
        self.learn_button = QPushButton("MIDI Learn")
        self.learn_button.setCheckable(True)
        self.learn_button.clicked.connect(self.toggle_learn_mode)
        mapping_layout.addWidget(self.learn_button, 2, 0)
        
        # Add mapping button
        self.add_mapping_button = QPushButton("Add Mapping")
        self.add_mapping_button.clicked.connect(self.add_mapping)
        mapping_layout.addWidget(self.add_mapping_button, 2, 1)
        
        main_layout.addWidget(mapping_group)
        
        # Mappings table
        main_layout.addWidget(QLabel("Current Mappings:"))
        
        self.mappings_table = QTableWidget(0, 4)
        self.mappings_table.setHorizontalHeaderLabels([
            "MIDI Signal Type", "Channel", "Note/Control", "API Endpoint"
        ])
        self.mappings_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.mappings_table)
        
        # Delete selected mapping button
        delete_button_layout = QHBoxLayout()
        self.delete_mapping_button = QPushButton("Delete Selected Mapping")
        self.delete_mapping_button.clicked.connect(self.delete_mapping)
        delete_button_layout.addWidget(self.delete_mapping_button)
        delete_button_layout.addStretch()
        main_layout.addLayout(delete_button_layout)
        
        # Initialize with devices
        self.refresh_midi_devices()
    
    def refresh_midi_devices(self):
        """Refresh MIDI device list"""
        logger.debug("Refreshing MIDI device list")
        devices = self.midi_handler.refresh_devices()
        self.update_midi_devices(devices)
    
    def update_midi_devices(self, devices):
        """Update MIDI device dropdown"""
        logger.debug("Updating MIDI device dropdown with %d devices", len(devices))
        current_device = self.midi_device_combo.currentText()
        self.midi_device_combo.clear()
        
        for device in devices:
            self.midi_device_combo.addItem(device)
        
        # Restore previously selected device if available
        if current_device:
            index = self.midi_device_combo.findText(current_device)
            if index != -1:
                self.midi_device_combo.setCurrentIndex(index)
        
        # If we have a current device connected, update the button text
        if self.midi_handler.current_device:
            logger.debug("Currently connected to MIDI device: %s", self.midi_handler.current_device)
            self.connect_button.setText("Disconnect")
        else:
            self.connect_button.setText("Connect")
    
    def update_endpoints(self, endpoints):
        """Update API endpoints dropdown"""
        logger.debug("Updating API endpoints dropdown with %d endpoints", len(endpoints))
        current_endpoint = self.endpoint_combo.currentText()
        self.endpoint_combo.clear()
        
        # Check if we received the full endpoint objects or just paths
        if endpoints and isinstance(endpoints[0], dict):
            # We have full endpoint info
            for endpoint in endpoints:
                display = endpoint.get("display", "")
                path = endpoint.get("path", "")
                description = endpoint.get("description", "")
                
                # Add to dropdown with tooltip
                self.endpoint_combo.addItem(f"{endpoint['method']} {path}", path)
                index = self.endpoint_combo.count() - 1
                self.endpoint_combo.setItemData(index, description, Qt.ItemDataRole.ToolTipRole)
        else:
            # Just paths (backward compatibility)
            for endpoint in endpoints:
                self.endpoint_combo.addItem(endpoint)
        
        # Restore previously selected endpoint if available
        if current_endpoint:
            index = self.endpoint_combo.findText(current_endpoint)
            if index != -1:
                self.endpoint_combo.setCurrentIndex(index)
    
    def connect_to_device(self):
        """Connect or disconnect from MIDI device"""
        if self.midi_handler.current_device:
            # Disconnect
            logger.info("Disconnecting from MIDI device: %s", self.midi_handler.current_device)
            self.midi_handler.close()
            self.midi_handler.current_device = None
            self.connect_button.setText("Connect")
        else:
            # Connect
            device = self.midi_device_combo.currentText()
            if device:
                logger.info("Connecting to MIDI device: %s", device)
                if self.midi_handler.connect_to_device(device):
                    self.connect_button.setText("Disconnect")
                else:
                    logger.error("Failed to connect to MIDI device: %s", device)
                    QMessageBox.warning(self, "Connection Error", 
                                     f"Failed to connect to {device}")
    
    def toggle_learn_mode(self):
        """Toggle MIDI learn mode"""
        self.learning_mode = self.learn_button.isChecked()
        if self.learning_mode:
            logger.info("MIDI learn mode activated")
            self.learn_button.setText("Listening...")
            self.current_midi_message = None
        else:
            logger.info("MIDI learn mode deactivated")
            self.learn_button.setText("MIDI Learn")
    
    def on_midi_received(self, message, endpoint=None):
        """Handle received MIDI message"""
        if self.learning_mode:
            # In learn mode, store the received message
            if message.type in ['note_on', 'note_off', 'control_change']:
                if message.type == 'note_on' and message.velocity == 0:
                    return  # Ignore note_on with velocity 0 (equivalent to note_off)
                
                logger.info("MIDI learn captured: %s", message)
                self.signal_type_combo.setCurrentText(message.type)
                self.channel_spin.setValue(message.channel)
                
                if message.type in ['note_on', 'note_off']:
                    self.note_control_spin.setValue(message.note)
                elif message.type == 'control_change':
                    self.note_control_spin.setValue(message.control)
                
                self.current_midi_message = message
                self.learn_button.setChecked(False)
                self.toggle_learn_mode()
    
    def add_mapping(self):
        """Add a new MIDI mapping"""
        msg_type = self.signal_type_combo.currentText()
        channel = self.channel_spin.value()
        note_or_control = self.note_control_spin.value()
        
        # Get endpoint path (might be stored in the item data)
        endpoint_index = self.endpoint_combo.currentIndex()
        if endpoint_index >= 0:
            endpoint = self.endpoint_combo.itemData(endpoint_index) or self.endpoint_combo.currentText()
        else:
            endpoint = self.endpoint_combo.currentText()
        
        if not endpoint:
            logger.warning("Missing endpoint when adding mapping")
            QMessageBox.warning(self, "Missing Information", 
                             "Please select or enter an API endpoint")
            return
        
        # Add mapping
        logger.info("Adding MIDI mapping: (%s, %d, %d) -> %s", 
                   msg_type, channel, note_or_control, endpoint)
        self.midi_handler.add_mapping(msg_type, channel, note_or_control, endpoint)
        
        # Refresh display
        self.refresh_mappings()
        
        # Notify change
        self.mapping_changed_signal.emit(self.midi_handler.mappings)
    
    def delete_mapping(self):
        """Delete selected mapping"""
        selected_row = self.mappings_table.currentRow()
        if selected_row >= 0:
            msg_type = self.mappings_table.item(selected_row, 0).text()
            channel = int(self.mappings_table.item(selected_row, 1).text())
            note_or_control = int(self.mappings_table.item(selected_row, 2).text())
            endpoint = self.mappings_table.item(selected_row, 3).text()
            
            # Remove mapping
            logger.info("Deleting MIDI mapping: (%s, %d, %d) -> %s", 
                       msg_type, channel, note_or_control, endpoint)
            self.midi_handler.remove_mapping(msg_type, channel, note_or_control)
            
            # Refresh display
            self.refresh_mappings()
            
            # Notify change
            self.mapping_changed_signal.emit(self.midi_handler.mappings)
        else:
            logger.warning("Attempted to delete mapping with no row selected")
    
    def refresh_mappings(self):
        """Refresh the mappings table"""
        logger.debug("Refreshing mappings table with %d mappings", len(self.midi_handler.mappings))
        self.mappings_table.setRowCount(0)
        
        for (msg_type, channel, note_control), endpoint in self.midi_handler.mappings.items():
            row_position = self.mappings_table.rowCount()
            self.mappings_table.insertRow(row_position)
            
            self.mappings_table.setItem(row_position, 0, QTableWidgetItem(msg_type))
            self.mappings_table.setItem(row_position, 1, QTableWidgetItem(str(channel)))
            self.mappings_table.setItem(row_position, 2, QTableWidgetItem(str(note_control)))
            self.mappings_table.setItem(row_position, 3, QTableWidgetItem(endpoint))
