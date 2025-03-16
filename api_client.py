import requests
import logging
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, List, Any

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
        logger.debug("API client initialized")
    
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
    
    def call_endpoint(self, endpoint, params=None, data=None):
        """Call a specific endpoint with parameters
        
        Args:
            endpoint (str): The endpoint path
            params (dict, optional): Query parameters
            data (dict, optional): Body data (for POST/PUT)
        """
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
            
        headers = {'x-api-key': self.api_key}
        if self.client_id:
            # Always add client_id as query parameter if specified
            if params is None:
                params = {}
            params['clientId'] = self.client_id
            
            # Also include it in header for legacy support
            headers['Client-ID'] = self.client_id
        
        logger.debug("Calling API endpoint: %s with params: %s, data: %s", endpoint, params, data)
            
        try:
            response = self._make_request("POST", endpoint, params=params, json=data)
            logger.debug("API response status: %d", response.status_code)
            return response.json() if response.content else {'success': True}
        except Exception as e:
            logger.error("API call failed: %s - %s", endpoint, str(e))
            raise Exception(f"API call failed: {str(e)}")
    
    def _make_request(self, method, endpoint, **kwargs):
        """Make a request to the API"""
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
            
        headers = kwargs.get('headers', {})
        # Use x-api-key header instead of Authorization
        headers['x-api-key'] = self.api_key
        if self.client_id:
            headers['Client-ID'] = self.client_id
        
        kwargs['headers'] = headers
        url = f"{self.api_url}{endpoint}"
        
        logger.debug("%s request to %s", method, url)
        return requests.request(method, url, **kwargs)
