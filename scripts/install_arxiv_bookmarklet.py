#!/usr/bin/env python3
"""Install the macOS arXiv URL handler and generate a Firefox bookmarklet page."""

import argparse
import html
import json
import plistlib
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


def applescript_string(value):
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--papers-dir", default="~/Downloads/Papers")
    parser.add_argument("--sioyek-app", default="~/Applications/sioyek.app")
    args = parser.parse_args()
    directory = Path(args.papers_dir).expanduser().resolve()
    sioyek = Path(args.sioyek_app).expanduser().resolve()
    if not sioyek.is_dir():
        parser.error(f"Sioyek app not found: {sioyek}")
    support = Path.home() / "Library/Application Support/Sioyek arXiv"
    support.mkdir(parents=True, exist_ok=True)
    helper = support / "arxiv_to_sioyek.py"
    shutil.copy2(Path(__file__).with_name("arxiv_to_sioyek.py"), helper)
    config_path = Path.home() / ".config/sioyek/arxiv.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    config.update(papers_dir=str(directory), sioyek_app=str(sioyek))
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    directory.mkdir(parents=True, exist_ok=True)
    log = support / "download.log"
    command = shlex.join([sys.executable, str(helper), "--notify"])
    source = support / "handler.applescript"
    source.write_text(
        "on open location incomingURL\n"
        "    do shell script " + applescript_string(command + " ")
        + " & quoted form of incomingURL & "
        + applescript_string(" >> " + shlex.quote(str(log)) + " 2>&1 < /dev/null &")
        + "\nend open location\n"
    )
    app = Path.home() / "Applications/Sioyek arXiv.app"
    app.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["/usr/bin/osacompile", "-o", str(app), str(source)], check=True)
    plist = app / "Contents/Info.plist"
    info = plistlib.loads(plist.read_bytes())
    info.update(
        CFBundleIdentifier="local.sioyek.arxiv",
        CFBundleName="Sioyek arXiv",
        LSUIElement=True,
        CFBundleURLTypes=[dict(CFBundleURLName="Sioyek arXiv",
                              CFBundleURLSchemes=["sioyek-arxiv"],
                              CFBundleTypeRole="Viewer")],
    )
    plist.write_bytes(plistlib.dumps(info))
    subprocess.run(["/usr/bin/codesign", "--force", "--sign", "-", str(app)], check=True)
    subprocess.run([
        "/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister",
        "-f", str(app),
    ], check=True)
    bookmarklet = (
        "javascript:(()=>{if(!/^(www\\.|export\\.)?arxiv\\.org$/.test(location.hostname))"
        "{alert('Open an arXiv paper page first.');return;}"
        "location.href='sioyek-arxiv://open?url='+encodeURIComponent(location.href);})()"
    )
    (support / "bookmarklet.txt").write_text(bookmarklet + "\n")
    page = support / "bookmarklet.html"
    page.write_text(
        '<!doctype html><meta charset="utf-8"><title>arXiv → Sioyek</title>'
        '<style>body{font:18px system-ui;max-width:740px;margin:70px auto;line-height:1.6;'
        'padding:0 24px}a{display:inline-block;padding:12px 18px;background:#2456b8;'
        'color:white;border-radius:8px}textarea{width:100%;height:130px}</style>'
        '<h1>arXiv → Sioyek</h1><p>Drag this button onto your Firefox bookmarks toolbar:</p>'
        '<p><a href="' + html.escape(bookmarklet, quote=True) + '">Open in Sioyek</a></p>'
        '<p>On an arXiv abstract or HTML paper page, click the bookmark. '
        'Allow Firefox to open <b>Sioyek arXiv</b> when prompted. '
        'The paper is saved in <code>' + html.escape(str(directory)) + '</code> '
        'with its title and version, then opened in Sioyek.</p>'
        '<p>If the toolbar is hidden, press <b>⌘⇧B</b>. '
        'Alternatively, create a bookmark and paste this into its URL field:</p>'
        '<textarea readonly>' + html.escape(bookmarklet) + '</textarea>'
        '<p>Firefox’s PDF viewer may restrict bookmarklets; use the paper’s abstract page '
        'if clicking from a PDF does not work.</p>'
    )
    print(f"Installed: {app}\nPapers: {directory}\nBookmarklet page: {page}\nConfig: {config_path}")


if __name__ == "__main__":
    main()
