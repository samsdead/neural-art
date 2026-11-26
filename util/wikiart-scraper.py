"""Download JPEGs listed in public WikiArt artist galleries."""

from html.parser import HTMLParser
import os
from pathlib import Path
import re
import sys
from tempfile import NamedTemporaryFile
from time import monotonic
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ARTIST_URL = "https://www.wikiart.org/en/{artist}/mode/allpaintings"
ARTISTS = ["pablo-picasso"]
IMAGE_DIR = Path(__file__).resolve().parent.parent / "wikiart"
MAX_PAGE_BYTES = 4 * 1024 * 1024
MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_PAINTINGS = 100


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Gallery(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "img" and attributes.get("src"):
            self.sources.append(attributes["src"])
        if attributes.get("ng-controller") == "MasonryCtrl":
            gallery = attributes.get("ng-init") or ""
            self.sources.extend(re.findall(r'"image"\s*:\s*"([^"]+)"', gallery))


def painting_link(source, artist):
    if not source:
        return None

    try:
        parts = urlsplit(source.partition("!")[0])
    except ValueError:
        return None

    if parts.scheme not in {"http", "https", ""} or not re.fullmatch(
        r"uploads[0-9]?\.wikiart\.org", parts.netloc, re.IGNORECASE
    ):
        return None

    image = re.fullmatch(
        rf"/(?:[0-9]+/)?images/{re.escape(artist)}/"
        r"([a-z0-9][a-z0-9_.-]{0,180}\.jpe?g)",
        parts.path,
        re.IGNORECASE,
    )
    if not image:
        return None

    filename = image.group(1)
    stem = filename.partition(".")[0].upper()
    if re.fullmatch(r"AUX|CON|NUL|PRN|(?:COM|LPT)[1-9]", stem):
        return None

    return urlunsplit(("https", parts.netloc.lower(), parts.path, "", "")), filename


def fetch(opener, url, media_type, max_bytes):
    request = Request(url, headers={"User-Agent": "neural-art-wikiart-client/1.0"})
    deadline = monotonic() + 45
    content = bytearray()
    with opener.open(request, timeout=10) as response:
        if response.status != 200 or response.headers.get_content_type() != media_type:
            raise ValueError("Unexpected response status or content type.")
        while True:
            if monotonic() >= deadline:
                raise ValueError("Response exceeded the download time limit.")
            chunk = response.read1(min(65536, max_bytes + 1 - len(content)))
            if not chunk:
                return content
            content.extend(chunk)
            if len(content) > max_bytes:
                raise ValueError("Response exceeded the download size limit.")


def save_painting(opener, url, destination):
    image = fetch(opener, url, "image/jpeg", MAX_IMAGE_BYTES)
    if not image.startswith(b"\xff\xd8\xff") or not image.endswith(b"\xff\xd9"):
        raise ValueError("Response did not have JPEG start and end markers.")

    temporary = None
    try:
        with NamedTemporaryFile(dir=destination.parent, delete=False) as output:
            temporary = Path(output.name)
            output.write(image)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def scrape_artist(opener, artist):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", artist):
        raise ValueError("ARTISTS entries must be WikiArt slugs.")
    url = ARTIST_URL.format(artist=artist)
    page = fetch(opener, url, "text/html", MAX_PAGE_BYTES)

    gallery = Gallery()
    gallery.feed(page.decode("utf-8", errors="replace"))
    gallery.close()
    links = {}
    for source in gallery.sources:
        link = painting_link(source, artist)
        if link:
            image_url, filename = link
            links.setdefault(filename, image_url)
    if not links:
        raise ValueError("The public gallery did not contain matching JPEG links.")

    directory = IMAGE_DIR / artist
    if IMAGE_DIR.is_symlink() or directory.is_symlink():
        raise ValueError("Image directory must not be a symbolic link.")
    directory.mkdir(parents=True, exist_ok=True)
    for index, (filename, image_url) in enumerate(links.items()):
        if index == MAX_PAINTINGS:
            break
        save_painting(opener, image_url, directory / filename)


def main():
    opener = build_opener(NoRedirects())
    try:
        for artist in ARTISTS:
            scrape_artist(opener, artist)
    except (OSError, ValueError) as error:
        print(f"wikiart-scraper.py: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
