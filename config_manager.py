import json
import os
import logging
from PyQt6.QtCore import QObject
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class ConfigManager(QObject):
    def __init__(self):
        super().__init__()
        self.config_dir = os.path.join(os.path.expanduser('~'), '.foundry_midi_rest')
        self.mappings_file = os.path.join(self.config_dir, 'mappings.json')
        logger.info("Config manager initialized: %s", self.config_dir)
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """Ensure the configuration directory exists"""
        if not os.path.exists(self.config_dir):
            logger.info("Creating configuration directory: %s", self.config_dir)
            os.makedirs(self.config_dir)
    
    def save_mappings(self, mappings: Dict[Tuple, any]):
        """Save MIDI mappings to file"""
        logger.info("Saving %d MIDI mappings to %s", len(mappings), self.mappings_file)
        
        # Convert tuple keys to strings for JSON serialization
        serializable_mappings = {}
        for (msg_type, channel, note_control), mapping_data in mappings.items():
            key = f"{msg_type}:{channel}:{note_control}"
            
            # Handle both old and new formats
            if isinstance(mapping_data, dict):
                serializable_mappings[key] = mapping_data
            else:
                # Legacy format: just the endpoint string
                serializable_mappings[key] = {
                    "endpoint": mapping_data,
                    "query_params": {},
                    "body_params": {}
                }
        
        try:
            with open(self.mappings_file, 'w') as f:
                json.dump(serializable_mappings, f, indent=2)
            logger.debug("Mappings saved successfully")
        except Exception as e:
            logger.error("Error saving mappings: %s", str(e))
    
    def load_mappings(self) -> Dict[Tuple, any]:
        """Load MIDI mappings from file"""
        if not os.path.exists(self.mappings_file):
            logger.info("No mappings file found at %s", self.mappings_file)
            return {}
        
        try:
            logger.info("Loading MIDI mappings from %s", self.mappings_file)
            with open(self.mappings_file, 'r') as f:
                serialized_mappings = json.load(f)
            
            # Convert string keys back to tuples
            mappings = {}
            for key, mapping_data in serialized_mappings.items():
                msg_type, channel, note_control = key.split(':')
                tuple_key = (msg_type, int(channel), int(note_control))
                
                # Handle both old and new formats
                if isinstance(mapping_data, dict) and "endpoint" in mapping_data:
                    mappings[tuple_key] = mapping_data
                else:
                    # Legacy format or just the endpoint string
                    mappings[tuple_key] = {
                        "endpoint": mapping_data if isinstance(mapping_data, str) else mapping_data["endpoint"],
                        "query_params": mapping_data.get("query_params", {}),
                        "body_params": mapping_data.get("body_params", {})
                    }
            
            logger.info("Loaded %d MIDI mappings", len(mappings))
            return mappings
        except Exception as e:
            logger.error("Error loading mappings: %s", str(e))
            return {}
    
    def export_config(self, filename: str):
        """Export configuration to a file"""
        if not filename.endswith('.json'):
            filename += '.json'
        
        logger.info("Exporting configuration to %s", filename)
            
        try:
            mappings = self.load_mappings()
            serializable_mappings = {
                f"{msg_type}:{channel}:{note_control}": endpoint
                for (msg_type, channel, note_control), endpoint in mappings.items()
            }
            
            with open(filename, 'w') as f:
                json.dump(serializable_mappings, f, indent=2)
            logger.info("Configuration exported successfully")
        except Exception as e:
            logger.error("Error exporting configuration: %s", str(e))
    
    def import_config(self, filename: str) -> Dict[Tuple, str]:
        """Import configuration from a file"""
        logger.info("Importing configuration from %s", filename)
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
            logger.info("Imported %d mappings", len(mappings))
            
            return mappings
        except Exception as e:
            logger.error("Error importing configuration: %s", str(e))
            return {}
