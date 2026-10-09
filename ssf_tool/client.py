import json
import urllib.parse
import urllib.request
import urllib.error
from typing import Any, Dict, Optional
import uuid

class ApiClientError(Exception):
    def __init__(self, status: int, message: str, payload: Any = None):
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.payload = payload

class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None

    def set_token(self, token: Optional[str]) -> None:
        self.token = token

    def _make_url(self, endpoint: str, query: Optional[Dict[str, Any]] = None) -> str:
        ep = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        url = f"{self.base_url}{ep}"
        if query:
            filtered = {k: v for k, v in query.items() if v is not None}
            if filtered:
                url += "?" + urllib.parse.urlencode(filtered)
        return url

    def request(self, method: str, endpoint: str, body: Optional[Dict[str, Any]] = None, query: Optional[Dict[str, Any]] = None) -> Any:
        url = self._make_url(endpoint, query)
        headers = {
            "Accept": "application/json",
            "User-Agent": "ssf-tool/1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        data_bytes = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data_bytes = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                if status == 204:
                    return None
                resp_bytes = resp.read()
                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type or "application/problem+json" in content_type:
                    return json.loads(resp_bytes.decode("utf-8"))
                return resp_bytes.decode("utf-8")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            err_json = None
            msg = e.reason
            try:
                err_json = json.loads(err_body)
                if isinstance(err_json, dict):
                    msg = err_json.get("detail") or err_json.get("error") or msg
            except Exception:
                pass
            raise ApiClientError(e.code, msg, err_json) from e
        except urllib.error.URLError as e:
            raise ApiClientError(0, f"No se pudo conectar a {self.base_url}: {e.reason}") from e

    def get(self, endpoint: str, query: Optional[Dict[str, Any]] = None) -> Any:
        return self.request("GET", endpoint, query=query)

    def post(self, endpoint: str, body: Optional[Dict[str, Any]] = None) -> Any:
        return self.request("POST", endpoint, body=body)

    def post_multipart(self, endpoint: str, field_name: str, filename: str, file_bytes: bytes, content_type: str = "image/png") -> Any:
        url = self._make_url(endpoint)
        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        
        body_parts = []
        body_parts.append(f"--{boundary}\r\n".encode("utf-8"))
        body_parts.append(
            f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8")
        )
        body_parts.append(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        body_parts.append(file_bytes)
        body_parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
        
        full_body = b"".join(body_parts)

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(full_body)),
            "Accept": "application/json",
            "User-Agent": "ssf-tool/1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        req = urllib.request.Request(url, data=full_body, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req) as resp:
                resp_bytes = resp.read()
                return json.loads(resp_bytes.decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            msg = e.reason
            try:
                err_json = json.loads(err_body)
                if isinstance(err_json, dict):
                    msg = err_json.get("detail") or err_json.get("error") or msg
            except Exception:
                pass
            raise ApiClientError(e.code, msg) from e
