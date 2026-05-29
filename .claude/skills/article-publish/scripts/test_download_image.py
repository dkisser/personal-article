"""Tests for download_image.py."""

import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from download_image import infer_extension, generate_filename, download_image


class TestInferExtension(unittest.TestCase):
    """Tests for infer_extension()."""

    def test_from_content_type_png(self):
        """Infer .png from Content-Type header."""
        headers = {"Content-Type": "image/png"}
        self.assertEqual(infer_extension(headers, "http://example.com/img"), ".png")

    def test_from_content_type_jpeg(self):
        """Infer .jpg from image/jpeg Content-Type header."""
        headers = {"Content-Type": "image/jpeg"}
        self.assertEqual(infer_extension(headers, "http://example.com/img"), ".jpg")

    def test_from_url_path_with_query(self):
        """Infer extension from URL path with query params."""
        headers = {}
        url = "http://example.com/photo.png?size=large&format=raw"
        self.assertEqual(infer_extension(headers, url), ".png")

    def test_fallback_bin(self):
        """Fallback to .bin when no extension can be inferred."""
        headers = {}
        url = "http://example.com/image"
        self.assertEqual(infer_extension(headers, url), ".bin")

    def test_content_type_priority_over_url(self):
        """Content-Type takes priority over URL path."""
        headers = {"Content-Type": "image/webp"}
        url = "http://example.com/photo.png"
        self.assertEqual(infer_extension(headers, url), ".webp")


class TestGenerateFilename(unittest.TestCase):
    """Tests for generate_filename()."""

    def test_empty_dir(self):
        """Generate first filename in empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_filename(tmpdir, ".png")
            self.assertEqual(os.path.basename(result), "image-1.png")

    def test_existing_files(self):
        """Skip existing files and generate next sequential filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "image-1.png"), "w").close()
            open(os.path.join(tmpdir, "image-2.png"), "w").close()
            result = generate_filename(tmpdir, ".png")
            self.assertEqual(os.path.basename(result), "image-3.png")

    def test_mixed_extensions(self):
        """Only consider files matching the target extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "image-1.jpg"), "w").close()
            result = generate_filename(tmpdir, ".png")
            self.assertEqual(os.path.basename(result), "image-1.png")


class TestDownloadImage(unittest.TestCase):
    """Tests for download_image()."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmpdir))

    @patch("download_image.requests.get")
    def test_successful_download(self, mock_get):
        """Download succeeds and saves file."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "image/png"}
        mock_response.content = b"fake-image-data"
        mock_get.return_value = mock_response

        result = download_image("http://example.com/img.png", self.tmpdir)

        self.assertTrue(os.path.exists(result))
        self.assertEqual(os.path.basename(result), "image-1.png")
        with open(result, "rb") as f:
            self.assertEqual(f.read(), b"fake-image-data")

    @patch("download_image.requests.get")
    def test_skip_existing_same_size(self, mock_get):
        """Skip download if file with same size already exists."""
        existing_path = os.path.join(self.tmpdir, "image-1.png")
        with open(existing_path, "wb") as f:
            f.write(b"fake-image-data")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "image/png"}
        mock_response.content = b"fake-image-data"
        mock_get.return_value = mock_response

        result = download_image("http://example.com/img.png", self.tmpdir)

        self.assertEqual(result, existing_path)
        mock_get.assert_called_once()

    @patch("download_image.requests.get")
    def test_network_failure(self, mock_get):
        """Handle network failure after retries."""
        mock_get.side_effect = Exception("Connection refused")

        result = download_image("http://example.com/img.png", self.tmpdir)

        self.assertIsNone(result)
        self.assertEqual(mock_get.call_count, 3)


if __name__ == "__main__":
    unittest.main()
