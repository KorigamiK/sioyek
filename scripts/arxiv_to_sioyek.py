#!/usr/bin/env python3
"""Save an arXiv paper under its title and open the local PDF in Sioyek."""

import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit


CONFIG = Path.home() / ".config/sioyek/arxiv.json"
ARXIV_ID = r"(?:\d{4}\.\d{4,5}|[a-zA-Z][a-zA-Z.-]*/\d{7})(?:v[1-9]\d*)?"


def paper_id(value):
    url = urlsplit(value)
    if url.scheme == "sioyek-arxiv":
        if url.netloc != "open":
            raise ValueError("Expected sioyek-arxiv://open?url=...")
        value = parse_qs(url.query).get("url", [""])[0]
        url = urlsplit(value)
    if (url.scheme not in ("https", "http")
            or url.hostname not in ("arxiv.org", "www.arxiv.org", "export.arxiv.org")
            or url.username or url.password or url.port not in (None, 80, 443)):
        raise ValueError("Open an arXiv abstract, HTML, or PDF page first.")
    match = re.fullmatch(r"/(?:abs|pdf|html)/(" + ARXIV_ID + r")(?:\.pdf)?/?",
                         unquote(url.path))
    if not match:
        raise ValueError("This URL does not identify an arXiv paper.")
    return match.group(1)


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and attrs.get("name") == "citation_title":
            self.title = attrs.get("content", "")
        if tag == "a":
            self.links.append(attrs.get("href", ""))


def fetch(url, destination):
    subprocess.run([
        "/usr/bin/curl", "--fail", "--location", "--silent", "--show-error",
        "--proto", "=https", "--proto-redir", "=https", "--connect-timeout", "15",
        "--max-time", "180", "--retry", "2", "--retry-delay", "2",
        "--output", str(destination), url,
    ], check=True)


def describe(identifier):
    with tempfile.TemporaryDirectory(prefix="sioyek-arxiv-") as temp:
        page = Path(temp) / "abstract.html"
        fetch("https://arxiv.org/abs/" + identifier, page)
        metadata = Metadata()
        metadata.feed(page.read_text(encoding="utf-8"))
    if not metadata.title.strip():
        raise ValueError("arXiv did not return a paper title. Please try again.")
    if not re.search(r"v\d+$", identifier):
        versions = []
        for link in metadata.links:
            match = re.fullmatch(r"/abs/" + re.escape(identifier) + r"v([1-9]\d*)",
                                 urlsplit(link).path)
            if match:
                versions.append(int(match.group(1)))
        if not versions:
            raise ValueError("Could not identify the paper version on arXiv.")
        identifier += "v" + str(max(versions))
    return " ".join(metadata.title.split()), identifier


def filename(title, identifier):
    title = unicodedata.normalize("NFC", title)
    title = re.sub(r'[\x00-\x1f\x7f/\\:*?"<>|]', "-", title).strip(" .")
    # Leave room for the identifier and .pdf within macOS's filename limit.
    title = title.encode("utf-8")[:180].decode("utf-8", errors="ignore").rstrip(" .")
    return f"{title or 'Paper'} [{identifier.replace('/', '_')}].pdf"


def is_pdf(path):
    if not path.is_file():
        return False
    with path.open("rb") as stream:
        return stream.read(5) == b"%PDF-"


def save_paper(url, directory):
    identifier = paper_id(url)
    title, identifier = describe(identifier)
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / filename(title, identifier)
    # Serialize repeated clicks, and never expose a partially downloaded PDF.
    with (directory / ".sioyek-arxiv.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if destination.exists():
            if is_pdf(destination):
                return destination
            raise ValueError(f"Existing file is not a PDF; move it aside first: {destination}")
        with tempfile.NamedTemporaryFile(dir=directory, prefix=".arxiv-", suffix=".part",
                                         delete=False) as stream:
            partial = Path(stream.name)
        try:
            fetch("https://arxiv.org/pdf/" + identifier, partial)
            if not is_pdf(partial):
                raise ValueError("arXiv returned something other than a PDF; nothing was saved.")
            # link() refuses to overwrite an existing file, even in a race.
            os.link(partial, destination)
        finally:
            partial.unlink(missing_ok=True)
    return destination


def notify_error(message):
    # Pass the message as argv rather than interpolating it into AppleScript.
    subprocess.run([
        "/usr/bin/osascript", "-e",
        'on run argv\ndisplay alert "Sioyek arXiv" message (item 1 of argv)\nend run',
        message,
    ], check=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="arXiv URL or sioyek-arxiv://open?url=...")
    parser.add_argument("--no-open", action="store_true", help="Download without opening Sioyek")
    parser.add_argument("--notify", action="store_true", help="Show errors in a macOS alert")
    args = parser.parse_args()
    try:
        config = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
        directory = Path(config.get("papers_dir", "~/Downloads/Papers")).expanduser()
        app = Path(config.get("sioyek_app", "~/Applications/sioyek.app")).expanduser()
        if not args.no_open and not app.is_dir():
            raise ValueError(f"Sioyek app not found at {app}. Set sioyek_app in {CONFIG}.")
        destination = save_paper(args.url, directory)
        print(destination, flush=True)
        if not args.no_open:
            subprocess.run(["/usr/bin/open", "-a", str(app), str(destination)], check=True)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        message = str(error)
        print(message, file=sys.stderr, flush=True)
        if args.notify:
            notify_error(message)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
