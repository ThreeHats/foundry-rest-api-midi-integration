import mido
import time
import logging
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from typing import Dict, List, Any, Optional, Tuple
from collections import deque

logger = logging.getLogger(__name__)

class MidiListenerThread(QThread):
    midi_event = pyqtSignal(object)
    
    def __init__(self, port_name, buffer_size=10):
        super().__init__()
        self.port_name = port_name
        self._running = True
        # Modified buffer design that stores the message key and a timestamp
        # This will allow repeated button presses after a small timeout
        self._message_buffer = {}  # {key: timestamp}
        self._buffer_timeout = 0.1  # 100ms timeout for duplicate messages
        logger.debug("MIDI listener thread initialized for port: %s", port_name)
    
    def run(self):
        logger.info("Starting MIDI listener thread for: %s", self.port_name)
        try:
            with mido.open_input(self.port_name) as port:
                logger.debug("MIDI port opened: %s", self.port_name)
                while self._running:
                    for message in port.iter_pending():
                        # Create a unique key for the message
                        message_key = (message.type, message.channel, 
                                     getattr(message, 'note', -1), 
                                     getattr(message, 'control', -1))
                        
                        current_time = time.time()
                        
                        # Check if this is a repeated message within the timeout period
                        # For note_on/note_off pairs, we always process both
                        if (message_key in self._message_buffer and 
                            message.type not in ['note_off', 'note_on'] and
                            current_time - self._message_buffer[message_key] < self._buffer_timeout):
                            # Skip too-frequent duplicate messages
                            continue
                        
                        # Update the timestamp and process the message
                        self._message_buffer[message_key] = current_time
                        self.midi_event.emit(message)
                        
                    # Optimized sleep time for lower latency
                    time.sleep(0.001)  # 1ms polling is enough for real-time performance
        except Exception as e:
            logger.error("MIDI Error: %s", str(e))
        logger.info("MIDI listener thread stopped")
    
    def stop(self):
        logger.debug("Stopping MIDI listener thread")
        self._running = False


class MidiHandler(QObject):
    midi_signal_received = pyqtSignal(object, str, dict, dict, dict)  # message, endpoint, query_params, body_params, path_params
    midi_devices_changed = pyqtSignal(list)
    
    def __init__(self, auto_connect=False):
        super().__init__()
        self.mappings = {}  # {(msg_type, channel, note/control): endpoint}
        self.current_device = None
        self.listener_thread = None
        logger.info("MIDI handler initialized")
        
        # Cache device list but don't connect automatically
        self._cached_devices = []
        if auto_connect:
            self.refresh_devices()
    
    def refresh_devices(self) -> List[str]:
        """Refresh the list of MIDI devices without auto-connecting"""
        try:
            devices = mido.get_input_names()
            self._cached_devices = devices
            logger.info("Found %d MIDI input devices", len(devices))
            if logger.level <= logging.DEBUG:
                for device in devices:
                    logger.debug("MIDI device: %s", device)
            self.midi_devices_changed.emit(devices)
            return devices
        except Exception as e:
            logger.error("Error refreshing MIDI devices: %s", str(e))
            return []
    
    def get_cached_devices(self) -> List[str]:
        """Get the cached device list without querying hardware"""
        if not self._cached_devices:
            # Only refresh if cache is empty
            return self.refresh_devices()
        return self._cached_devices
    
    def connect_to_device(self, device_name: str) -> bool:
        """Connect to a MIDI device"""
        if self.listener_thread and self.listener_thread.isRunning():
            logger.debug("Stopping existing MIDI listener thread")
            self.listener_thread.stop()
            self.listener_thread.wait()
        
        try:
            logger.info("Connecting to MIDI device: %s", device_name)
            self.listener_thread = MidiListenerThread(device_name)
            self.listener_thread.midi_event.connect(self._process_midi_message)
            self.listener_thread.start()
            self.current_device = device_name
            logger.info("Successfully connected to MIDI device")
            return True
        except Exception as e:
            logger.error("Failed to connect to MIDI device: %s - %s", device_name, str(e))
            self.listener_thread = None  # Fix: Clear the reference if connection failed
            return False
    
    def set_mappings(self, mappings: Dict[Tuple, str]):
        """Set MIDI mappings {(msg_type, channel, note/control): endpoint}"""
        self.mappings = mappings
        logger.info("Set %d MIDI mappings", len(mappings))
        for key, endpoint in mappings.items():
            logger.debug("Mapping: %s -> %s", key, endpoint)
    
    def add_mapping(self, msg_type: str, channel: int, 
                    note_or_control: int, endpoint: str,
                    query_params: dict = None,
                    body_params: dict = None,
                    path_params: dict = None):
        """Add a new MIDI mapping with parameters"""
        key = (msg_type, channel, note_or_control)
        self.mappings[key] = {
            "endpoint": endpoint,
            "query_params": query_params or {},
            "body_params": body_params or {},
            "path_params": path_params or {}
        }
        logger.info("Added MIDI mapping: (%s, %d, %d) -> %s with params", 
                   msg_type, channel, note_or_control, endpoint)
    
    def remove_mapping(self, msg_type: str, channel: int, note_or_control: int):
        """Remove a MIDI mapping"""
        key = (msg_type, channel, note_or_control)
        if key in self.mappings:
            mapping_data = self.mappings[key]
            endpoint = mapping_data["endpoint"] if isinstance(mapping_data, dict) else mapping_data
            del self.mappings[key]
            logger.info("Removed MIDI mapping: (%s, %d, %d) -> %s", 
                      msg_type, channel, note_or_control, endpoint)
    
    def _process_midi_message(self, message):
        """Process incoming MIDI message and trigger API calls if mapped"""
        key = None
        
        # Use direct access to message attributes for performance
        if message.type == 'note_on' and message.velocity > 0:
            key = ('note_on', message.channel, message.note)
        elif message.type == 'note_off' or (message.type == 'note_on' and message.velocity == 0):
            key = ('note_off', message.channel, message.note)
        elif message.type == 'control_change':
            key = ('control_change', message.channel, message.control)
        
        # Fast path for mapped keys
        if key and key in self.mappings:
            mapping_data = self.mappings[key]
            
            # Handle both old and new mapping formats with minimal processing
            if isinstance(mapping_data, dict):
                endpoint = mapping_data["endpoint"]
                query_params = mapping_data.get("query_params", {})
                body_params = mapping_data.get("body_params", {})
                path_params = mapping_data.get("path_params", {})
            else:
                # Legacy format: just the endpoint string
                endpoint = mapping_data
                query_params = {}
                body_params = {}
                path_params = {}
                
            # Update the signal to include path parameters
            self.midi_signal_received.emit(message, endpoint, query_params, body_params, path_params)
    
    def close(self):
        """Close MIDI connections"""
        if self.listener_thread and self.listener_thread.isRunning():
            logger.info("Closing MIDI connections")
            self.listener_thread.stop()
            self.listener_thread.wait()
            logger.debug("MIDI listener thread stopped")
