import requests
from PyQt6.QtCore import QObject, pyqtSignal

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
    
    def set_api_config(self, url, key, client_id=""):
        """Set API configuration"""
        self.api_url = url.rstrip('/')
        self.api_key = key
        self.client_id = client_id
        
        # Test connection
        if url and key:
            self.test_connection()
    
    def test_connection(self):
        """Test API connection and fetch available endpoints"""
        try:
            response = self._make_request("GET", "/")
            if response.status_code == 200:
                self.api_status_changed.emit(True, "Connected successfully")
                self.fetch_clients()
                self.fetch_available_endpoints()
                return True
            else:
                self.api_status_changed.emit(False, f"Failed with status code: {response.status_code}")
                return False
        except Exception as e:
            self.api_status_changed.emit(False, str(e))
            return False
    
    def fetch_clients(self):
        """Fetch available clients from the API"""
        try:
            response = self._make_request("GET", "/clients")
            if response.status_code == 200:
                response_data = response.json()
                if "clients" in response_data and isinstance(response_data["clients"], list):
                    clients = response_data["clients"]
                    self.clients_loaded.emit(clients)
                    return clients
                else:
                    self.api_status_changed.emit(False, "Invalid client data format")
                    return []
            return []
        except Exception as e:
            self.api_status_changed.emit(False, f"Failed to fetch clients: {str(e)}")
            return []
    
    def fetch_available_endpoints(self):
        """Fetch available endpoints from the API"""
        try:
            response = self._make_request("GET", "/endpoints")
            if response.status_code == 200:
                endpoints = response.json()
                self.available_endpoints = endpoints
                self.endpoints_loaded.emit(endpoints)
                return endpoints
            return []
        except Exception as e:
            self.api_status_changed.emit(False, f"Failed to fetch endpoints: {str(e)}")
            return []
    
    def call_endpoint(self, endpoint, data=None):
        """Call a specific endpoint"""
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
            
        headers = {'x-api-key': self.api_key}
        if self.client_id:
            headers['Client-ID'] = self.client_id
            
        try:
            response = self._make_request("POST", endpoint, json=data)
            return response.json() if response.content else {'success': True}
        except Exception as e:
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
        return requests.request(method, f"{self.api_url}{endpoint}", **kwargs)
