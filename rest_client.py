class RestClient:
    def __init__(self, config):
        self.config = config

    def _get_cert(self):
        # Safely get cert and key if present, else return None
        cert = getattr(self.config, 'cert', None)
        key = getattr(self.config, 'key', None)
        if cert and key:
            return (cert, key)
        return None

    def get(self, endpoint, params=None):
        import requests
        # If endpoint is a full URL, use it directly
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            url = endpoint
        else:
            url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        cert = self._get_cert()
        try:
            response = requests.get(url, headers=self.config.headers, params=params, timeout=self.config.timeout, cert=cert)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"GET request failed: {e}")
            return None

    def post(self, endpoint, data=None):
        import requests
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            url = endpoint
        else:
            url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        cert = self._get_cert()
        try:
            response = requests.post(url, headers=self.config.headers, json=data, timeout=self.config.timeout, cert=cert)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"POST request failed: {e}")
            return None

    def put(self, endpoint, data=None):
        import requests
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            url = endpoint
        else:
            url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        cert = self._get_cert()
        try:
            response = requests.put(url, headers=self.config.headers, json=data, timeout=self.config.timeout, cert=cert)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"PUT request failed: {e}")
            return None

    def delete(self, endpoint):
        import requests
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            url = endpoint
        else:
            url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        cert = self._get_cert()
        try:
            response = requests.delete(url, headers=self.config.headers, timeout=self.config.timeout, cert=cert)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"DELETE request failed: {e}")
            return None