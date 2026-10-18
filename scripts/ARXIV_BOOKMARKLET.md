# arXiv → Sioyek on macOS

Click a Firefox bookmarklet on an arXiv abstract or HTML page to download the
PDF into `~/Downloads/Papers` with its title and version in the filename, then
open the local file in Sioyek. No extension or background server is required.

Install using the Python interpreter you want the handler to use:

```sh
python3 scripts/install_arxiv_bookmarklet.py
```

If needed, pass `--papers-dir /path/to/papers` or
`--sioyek-app /Applications/sioyek.app`.

Open `~/Library/Application Support/Sioyek arXiv/bookmarklet.html` in Firefox,
and drag **Open in Sioyek** to the bookmarks toolbar. Click it on an arXiv paper
page and allow Firefox to launch **Sioyek arXiv** when prompted. Firefox may
offer to remember this choice. If a bookmarklet does not run in Firefox's PDF
viewer, use the paper's `/abs/` page.

For example, a saved filename is:

```text
Attention Is All You Need [1706.03762v7].pdf
```

An unversioned link resolves the latest version listed on the abstract page.
An explicit version link keeps that version. Clicking again reuses the same
file. Downloads use a temporary file, and failed downloads do not create a
final PDF. Only arXiv paper URLs are accepted; arbitrary publisher pages and
papers requiring browser login are outside this helper's scope.

The installed helper is independent of this checkout. Settings live in
`~/.config/sioyek/arxiv.json`; change `papers_dir` or `sioyek_app` there.
Reopen the generated bookmarklet page after reinstalling if the folder changes.
The handler uses the Python interpreter that ran the installer; rerun it if
that interpreter is removed. Errors appear in a macOS alert and in
`~/Library/Application Support/Sioyek arXiv/download.log`.

You can also run it from a terminal:

```sh
python3 scripts/arxiv_to_sioyek.py https://arxiv.org/abs/1706.03762
python3 scripts/arxiv_to_sioyek.py --no-open https://arxiv.org/abs/1706.03762
```

To uninstall, remove the Firefox bookmark, `~/Applications/Sioyek arXiv.app`,
`~/Library/Application Support/Sioyek arXiv`, and `~/.config/sioyek/arxiv.json`.
Downloaded papers remain in the papers folder.
