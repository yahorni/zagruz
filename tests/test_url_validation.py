import unittest
from typing import override

from PyQt6.QtWidgets import QApplication

from src.zagruz.zagruz import DownloadApp


class TestURLValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qapp = QApplication.instance() or QApplication([])

    @override
    def setUp(self):
        self.app = DownloadApp(ui=False)

    def test_valid_urls(self):
        valid_urls = [
            "http://example.com",
            "https://www.example.com/path?query=param",
            "http://localhost:8080",
            "https://123.45.67.89",
            "http://example.co.uk",
            "https://youtube.com/watch?v=ABCD1234",
            "http://sub.domain.example.com/path/to/file.html",
            "https://user:pass@example.com:8080/path?query=param#fragment",
            "http://example.com#fragment"
        ]
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(self.app.validate_url(url))

    def test_invalid_urls(self):
        invalid_urls = [
            "ftp://example.com",
            "http://",
            "https://.com",
            "www.example.com",
            "javascript:alert(1)",
            "mailto:user@example.com",
            "http://example..com",
            "http://-example.com",
            "http://example.com/path with spaces"
        ]
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(self.app.validate_url(url))

    def test_edge_cases(self):
        edge_cases = [
            ("http://example.com", True),
            ("HTTP://EXAMPLE.COM", True),  # case insensitive
            ("https://example.com/?query=param&another=param", True),
            ("http://localhost:3000", True),
            ("http://192.168.1.1:8080/path", True),
            ("http://example.com/path/with/underscores_and-hyphens", True),
            ("http://example.com#fragment", True),
            ("http://example.com,", False),
            ("http://example.com\n", False),
            ("http:// example.com", False)
        ]
        for url, expected in edge_cases:
            with self.subTest(url=url):
                self.assertEqual(self.app.validate_url(url), expected)


if __name__ == '__main__':
    unittest.main()
