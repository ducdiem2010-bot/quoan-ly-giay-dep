import tempfile
import unittest
from pathlib import Path
from app import create_app

class DiscoveryRoutesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nhom6_discovery_")
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-discovery-secret",
                              "DATABASE": str(Path(self.temp.name) / "test.sqlite3")})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_collection_page(self):
        response = self.client.get("/collections")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Bộ sưu tập giày".encode(), response.data)

    def test_recommendations_page(self):
        response = self.client.get("/recommendations")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Gợi ý sản phẩm".encode(), response.data)

if __name__ == "__main__":
    unittest.main()
