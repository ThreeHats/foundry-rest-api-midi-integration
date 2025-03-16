import mido
import time
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from typing import Dict, List, Any, Optional, Tuple

class MidiListenerThread(QThread):
    midi_event = pyqtSignal(object)
    
    def __init__(self, port_name):
        super().__init__()
        self.port_name = port_name
        self._running = True
    
    def run(self):
        try:
            with mido.open_input(self.port_name) as port:
                while self._running:
                    for message in port.iter_pending():
                        self.midi_event.emit(message)
                    time.sleep(0.001)
        except Exception as e:
            print(f"MIDI Error: {str(e)}")
    
    def stop(self):
        self._running = False

class MidiHandler(QObject):
    midi_signal_received = pyqtSignal(object, str)
    midi_devices_changed = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.mappings = {}  # {(msg_type, channel, note/control): endpoint}
        self.current_device = None
        self.listener_thread = None
        self.refresh_devices()
    
    def refresh_devices(self) -> List[str]:
        """Refresh the list of MIDI devices"""
        devices = mido.get_input_names()
        self.midi_devices_changed.emit(devices)
        return devices
    
    def connect_to_device(self, device_name: str) -> bool:
        """Connect to a MIDI device"""
        if self.listener_thread and self.listener_thread.isRunning():
            self.listener_thread.stop()
            self.listener_thread.wait()
        
        try:
            self.listener_thread = MidiListenerThread(device_name)
            self.listener_thread.midi_event.connect(self._process_midi_message)
            self.listener_thread.start()
            self.current_device = device_name
            return True
        except Exception as e:
            print(f"Failed to connect to MIDI device: {str(e)}")
            return False
    
    def set_mappings(self, mappings: Dict[Tuple, str]):
        """Set MIDI mappings {(msg_type, channel, note/control): endpoint}"""
        self.mappings = mappings
    
    def add_mapping(self, msg_type: str, channel: int, 
                    note_or_control: int, endpoint: str):
        """Add a new MIDI mapping"""
        key = (msg_type, channel, note_or_control)
        self.mappings[key] = endpoint
    
    def remove_mapping(self, msg_type: str, channel: int, note_or_control: int):
        """Remove a MIDI mapping"""
        key = (msg_type, channel, note_or_control)
        if key in self.mappings:
            del self.mappings[key]
    
    def _process_midi_message(self, message):
        """Process incoming MIDI message and trigger API calls if mapped"""
        key = None
        
        if message.type == 'note_on' and message.velocity > 0:
            key = ('note_on', message.channel, message.note)
        elif message.type == 'note_off' or (message.type == 'note_on' and message.velocity == 0):
            key = ('note_off', message.channel, message.note)
        elif message.type == 'control_change':
            key = ('control_change', message.channel, message.control)
        
        if key and key in self.mappings:
            endpoint = self.mappings[key]
            self.midi_signal_received.emit(message, endpoint)
    
    def close(self):
        """Close MIDI connections"""
        if self.listener_thread and self.listener_thread.isRunning():
            self.listener_thread.stop()
            self.listener_thread.wait()
