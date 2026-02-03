import requests
import json
from typing import Dict, Any, Optional

class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000/api", token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({'Authorization': f'Token {token}'})

    def set_token(self, token: str):
        self.token = token
        self.session.headers.update({'Authorization': f'Token {token}'})

    def login(self, username: str, password: str) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/token/"
        response = self.session.post(url, json={"username": username, "password": password})
        response.raise_for_status()
        data = response.json()
        self.set_token(data.get('token'))
        return data

    def register(self, username: str, password: str) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/register/"
        response = self.session.post(url, json={"username": username, "password": password})
        response.raise_for_status()
        return response.json()

    def get_datasets(self) -> Dict[str, Any]:
        url = f"{self.base_url}/datasets/"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def upload_dataset(self, file_path: str) -> Dict[str, Any]:
        url = f"{self.base_url}/upload/"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self.session.post(url, files=files)
        response.raise_for_status()
        return response.json()

    def get_dataset_health(self, dataset_id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/datasets/{dataset_id}/health/"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_dataset_rows(self, dataset_id: int, limit: int = 500, offset: int = 0) -> Dict[str, Any]:
        url = f"{self.base_url}/datasets/{dataset_id}/rows/"
        params = {'limit': limit, 'offset': offset}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_quality_metrics(self, dataset_id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/datasets/{dataset_id}/quality_metrics/"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def generate_report(self, dataset_id: int) -> bytes:
        url = f"{self.base_url}/datasets/{dataset_id}/report/"
        response = self.session.get(url)
        response.raise_for_status()
        return response.content
