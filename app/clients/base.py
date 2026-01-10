"""Base HTTP client for external services"""
import httpx
from typing import Optional, Dict, Any
from app.config import settings


class BaseClient:
    """Base client for external service calls"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.timeout = settings.service_timeout
        self.max_retries = settings.service_max_retries
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        correlation_id: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}{endpoint}"
        
        request_headers = {
            "X-Correlation-ID": correlation_id,
            "Content-Type": "application/json"
        }
        if headers:
            request_headers.update(headers)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.request(
                        method=method,
                        url=url,
                        json=data,
                        params=params,
                        headers=request_headers
                    )
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPError as e:
                    if attempt == self.max_retries - 1:
                        raise Exception(f"Service call failed after {self.max_retries} attempts: {str(e)}")
                    continue
        
        raise Exception("Service call failed")
    
    async def get(self, endpoint: str, correlation_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request"""
        return await self._make_request("GET", endpoint, correlation_id, params=params)
    
    async def post(self, endpoint: str, correlation_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request"""
        return await self._make_request("POST", endpoint, correlation_id, data=data)
    
    async def put(self, endpoint: str, correlation_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make PUT request"""
        return await self._make_request("PUT", endpoint, correlation_id, data=data)
    
    async def delete(self, endpoint: str, correlation_id: str) -> Dict[str, Any]:
        """Make DELETE request"""
        return await self._make_request("DELETE", endpoint, correlation_id)
