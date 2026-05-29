#!/usr/bin/env python3
"""Download external images from articles to local storage."""

import os
import sys
import time
import mimetypes

import requests

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

CONNECT_TIMEOUT = 10
READ_TIMEOUT = 30

RETRY_DELAYS = [1, 2, 4]


def infer_extension(headers: dict, url: str) -> str:
    """Infer file extension from Content-Type header or URL path.

    Priority 1: Content-Type header (e.g. image/png -> .png)
    Priority 2: URL path (e.g. /photo.png?size=large -> .png)
    Fallback: .bin
    """
    content_type = headers.get("Content-Type", "")
    if content_type:
        content_type = content_type.split(";")[0].strip()
        ext = mimetypes.guess_extension(content_type)
        if ext:
            if ext == ".jpe":
                return ".jpg"
            return ext

    parsed = url.split("?")[0]
    _, ext = os.path.splitext(parsed)
    if ext:
        return ext.lower()

    return ".bin"


def generate_filename(output_dir: str, ext: str) -> str:
    """Generate sequential filename, skipping existing files.

    Returns absolute path like /path/to/dir/image-3.png
    """
    n = 1
    while True:
        candidate = os.path.join(output_dir, f"image-{n}{ext}")
        if not os.path.exists(candidate):
            return candidate
        n += 1


def _log(level: str, message: str) -> None:
    """Log to stderr."""
    print(f"[{level}] {message}", file=sys.stderr)


def download_image(url: str, output_dir: str) -> str | None:
    """Download image from URL to output_dir.

    Returns the absolute path of the saved file, or None on failure.
    """
    os.makedirs(output_dir, exist_ok=True)

    for attempt, delay in enumerate(RETRY_DELAYS):
        try:
            response = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            response.raise_for_status()
            break
        except Exception as e:
            _log("error", f"Attempt {attempt + 1} failed: {e}")
            if attempt < len(RETRY_DELAYS) - 1:
                time.sleep(delay)
            else:
                _log("error", "All retries exhausted")
                return None
    else:
        return None

    ext = infer_extension(response.headers, url)
    filepath = generate_filename(output_dir, ext)
    basename = os.path.basename(filepath)

    content = response.content
    content_length = len(content)

    for existing in os.listdir(output_dir):
        existing_path = os.path.join(output_dir, existing)
        if (
            os.path.isfile(existing_path)
            and os.path.getsize(existing_path) == content_length
        ):
            _log("skip", f"{basename} already exists as {existing}")
            return existing_path

    _log("download", f"{url} -> {basename}")
    with open(filepath, "wb") as f:
        f.write(content)

    _log("done", basename)
    return filepath


def main() -> int:
    """CLI entry point."""
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <url> <output_dir>", file=sys.stderr)
        return 1

    url = sys.argv[1]
    output_dir = sys.argv[2]

    result = download_image(url, output_dir)
    if result is None:
        return 1

    print(os.path.relpath(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
