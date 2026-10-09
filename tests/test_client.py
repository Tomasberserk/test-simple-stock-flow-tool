import unittest
from ssf_tool.client import ApiClient

class TestApiClient(unittest.TestCase):
    def test_url_construction(self):
        client = ApiClient("http://localhost:8000/api")
        url = client._make_url("/products", {"query": "martillo", "page": 1, "empty": None})
        self.assertEqual(url, "http://localhost:8000/api/products?query=martillo&page=1")

    def test_bearer_token_setting(self):
        client = ApiClient("http://localhost:8000")
        client.set_token("my-test-jwt")
        self.assertEqual(client.token, "my-test-jwt")

if __name__ == "__main__":
    unittest.main()
