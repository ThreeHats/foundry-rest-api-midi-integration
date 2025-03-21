import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QTabWidget, QWidget, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt

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
        self.path_param_inputs = {}  # To track inputs for path parameters
        
        # Extract path variables from the endpoint path
        self.path_variables = []
        path = endpoint_data.get("path", "")
        if path:
            # Parse path variables (format: /path/:variable/next)
            parts = path.split('/')
            for part in parts:
                if part and part.startswith(':'):
                    var_name = part[1:]  # Remove the leading colon
                    self.path_variables.append(var_name)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI"""
        self.setWindowTitle("Configure Endpoint Parameters")
        self.resize(500, 400)
        
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
        
        # Create path parameters tab if needed
        if self.path_variables:
            path_tab = QWidget()
            path_layout = QVBoxLayout(path_tab)
            path_scroll = QScrollArea()
            path_scroll.setWidgetResizable(True)
            path_scroll_content = QWidget()
            path_form = QFormLayout(path_scroll_content)
            
            # Add a label explaining path variables
            path_form.addRow(QLabel("These values will replace variables in the endpoint URL path."))
            path_form.addRow(QLabel(f"Endpoint: {self.endpoint_data.get('path', '')}"))
            path_form.addRow(QLabel(""))  # Spacer
            
            for var_name in self.path_variables:
                input_field = QLineEdit()
                
                # Set existing value if available
                if var_name in self.path_params:
                    input_field.setText(str(self.path_params[var_name]))
                
                # Add to form
                label_text = f"{var_name}:"
                path_form.addRow(label_text, input_field)
                
                # Store the input field reference
                self.path_param_inputs[var_name] = input_field
            
            path_scroll.setWidget(path_scroll_content)
            path_layout.addWidget(path_scroll)
            param_tabs.addTab(path_tab, "Path Variables")
        
        # Create required parameters tab
        required_tab = QWidget()
        required_layout = QVBoxLayout(required_tab)
        required_scroll = QScrollArea()
        required_scroll.setWidgetResizable(True)
        required_scroll_content = QWidget()
        required_form = QFormLayout(required_scroll_content)
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
                
                # Create input field
                input_field = QLineEdit()
                
                # Add tooltip with description
                input_field.setToolTip(f"{param_desc} (Type: {param_type})")
                
                # Set existing value if available
                if param_location == "query" and param_name in self.query_params:
                    input_field.setText(str(self.query_params[param_name]))
                elif param_location == "body" and param_name in self.body_params:
                    input_field.setText(str(self.body_params[param_name]))
                
                # Add to form with location prefix
                label_text = f"{param_name} ({param_location})"
                required_form.addRow(label_text, input_field)
                
                # Store the input field reference
                self.required_param_inputs[(param_name, param_location)] = input_field
        else:
            required_form.addRow(QLabel("No required parameters for this endpoint."))
        
        required_scroll.setWidget(required_scroll_content)
        required_layout.addWidget(required_scroll)
        param_tabs.addTab(required_tab, "Required Parameters")
        
        # Create optional parameters tab
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
                
                # Create input field
                input_field = QLineEdit()
                
                # Add tooltip with description
                input_field.setToolTip(f"{param_desc} (Type: {param_type})")
                
                # Set existing value if available
                if param_location == "query" and param_name in self.query_params:
                    input_field.setText(str(self.query_params[param_name]))
                elif param_location == "body" and param_name in self.body_params:
                    input_field.setText(str(self.body_params[param_name]))
                
                # Add to form with location prefix
                label_text = f"{param_name} ({param_location})"
                optional_form.addRow(label_text, input_field)
                
                # Store the input field reference
                self.optional_param_inputs[(param_name, param_location)] = input_field
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
    
    def accept_parameters(self):
        """Validate and accept parameters"""
        # Check path parameters (all are required)
        missing_path = []
        for var_name, input_field in self.path_param_inputs.items():
            if not input_field.text().strip():
                missing_path.append(var_name)
        
        if missing_path:
            QMessageBox.warning(
                self, 
                "Missing Path Variables",
                f"Please provide values for the following path variables: {', '.join(missing_path)}"
            )
            return
        
        # Check required parameters
        missing_required = []
        for (param_name, param_location), input_field in self.required_param_inputs.items():
            if not input_field.text().strip():
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
        
        # Process path parameters
        for var_name, input_field in self.path_param_inputs.items():
            value = input_field.text().strip()
            if value:
                path_params[var_name] = value
        
        # Process required parameters
        for (param_name, param_location), input_field in self.required_param_inputs.items():
            value = input_field.text().strip()
            if value:
                if param_location == "query":
                    query_params[param_name] = value
                elif param_location == "body":
                    body_params[param_name] = value
        
        # Process optional parameters
        for (param_name, param_location), input_field in self.optional_param_inputs.items():
            value = input_field.text().strip()
            if value:
                if param_location == "query":
                    query_params[param_name] = value
                elif param_location == "body":
                    body_params[param_name] = value
        
        return query_params, body_params, path_params
