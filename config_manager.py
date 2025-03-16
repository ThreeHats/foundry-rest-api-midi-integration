import json
import os
from PyQt6.QtCore import QObject
from typing import Dict, List, Any, Optional, Tuple

class ConfigManager(QObject):
    def __init__(self):
        super().__init__()
        self.config_dir = os.path.join(os.path.expanduser('~'), '.foundry_midi_rest')
        self.mappings_file = os.path.join(self.config_dir, 'mappings.json')
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """Ensure the configuration directory exists"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
    
    def save_mappings(self, mappings: Dict[Tuple, str]):
        """Save MIDI mappings to file"""
        # Convert tuple keys to strings for JSON serialization
        serializable_mappings = {
            f"{msg_type}:{channel}:{note_control}": endpoint
            for (msg_type, channel, note_control), endpoint in mappings.items()
        }
        
        with open(self.mappings_file, 'w') as f:
            json.dump(serializable_mappings, f, indent=2)
    
    def load_mappings(self) -> Dict[Tuple, str]:
        """Load MIDI mappings from file"""
        if not os.path.exists(self.mappings_file):
            return {}
        
        try:
            with open(self.mappings_file, 'r') as f:
                serialized_mappings = json.load(f)
            
            # Convert string keys back to tuples
            mappings = {}
            for key, endpoint in serialized_mappings.items():
                msg_type, channel, note_control = key.split(':')
                mappings[(msg_type, int(channel), int(note_control))] = endpoint
            
            return mappings
        except Exception as e:
            print(f"Error loading mappings: {str(e)}")
            return {}
    
    def export_config(self, filename: str):
        """Export configuration to a file"""
        if not filename.endswith('.json'):
            filename += '.json'
            
        mappings = self.load_mappings()
        serializable_mappings = {
            f"{msg_type}:{channel}:{note_control}": endpoint
            for (msg_type, channel, note_control), endpoint in mappings.items()
        }
        
        with open(filename, 'w') as f:
            json.dump(serializable_mappings, f, indent=2)
    
    def import_config(self, filename: str) -> Dict[Tuple, str]:
        """Import configuration from a file"""
        try:
            with open(filename, 'r') as f:
                serialized_mappings = json.load(f)
            
            # Convert string keys back to tuples
            mappings = {}
            for key, endpoint in serialized_mappings.items():
                msg_type, channel, note_control = key.split(':')
                mappings[(msg_type, int(channel), int(note_control))] = endpoint
            
            # Save the imported mappings
            self.save_mappings(mappings)
            
            return mappings
        except Exception as e:
            print(f"Error importing configuration: {str(e)}")
            return {}
