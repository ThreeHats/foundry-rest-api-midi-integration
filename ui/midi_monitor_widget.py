import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLabel, QPushButton, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSlot
from datetime import datetime

logger = logging.getLogger(__name__)

class MidiMonitorWidget(QWidget):
    def __init__(self, midi_handler):
        super().__init__()
        self.midi_handler = midi_handler
        self.auto_scroll = True
        self.max_messages = 100
        self.filter_types = set()  # Empty set means no filtering
        
        logger.info("Initializing MIDI monitor widget")
        self.init_ui()
        
        # Connect to MIDI signals
        self.midi_handler.midi_signal_received.connect(self.on_midi_signal)
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_monitor)
        controls_layout.addWidget(self.clear_button)
        
        # Auto-scroll checkbox
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(self.auto_scroll)
        self.auto_scroll_check.stateChanged.connect(self.toggle_auto_scroll)
        controls_layout.addWidget(self.auto_scroll_check)
        
        # Filter controls
        controls_layout.addWidget(QLabel("Filter:"))
        
        self.filter_note_on = QCheckBox("Note On")
        self.filter_note_on.stateChanged.connect(lambda state: self.toggle_filter('note_on', state))
        controls_layout.addWidget(self.filter_note_on)
        
        self.filter_note_off = QCheckBox("Note Off")
        self.filter_note_off.stateChanged.connect(lambda state: self.toggle_filter('note_off', state))
        controls_layout.addWidget(self.filter_note_off)
        
        self.filter_control = QCheckBox("CC")
        self.filter_control.stateChanged.connect(lambda state: self.toggle_filter('control_change', state))
        controls_layout.addWidget(self.filter_control)
        
        controls_layout.addStretch()
        
        # Add controls to main layout
        main_layout.addLayout(controls_layout)
        
        # Monitor text area
        self.monitor_text = QTextEdit()
        self.monitor_text.setReadOnly(True)
        main_layout.addWidget(self.monitor_text)
        
        # Welcome message
        self.monitor_text.append("MIDI Monitor initialized. Waiting for MIDI events...\n")
    
    def toggle_auto_scroll(self, state):
        """Toggle auto-scrolling"""
        self.auto_scroll = state == Qt.CheckState.Checked.value
        logger.debug("Auto-scroll %s", "enabled" if self.auto_scroll else "disabled")
    
    def toggle_filter(self, msg_type, state):
        """Toggle filtering for a specific message type"""
        if state == Qt.CheckState.Checked.value:
            self.filter_types.add(msg_type)
            logger.debug("Added filter for %s messages", msg_type)
        else:
            if msg_type in self.filter_types:
                self.filter_types.remove(msg_type)
                logger.debug("Removed filter for %s messages", msg_type)
    
    def clear_monitor(self):
        """Clear the monitor text"""
        logger.debug("Clearing MIDI monitor display")
        self.monitor_text.clear()
        self.monitor_text.append("Monitor cleared.\n")
    
    @pyqtSlot(object, str, dict, dict, dict)
    def on_midi_signal(self, message, endpoint=None, query_params=None, body_params=None, path_params=None):
        """Handle MIDI signal with parameters"""
        # Apply filters if any are active
        if self.filter_types and message.type not in self.filter_types:
            logger.debug("Filtered out %s message due to display filter", message.type)
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Format message based on type
        if message.type == 'note_on':
            msg_text = f"[{timestamp}] NOTE ON: Channel {message.channel}, Note {message.note}, Velocity {message.velocity}"
        elif message.type == 'note_off':
            msg_text = f"[{timestamp}] NOTE OFF: Channel {message.channel}, Note {message.note}, Velocity {message.velocity}"
        elif message.type == 'control_change':
            msg_text = f"[{timestamp}] CONTROL CHANGE: Channel {message.channel}, Control {message.control}, Value {message.value}"
        else:
            msg_text = f"[{timestamp}] {message.type.upper()}: {message}"
        
        # Add endpoint and parameter info if available
        if endpoint:
            msg_text += f" -> API: {endpoint}"
            
            # Add parameter details if available
            params_text = []
            if path_params and len(path_params) > 0:
                params_text.append(f"Path: {path_params}")
            if query_params and len(query_params) > 0:
                params_text.append(f"Query: {query_params}")
            if body_params and len(body_params) > 0:
                params_text.append(f"Body: {body_params}")
                
            if params_text:
                msg_text += f" ({'; '.join(params_text)})"
                
            logger.debug("Displaying mapped %s message to %s with parameters", message.type, endpoint)
        else:
            logger.debug("Displaying unmapped %s message", message.type)
        
        # Add to monitor with different colors based on message type
        message_html = f"<span style='color: #e6e6e6;'>{msg_text}</span>"
        self.monitor_text.append(message_html)
        
        # Limit the number of messages
        if self.monitor_text.document().lineCount() > self.max_messages:
            logger.debug("Trimming MIDI monitor display (exceeded %d lines)", self.max_messages)
            cursor = self.monitor_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
        
        # Auto-scroll if enabled
        if self.auto_scroll:
            self.monitor_text.verticalScrollBar().setValue(
                self.monitor_text.verticalScrollBar().maximum()
            )
