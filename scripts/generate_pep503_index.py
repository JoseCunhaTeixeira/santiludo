"""Generate/update a static PEP 503 "simple" package index for GitHub Pages.

Run from CI after a release's wheels are uploaded as GitHub Release assets.
Merges the current release's wheels into whatever index already exists on the
gh-pages branch (if any), so the index accumulates every release over time,
then writes the two static index.html files consuming repos' ``uv``/``pip``
point at.

Usage: python scripts/generate_pep503_index.py <repo> <tag> <dist_dir> <existing_index_dir> <out_dir>
"""

import hashlib
import html
import re
import sys
from pathlib import Path

PROJECT = "santiludo"


def main() -> None:
    repo, tag, dist_dir, existing_index_dir, out_dir = sys.argv[1:6]

    links: dict[str, str] = {}
    existing_index = Path(existing_index_dir) / "simple" / PROJECT / "index.html"
    if existing_index.exists():
        for m in re.finditer(r'href="([^"]+)"[^>]*>([^<]+)</a>', existing_index.read_text()):
            href, name = m.groups()
            links[name] = href

    for whl in sorted(Path(dist_dir).glob("*.whl")):
        sha256 = hashlib.sha256(whl.read_bytes()).hexdigest()
        url = f"https://github.com/{repo}/releases/download/{tag}/{whl.name}"
        links[whl.name] = f"{url}#sha256={sha256}"

    project_dir = Path(out_dir) / "simple" / PROJECT
    project_dir.mkdir(parents=True, exist_ok=True)

    rows = "\n".join(
        f'    <a href="{html.escape(href)}">{html.escape(name)}</a><br/>'
        for name, href in sorted(links.items())
    )
    (project_dir / "index.html").write_text(
        f"<!DOCTYPE html>\n<html>\n<body>\n{rows}\n</body>\n</html>\n"
    )

    root_dir = Path(out_dir) / "simple"
    (root_dir / "index.html").write_text(
        f'<!DOCTYPE html>\n<html>\n<body>\n    <a href="{PROJECT}/">{PROJECT}</a><br/>\n</body>\n</html>\n'
    )

    print(f"Wrote index for {len(links)} wheel(s) to {out_dir}/simple/")


if __name__ == "__main__":
    main()
