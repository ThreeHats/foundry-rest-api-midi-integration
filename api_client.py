import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class ApiClient(QObject):
    api_status_changed = pyqtSignal(bool, str)
    clients_loaded = pyqtSignal(list)
    endpoints_loaded = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.api_url = ""
        self.api_key = ""
        self.client_id = ""
        self.available_endpoints = []
        
        # Create an optimized session for faster API calls
        self.session = self._create_session()
        
        logger.debug("API client initialized")
    
    def _create_session(self):
        """Create an optimized session for API calls"""
        session = requests.Session()
        
        # Configure connection pooling and keepalives
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=Retry(
                total=0,  # No retries for real-time performance
                backoff_factor=0
            )
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session
    
    def set_api_config(self, url, key, client_id=""):
        """Set API configuration"""
        self.api_url = url.rstrip('/')
        self.api_key = key
        self.client_id = client_id
        
        logger.info("API configuration set: URL=%s, Client ID=%s", url, client_id)
        
        # Test connection
        if url and key:
            logger.debug("Testing API connection")
            self.test_connection()
    
    def test_connection(self):
        """Test API connection and fetch available endpoints"""
        try:
            logger.debug("Making test request to API root endpoint")
            response = self._make_request("GET", "/")
            if response.status_code == 200:
                logger.info("API connection test successful")
                self.api_status_changed.emit(True, "Connected successfully")
                self.fetch_clients()
                self.fetch_available_endpoints()
                return True
            else:
                logger.warning("API connection failed: Status code %d", response.status_code)
                self.api_status_changed.emit(False, f"Failed with status code: {response.status_code}")
                return False
        except Exception as e:
            logger.error("API connection test error: %s", str(e))
            self.api_status_changed.emit(False, str(e))
            return False
    
    def fetch_clients(self):
        """Fetch available clients from the API"""
        try:
            logger.debug("Fetching clients from API")
            response = self._make_request("GET", "/clients")
            if response.status_code == 200:
                response_data = response.json()
                logger.debug("Clients response: %s", response_data)
                
                if "clients" in response_data and isinstance(response_data["clients"], list):
                    clients = response_data["clients"]
                    logger.info("Successfully fetched %d clients", len(clients))
                    self.clients_loaded.emit(clients)
                    return clients
                else:
                    logger.warning("Invalid client data format in response")
                    self.api_status_changed.emit(False, "Invalid client data format")
                    return []
            logger.warning("Failed to fetch clients: Status code %d", response.status_code)
            return []
        except Exception as e:
            logger.error("Error fetching clients: %s", str(e))
            self.api_status_changed.emit(False, f"Failed to fetch clients: {str(e)}")
            return []
    
    def fetch_available_endpoints(self):
        """Fetch available endpoints from the API documentation"""
        try:
            logger.debug("Fetching available endpoints from API docs")
            response = self._make_request("GET", "/api/docs")
            if response.status_code == 200:
                api_docs = response.json()
                
                if "endpoints" in api_docs and isinstance(api_docs["endpoints"], list):
                    # Extract endpoints from the documentation
                    endpoints = []
                    for endpoint_info in api_docs["endpoints"]:
                        method = endpoint_info.get("method", "")
                        path = endpoint_info.get("path", "")
                        description = endpoint_info.get("description", "")
                        
                        # Skip documentation endpoints
                        if path in ["/api/docs", "/health", "/api/status"]:
                            continue
                            
                        # Extract parameter information
                        required_params = endpoint_info.get("requiredParameters", [])
                        optional_params = endpoint_info.get("optionalParameters", [])
                        
                        # Format endpoint for display
                        formatted_endpoint = f"{method} {path}"
                        endpoints.append({
                            "display": formatted_endpoint,
                            "method": method,
                            "path": path,
                            "description": description,
                            "required_parameters": required_params,
                            "optional_parameters": optional_params
                        })
                    
                    self.available_endpoints = endpoints
                    logger.info("Successfully fetched %d endpoints from API docs", len(endpoints))
                    
                    # Emit the full endpoint objects
                    self.endpoints_loaded.emit(endpoints)
                    return endpoints
                else:
                    logger.warning("Invalid API docs format - missing 'endpoints' array")
            else:
                logger.warning("Failed to fetch API docs: Status code %d", response.status_code)
            return []
        except Exception as e:
            logger.error("Error fetching API docs: %s", str(e))
            self.api_status_changed.emit(False, f"Failed to fetch endpoints: {str(e)}")
            return []
    
    def call_endpoint(self, endpoint, params=None, data=None, path_params=None, method=None):
        """Call a specific endpoint with parameters - optimized for performance
        
        Args:
            endpoint (str): The endpoint path with potential path variables
            params (dict, optional): Query parameters
            data (dict, optional): Body data
            path_params (dict, optional): Path parameter values to substitute
            method (str, optional): HTTP method (GET, POST, PUT, DELETE)
        """
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        
        # Determine the HTTP method
        if not method:
            # Try to extract method from endpoint string if in format "METHOD /path"
            if " " in endpoint and endpoint.split(" ")[0] in ["GET", "POST", "PUT", "DELETE"]:
                method, endpoint = endpoint.split(" ", 1)
            else:
                # Default to POST if not specified
                method = "POST"
        
        # Replace path variables with actual values if provided
        if path_params:
            # Process path variables (replace :variable with actual value)
            path_parts = endpoint.split('/')
            for i, part in enumerate(path_parts):
                if part and part.startswith(':'):
                    var_name = part[1:]  # Remove the colon
                    if var_name in path_params:
                        # Replace with the actual value
                        path_parts[i] = path_params[var_name]
                    else:
                        logger.warning("Missing path parameter value for %s", var_name)
            
            # Reconstruct the endpoint path
            endpoint = '/'.join(path_parts)
            
        headers = {'x-api-key': self.api_key}
        if self.client_id:
            # Always add client_id as query parameter if specified
            if params is None:
                params = {}
            params['clientId'] = self.client_id
            
            # Also include it in header for legacy support
            headers['Client-ID'] = self.client_id
            
        try:
            # Use the session for better performance through connection reuse
            url = f"{self.api_url}{endpoint}"
            
            # Use the appropriate HTTP method
            if method.upper() == "GET":
                response = self.session.get(url, params=params, headers=headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, params=params, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, params=params, headers=headers)
            else:  # Default to POST
                response = self.session.post(url, params=params, json=data, headers=headers)
                
            response.raise_for_status()
            return response.json() if response.content else {'success': True}
        except Exception as e:
            # Minimize logging in the critical path
            raise Exception(f"API call failed: {str(e)}")
    
    def _make_request(self, method, endpoint, **kwargs):
        """Make a request to the API using the session for better performance"""
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
            
        headers = kwargs.get('headers', {})
        # Use x-api-key header instead of Authorization
        headers['x-api-key'] = self.api_key
        if self.client_id:
            headers['Client-ID'] = self.client_id
        
        kwargs['headers'] = headers
        url = f"{self.api_url}{endpoint}"
        
        return self.session.request(method, url, **kwargs)
    
    def __del__(self):
        """Clean up resources"""
        if hasattr(self, 'session'):
            self.session.close()
