import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QTabWidget, QWidget, QMessageBox, QScrollArea,
    QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt
import json

logger = logging.getLogger(__name__)

class ParameterDialog(QDialog):
    def __init__(self, endpoint_data, query_params=None, body_params=None, path_params=None, parent=None):
        """Dialog for configuring endpoint parameters
        
        Args:
            endpoint_data (dict): The endpoint information from API docs
            query_params (dict, optional): Existing query parameters
            body_params (dict, optional): Existing body parameters
            path_params (dict, optional): Existing path parameters
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.endpoint_data = endpoint_data
        self.query_params = query_params or {}
        self.body_params = body_params or {}
        self.path_params = path_params or {}
        self.required_param_inputs = {}  # To track inputs for required parameters
        self.optional_param_inputs = {}  # To track inputs for optional parameters
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI"""
        self.setWindowTitle("Configure Endpoint Parameters")
        self.resize(550, 450)
        
        main_layout = QVBoxLayout(self)
        
        # Add endpoint information
        method = self.endpoint_data.get("method", "")
        path = self.endpoint_data.get("path", "")
        description = self.endpoint_data.get("description", "")
        
        info_group = QGroupBox("Endpoint Information")
        info_layout = QFormLayout()
        info_layout.addRow("Method:", QLabel(method))
        info_layout.addRow("Path:", QLabel(path))
        info_layout.addRow("Description:", QLabel(description))
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)
        
        # Create parameter tabs
        param_tabs = QTabWidget()
        
        # Create required parameters tab
        required_tab = QWidget()
        required_layout = QVBoxLayout(required_tab)
        required_scroll = QScrollArea()
        required_scroll.setWidgetResizable(True)
        required_scroll_content = QWidget()
        required_form = QFormLayout(required_scroll_content)
        
        # Add standard required parameters (includes path parameters now)
        required_params = self.endpoint_data.get("required_parameters", [])
        
        if required_params:
            for param in required_params:
                param_name = param.get("name", "")
                param_type = param.get("type", "")
                param_desc = param.get("description", "")
                param_location = param.get("location", "")
                
                # Skip clientId parameter as it's handled automatically
                if param_name == "clientId":
                    continue
                
                # Create appropriate input field based on type
                input_field = self._create_input_for_type(param_type)
                
                # Add tooltip with description
                input_field.setToolTip(f"{param_desc} (Type: {param_type})")
                
                # Set existing value if available
                if param_location == "query" and param_name in self.query_params:
                    self._set_value_for_field(input_field, param_type, self.query_params[param_name])
                elif param_location == "body" and param_name in self.body_params:
                    self._set_value_for_field(input_field, param_type, self.body_params[param_name])
                elif param_location == "path" and param_name in self.path_params:
                    self._set_value_for_field(input_field, param_type, self.path_params[param_name])
                
                # Add to form with location prefix
                label_text = f"{param_name} ({param_location}) [{param_type}]"
                required_form.addRow(label_text, input_field)
                
                # Store the input field reference
                self.required_param_inputs[(param_name, param_location, param_type)] = input_field
        else:
            required_form.addRow(QLabel("No required parameters for this endpoint."))
        
        required_scroll.setWidget(required_scroll_content)
        required_layout.addWidget(required_scroll)
        param_tabs.addTab(required_tab, "Required Parameters")
        
        # Create optional parameters tab (unchanged)
        optional_tab = QWidget()
        optional_layout = QVBoxLayout(optional_tab)
        optional_scroll = QScrollArea()
        optional_scroll.setWidgetResizable(True)
        optional_scroll_content = QWidget()
        optional_form = QFormLayout(optional_scroll_content)
        optional_params = self.endpoint_data.get("optional_parameters", [])
        
        if optional_params:
            for param in optional_params:
                param_name = param.get("name", "")
                param_type = param.get("type", "")
                param_desc = param.get("description", "")
                param_location = param.get("location", "")
                
                # Skip clientId parameter as it's handled automatically
                if param_name == "clientId":
                    continue
                
                # Create appropriate input field based on type
                input_field = self._create_input_for_type(param_type)
                
                # Add tooltip with description
                input_field.setToolTip(f"{param_desc} (Type: {param_type})")
                
                # Set existing value if available
                if param_location == "query" and param_name in self.query_params:
                    self._set_value_for_field(input_field, param_type, self.query_params[param_name])
                elif param_location == "body" and param_name in self.body_params:
                    self._set_value_for_field(input_field, param_type, self.body_params[param_name])
                
                # Add to form with location prefix
                label_text = f"{param_name} ({param_location}) [{param_type}]"
                optional_form.addRow(label_text, input_field)
                
                # Store the input field reference
                self.optional_param_inputs[(param_name, param_location, param_type)] = input_field
        else:
            optional_form.addRow(QLabel("No optional parameters for this endpoint."))
        
        optional_scroll.setWidget(optional_scroll_content)
        optional_layout.addWidget(optional_scroll)
        param_tabs.addTab(optional_tab, "Optional Parameters")
        
        main_layout.addWidget(param_tabs)
        
        # Add buttons
        buttons_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept_parameters)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.save_button)
        main_layout.addLayout(buttons_layout)
    
    def _create_input_for_type(self, param_type):
        """Create appropriate input widget based on parameter type"""
        if param_type.lower() == "boolean" or param_type.lower() == "bool":
            return QCheckBox("")
        elif "array" in param_type.lower() or "[]" in param_type:
            field = QLineEdit()
            field.setPlaceholderText("Comma-separated values")
            return field
        else:
            # Default to text input for string, number, etc.
            return QLineEdit()
    
    def _set_value_for_field(self, field, param_type, value):
        """Set value for a field based on its type"""
        if isinstance(field, QCheckBox):
            # Handle boolean
            field.setChecked(self._parse_bool_value(value))
        elif "array" in param_type.lower() or "[]" in param_type:
            # Handle arrays - convert to comma-separated string
            if isinstance(value, list):
                field.setText(", ".join(str(item) for item in value))
            else:
                field.setText(str(value))
        else:
            # Handle standard types
            field.setText(str(value))
    
    def _parse_bool_value(self, value):
        """Parse a value as boolean"""
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "on")
        elif isinstance(value, (int, float)):
            return bool(value)
        return False
    
    def _get_value_from_field(self, field, param_type):
        """Get properly typed value from a field"""
        if isinstance(field, QCheckBox):
            return field.isChecked()
        elif "array" in param_type.lower() or "[]" in param_type:
            # Parse comma-separated values into array
            text = field.text().strip()
            if not text:
                return []
            # Try to parse as JSON first if it looks like a proper array
            if text.startswith('[') and text.endswith(']'):
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    pass
            # Fall back to simple comma split
            return [item.strip() for item in text.split(',')]
        else:
            return field.text().strip()
    
    def accept_parameters(self):
        """Validate and accept parameters"""
        # Check required parameters
        missing_required = []
        for (param_name, param_location, param_type), input_field in self.required_param_inputs.items():
            # Only check text fields - checkboxes (booleans) are always valid
            if isinstance(input_field, QLineEdit) and not input_field.text().strip():
                missing_required.append(param_name)
        
        if missing_required:
            QMessageBox.warning(
                self, 
                "Missing Required Parameters",
                f"Please provide values for the following required parameters: {', '.join(missing_required)}"
            )
            return
        
        # Accept dialog
        self.accept()
    
    def get_parameters(self):
        """Get the configured parameters
        
        Returns:
            tuple: (query_params, body_params, path_params)
        """
        query_params = {}
        body_params = {}
        path_params = {}
        
        # Process required parameters
        for (param_name, param_location, param_type), input_field in self.required_param_inputs.items():
            value = self._get_value_from_field(input_field, param_type)
            
            # Skip empty strings but include other falsy values like False or 0
            if isinstance(value, str) and not value:
                continue
                
            if param_location == "query":
                query_params[param_name] = value
            elif param_location == "body":
                body_params[param_name] = value
            elif param_location == "path":
                path_params[param_name] = value
        
        # Process optional parameters
        for (param_name, param_location, param_type), input_field in self.optional_param_inputs.items():
            value = self._get_value_from_field(input_field, param_type)
            
            # Skip empty strings but include other falsy values like False or 0
            if isinstance(value, str) and not value:
                continue
                
            if param_location == "query":
                query_params[param_name] = value
            elif param_location == "body":
                body_params[param_name] = value
        
        return query_params, body_params, path_params
