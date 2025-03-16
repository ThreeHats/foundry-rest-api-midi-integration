import mido
import time
import logging
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class MidiListenerThread(QThread):
    midi_event = pyqtSignal(object)
    
    def __init__(self, port_name):
        super().__init__()
        self.port_name = port_name
        self._running = True
        logger.debug("MIDI listener thread initialized for port: %s", port_name)
    
    def run(self):
        logger.info("Starting MIDI listener thread for: %s", self.port_name)
        try:
            with mido.open_input(self.port_name) as port:
                logger.debug("MIDI port opened: %s", self.port_name)
                while self._running:
                    for message in port.iter_pending():
                        logger.debug("MIDI message received: %s", message)
                        self.midi_event.emit(message)
                    time.sleep(0.001)
        except Exception as e:
            logger.error("MIDI Error: %s", str(e))
        logger.info("MIDI listener thread stopped")
    
    def stop(self):
        logger.debug("Stopping MIDI listener thread")
        self._running = False

class MidiHandler(QObject):
    midi_signal_received = pyqtSignal(object, str)
    midi_devices_changed = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.mappings = {}  # {(msg_type, channel, note/control): endpoint}
        self.current_device = None
        self.listener_thread = None
        logger.info("MIDI handler initialized")
        self.refresh_devices()
    
    def refresh_devices(self) -> List[str]:
        """Refresh the list of MIDI devices"""
        try:
            devices = mido.get_input_names()
            logger.info("Found %d MIDI input devices", len(devices))
            for device in devices:
                logger.debug("MIDI device: %s", device)
            self.midi_devices_changed.emit(devices)
            return devices
        except Exception as e:
            logger.error("Error refreshing MIDI devices: %s", str(e))
            return []
    
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
            return False
    
    def set_mappings(self, mappings: Dict[Tuple, str]):
        """Set MIDI mappings {(msg_type, channel, note/control): endpoint}"""
        self.mappings = mappings
        logger.info("Set %d MIDI mappings", len(mappings))
        for key, endpoint in mappings.items():
            logger.debug("Mapping: %s -> %s", key, endpoint)
    
    def add_mapping(self, msg_type: str, channel: int, 
                    note_or_control: int, endpoint: str):
        """Add a new MIDI mapping"""
        key = (msg_type, channel, note_or_control)
        self.mappings[key] = endpoint
        logger.info("Added MIDI mapping: (%s, %d, %d) -> %s", 
                   msg_type, channel, note_or_control, endpoint)
    
    def remove_mapping(self, msg_type: str, channel: int, note_or_control: int):
        """Remove a MIDI mapping"""
        key = (msg_type, channel, note_or_control)
        if key in self.mappings:
            endpoint = self.mappings[key]
            del self.mappings[key]
            logger.info("Removed MIDI mapping: (%s, %d, %d) -> %s", 
                      msg_type, channel, note_or_control, endpoint)
    
    def _process_midi_message(self, message):
        """Process incoming MIDI message and trigger API calls if mapped"""
        key = None
        
        if message.type == 'note_on' and message.velocity > 0:
            key = ('note_on', message.channel, message.note)
            logger.debug("Note On: Channel %d, Note %d, Velocity %d", 
                       message.channel, message.note, message.velocity)
        elif message.type == 'note_off' or (message.type == 'note_on' and message.velocity == 0):
            key = ('note_off', message.channel, message.note)
            logger.debug("Note Off: Channel %d, Note %d", 
                       message.channel, message.note)
        elif message.type == 'control_change':
            key = ('control_change', message.channel, message.control)
            logger.debug("Control Change: Channel %d, Control %d, Value %d", 
                       message.channel, message.control, message.value)
        
        if key and key in self.mappings:
            endpoint = self.mappings[key]
            logger.info("MIDI message matched mapping: %s -> %s", key, endpoint)
            self.midi_signal_received.emit(message, endpoint)
    
    def close(self):
        """Close MIDI connections"""
        if self.listener_thread and self.listener_thread.isRunning():
            logger.info("Closing MIDI connections")
            self.listener_thread.stop()
            self.listener_thread.wait()
            logger.debug("MIDI listener thread stopped")
