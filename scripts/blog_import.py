# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-api-python-client>=2.100",
#     "google-auth>=2.23",
#     "Pillow>=10.0",
#     "pillow-heif>=0.16",
# ]
# ///
"""Import blog posts from the Google Form response sheet.

Each row with an empty Status cell becomes a post in _posts/, with its photos
resized into assets/media/img/posts/. See docs/blog-submissions.md.

    uv run scripts/blog_import.py --dry-run
    uv run scripts/blog_import.py --fixture scripts/fixtures/sample-rows.json --dry-run

Environment:
    BLOG_SHEET_ID        ID of the response sheet (required unless --fixture)
    BLOG_PUBLISH_MODE    "pr" (default) or "direct"
"""

from __future__ import annotations

import argparse
import html
import io
import json
import os
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from PIL import Image, ImageOps

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:  # HEIC support is optional
    pass

REPO = Path(__file__).resolve().parent.parent
POSTS_DIR = REPO / "_posts"
IMG_ROOT = REPO / "assets" / "media" / "img" / "posts"
IMG_URL_ROOT = "/assets/media/img/posts"

MISSIONS_DIR = REPO / "missions"
# Teams without a mission page
EXTRA_TEAMS = {"Podcast": "podcast", "General club news": "news"}


def load_teams() -> dict[str, str]:
    """Map Team dropdown labels to post categories, from each mission page's
    jumbotitle and news-cat."""
    teams = {}
    for page in sorted(MISSIONS_DIR.glob("*.html")):
        text = page.read_text()
        title = re.search(r'^jumbotitle:\s*"?(.*?)"?\s*$', text, re.MULTILINE)
        cat = re.search(r"^news-cat:\s*(\S+)", text, re.MULTILINE)
        if title and cat:
            teams[title.group(1)] = cat.group(1)
    teams.update(EXTRA_TEAMS)
    return teams


def resolve_category(team: str, teams: dict[str, str]) -> str:
    """Accept either a dropdown label ("Rockets") or a category ("rockets")."""
    if team in teams:
        return teams[team]
    if team in teams.values():
        return team
    raise ValueError(f"unknown team {team!r}")


# Sheet column headers, matching the Google Form questions.
COL_TIMESTAMP = "Timestamp"
COL_EMAIL = "Email Address"
COL_TITLE = "Title"
COL_TEAM = "Team"
COL_AUTHOR = "Author name"
COL_BODY = "Body"
COL_PHOTOS = "Photos"
COL_CAPTIONS = "Captions"
COL_SPOTIFY = "Spotify link"
COL_PUBLISH_DATE = "Publish date"
COL_STATUS = "Status"
COL_PR = "PR"
REQUIRED_COLS = [COL_TIMESTAMP, COL_TITLE, COL_TEAM, COL_AUTHOR, COL_BODY, COL_STATUS, COL_PR]

MAX_IMG_WIDTH = 1600
JPEG_QUALITY = 82
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]


@dataclass
class Submission:
    row_number: int
    values: dict[str, str]
    photos: list[str] = field(default_factory=list)

    def get(self, col: str) -> str:
        return (self.values.get(col) or "").strip()


def slugify(text: str, max_len: int = 50) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:max_len].rstrip("-") or "post"


def parse_date(value: str) -> date | None:
    value = value.strip()
    for fmt in ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def jekyll_date(d: date) -> str:
    # Match existing post filenames, e.g. 2024-9-8
    return f"{d.year}-{d.month}-{d.day}"


def sanitize_text(text: str) -> str:
    """Escape HTML and Liquid tags so submitted text can't change the page or break the build."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("<", "&lt;")
    text = re.sub(r"\{(?=[{%])", "&#123;", text)
    # Indented lines would render as code blocks
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def figure_html(src: str, caption: str) -> str:
    caption_html = ""
    if caption:
        caption_html = (
            "\n\t<div>\n    <figcaption class=\"text-center\">\n"
            f"      <b>{html.escape(caption)}</b>\n"
            "    </figcaption>\n  </div>"
        )
    return f'<p align="center">\n\t<img src="{src}">{caption_html}\n</p>'


SPOTIFY_URL = re.compile(
    r"^https://open\.spotify\.com/(?:intl-[a-z]+/)?(episode|show)/([A-Za-z0-9]+)(?:[?#].*)?$"
)


def spotify_embed(url: str) -> str:
    """Embed for a Spotify episode or show link."""
    if not url:
        return ""
    m = SPOTIFY_URL.match(url.strip())
    if not m:
        raise ValueError(f"not a Spotify episode/show link: {url[:80]!r}")
    kind, spotify_id = m.groups()
    return (
        '<p align="center">\n'
        f'\t<iframe src="https://open.spotify.com/embed/{kind}/{spotify_id}" '
        'width="100%" height="152" frameborder="0" allowfullscreen="" '
        'allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" '
        'loading="lazy"></iframe>\n'
        "</p>"
    )


PHOTO_MARKER = re.compile(r"\[photo\s*(\d+)\]", re.IGNORECASE)


def render_body(body: str, image_urls: list[str], captions: list[str]) -> str:
    """Place photo N at "[photo N]" in the body; unplaced photos go at the end."""
    body = sanitize_text(body)
    figures = [
        figure_html(url, captions[i] if i < len(captions) else "")
        for i, url in enumerate(image_urls)
    ]
    used: set[int] = set()

    def replace(m: re.Match) -> str:
        n = int(m.group(1))
        if 1 <= n <= len(figures) and n not in used:
            used.add(n)
            return f"\n\n{figures[n - 1]}\n\n"
        return ""

    body = PHOTO_MARKER.sub(replace, body)
    rest = [fig for i, fig in enumerate(figures, 1) if i not in used]
    parts = [body.strip()] + rest
    return re.sub(r"\n{3,}", "\n\n", "\n\n".join(p for p in parts if p)) + "\n"


def front_matter(title: str, d: date, category: str, author: str, submitted: str) -> str:
    q = lambda s: json.dumps(s, ensure_ascii=False)
    return (
        "---\n"
        "layout: post\n"
        f"title:  {q(title)}\n"
        f"date:   {jekyll_date(d)}\n"
        f"categories: {category}\n"
        f"author: {q(author)}\n"
        f"submission: {q(submitted)}\n"
        "---\n"
    )


def unique_stem(d: date, slug: str) -> str:
    base = f"{jekyll_date(d)}-{slug}"
    stem, n = base, 2
    while (POSTS_DIR / f"{stem}.markdown").exists() or (IMG_ROOT / stem).exists():
        stem, n = f"{base}-{n}", n + 1
    return stem


def save_image(data: bytes, dest: Path) -> None:
    with Image.open(io.BytesIO(data)) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        if im.width > MAX_IMG_WIDTH:
            im = im.resize(
                (MAX_IMG_WIDTH, round(im.height * MAX_IMG_WIDTH / im.width)),
                Image.LANCZOS,
            )
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Saving without exif= drops all metadata, including location
        im.save(dest, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)


def col_letter(index: int) -> str:
    letters = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


class FixtureSource:
    """Rows from a local JSON file, for testing. Photo values are local paths."""

    def __init__(self, path: Path):
        self.path = path
        rows = json.loads(path.read_text())
        self.submissions = []
        for i, values in enumerate(rows, start=2):
            photos = [p.strip() for p in (values.get(COL_PHOTOS) or "").split(",") if p.strip()]
            self.submissions.append(Submission(i, values, photos))

    def pending(self) -> list[Submission]:
        return [s for s in self.submissions if not s.get(COL_STATUS)]

    def fetch_photo(self, ref: str) -> bytes:
        return (self.path.parent / ref).read_bytes()

    def mark(self, sub: Submission, status: str, pr: str = "") -> None:
        print(f"  [fixture] row {sub.row_number}: Status={status!r} PR={pr!r}")


def google_credentials():
    """Application default credentials, or a key file in GOOGLE_SERVICE_ACCOUNT_JSON."""
    key = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if key:
        from google.oauth2 import service_account

        info = json.loads(key) if key.lstrip().startswith("{") else json.loads(Path(key).read_text())
        return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

    import google.auth
    from google.auth.exceptions import DefaultCredentialsError

    try:
        creds, _ = google.auth.default(scopes=SCOPES)
    except DefaultCredentialsError:
        raise SystemExit(
            "No Google credentials found. Run:\n"
            "  gcloud auth application-default login --impersonate-service-account=<service account>"
        )
    return creds


class SheetSource:
    def __init__(self, sheet_id: str):
        from googleapiclient.discovery import build

        creds = google_credentials()
        self.sheets = build("sheets", "v4", credentials=creds, cache_discovery=False)
        self.drive = build("drive", "v3", credentials=creds, cache_discovery=False)
        self.sheet_id = sheet_id

        meta = self.sheets.spreadsheets().get(spreadsheetId=sheet_id).execute()
        self.tab = meta["sheets"][0]["properties"]["title"]
        rows = (
            self.sheets.spreadsheets().values()
            .get(spreadsheetId=sheet_id, range=f"'{self.tab}'")
            .execute()
            .get("values", [])
        )
        if not rows:
            raise SystemExit("Response sheet is empty.")
        self.headers = [h.strip() for h in rows[0]]
        missing = [c for c in REQUIRED_COLS if c not in self.headers]
        if missing:
            raise SystemExit(f"Sheet is missing columns: {', '.join(missing)}")

        self.submissions = []
        for i, row in enumerate(rows[1:], start=2):
            values = dict(zip(self.headers, row))
            if not (values.get(COL_TIMESTAMP) or "").strip():
                continue
            ids = re.findall(r"[?&]id=([\w-]+)", values.get(COL_PHOTOS) or "")
            self.submissions.append(Submission(i, values, ids))

    def pending(self) -> list[Submission]:
        return [s for s in self.submissions if not s.get(COL_STATUS)]

    def fetch_photo(self, file_id: str) -> bytes:
        from googleapiclient.http import MediaIoBaseDownload

        buf = io.BytesIO()
        request = self.drive.files().get_media(fileId=file_id, supportsAllDrives=True)
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buf.getvalue()

    def mark(self, sub: Submission, status: str, pr: str = "") -> None:
        status_col = col_letter(self.headers.index(COL_STATUS))
        pr_col = col_letter(self.headers.index(COL_PR))
        self.sheets.spreadsheets().values().batchUpdate(
            spreadsheetId=self.sheet_id,
            body={
                "valueInputOption": "RAW",
                "data": [
                    {"range": f"'{self.tab}'!{status_col}{sub.row_number}", "values": [[status]]},
                    {"range": f"'{self.tab}'!{pr_col}{sub.row_number}", "values": [[pr]]},
                ],
            },
        ).execute()


def build_post(source, sub: Submission) -> tuple[str, list[Path]]:
    """Write the post and its photos. Returns the filename stem and the paths written."""
    title = sub.get(COL_TITLE)
    category = resolve_category(sub.get(COL_TEAM), load_teams())
    author = sub.get(COL_AUTHOR)
    body = sub.get(COL_BODY)
    if not title or not body:
        raise ValueError("title and body are required")
    episode = spotify_embed(sub.get(COL_SPOTIFY))

    d = parse_date(sub.get(COL_PUBLISH_DATE)) or parse_date(sub.get(COL_TIMESTAMP))
    if d is None:
        raise ValueError(f"can't parse date {sub.get(COL_TIMESTAMP)!r}")

    stem = unique_stem(d, slugify(title))
    written: list[Path] = []
    image_urls = []
    for n, ref in enumerate(sub.photos, start=1):
        dest = IMG_ROOT / stem / f"{n}.jpg"
        save_image(source.fetch_photo(ref), dest)
        written.append(dest)
        image_urls.append(f"{IMG_URL_ROOT}/{stem}/{n}.jpg")

    captions = [c.strip() for c in sub.get(COL_CAPTIONS).splitlines() if c.strip()]
    post = POSTS_DIR / f"{stem}.markdown"
    post.write_text(
        front_matter(title, d, category, author, sub.get(COL_TIMESTAMP))
        + (f"{episode}\n\n" if episode else "")
        + render_body(body, image_urls, captions)
    )
    written.insert(0, post)
    return stem, written


def set_repo(path: Path) -> None:
    """Work in another checkout of the site."""
    global REPO, POSTS_DIR, IMG_ROOT, MISSIONS_DIR
    REPO = path.resolve()
    if not (REPO / "_config.yml").exists():
        raise SystemExit(f"{REPO} doesn't look like the site repo (no _config.yml).")
    POSTS_DIR = REPO / "_posts"
    IMG_ROOT = REPO / "assets" / "media" / "img" / "posts"
    MISSIONS_DIR = REPO / "missions"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()


def open_pr(sub: Submission, stem: str, written: list[Path], base_ref: str) -> str:
    branch = f"blog/{stem}"
    title = sub.get(COL_TITLE)
    git("add", "--", *[str(p.relative_to(REPO)) for p in written])
    git("commit", "-m", f"Add blog post: {title}")
    git("push", "-u", "origin", branch)
    # The repo is public, so leave the submitter's email out
    body = (
        f"Blog submission from the Google Form.\n\n"
        f"- **Author:** {sub.get(COL_AUTHOR)}\n"
        f"- **Team:** {sub.get(COL_TEAM)}\n"
        f"- **Submitted:** {sub.get(COL_TIMESTAMP)} (sheet row {sub.row_number})\n"
        f"- **Photos:** {len(written) - 1}\n\n"
        "Before merging, check the text for typos and formatting, and check that the "
        "photos and captions are appropriate. Merging publishes the post."
    )
    return subprocess.run(
        ["gh", "pr", "create", "--base", base_ref, "--head", branch,
         "--title", f"Blog post: {title}", "--body", body],
        cwd=REPO, check=True, capture_output=True, text=True,
    ).stdout.strip().splitlines()[-1]


def publish_direct(sub: Submission, written: list[Path], base_ref: str) -> str:
    """Commit the post directly to the base branch. Returns the commit URL."""
    git("add", "--", *[str(p.relative_to(REPO)) for p in written])
    git("commit", "-m", f"Add blog post: {sub.get(COL_TITLE)}",
        "-m", f"From the blog Google Form (sheet row {sub.row_number}).")
    git("push", "origin", f"HEAD:refs/heads/{base_ref}")
    sha = git("rev-parse", "HEAD")
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", git("remote", "get-url", "origin"))
    return f"https://github.com/{m.group(1)}/commit/{sha}" if m else sha


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="write files only, without git or sheet updates")
    parser.add_argument("--fixture", type=Path, help="read rows from a JSON file instead of the sheet")
    parser.add_argument("--limit", type=int, default=0, help="process at most N rows")
    parser.add_argument("--base", default="master", help="branch to publish to")
    parser.add_argument("--repo", type=Path, help="checkout of the site to use (default: this one)")
    parser.add_argument("--mode", choices=["pr", "direct"],
                        default=os.environ.get("BLOG_PUBLISH_MODE", "pr"),
                        help="open a PR per post, or commit directly to --base")
    parser.add_argument("--list-teams", action="store_true", help="print the Team dropdown options")
    args = parser.parse_args()

    if args.repo:
        set_repo(args.repo)
    mode = args.mode

    if args.list_teams:
        for label, category in load_teams().items():
            print(f"{label}\t({category})")
        return 0

    if args.fixture:
        source = FixtureSource(args.fixture.resolve())
    else:
        sheet_id = os.environ.get("BLOG_SHEET_ID")
        if not sheet_id:
            raise SystemExit("Set BLOG_SHEET_ID to the response sheet's ID.")
        source = SheetSource(sheet_id)

    pending = source.pending()
    if args.limit:
        pending = pending[: args.limit]
    print(f"{len(pending)} pending submission(s)" + ("" if args.dry_run else f", mode: {mode}"))

    start = orig_branch = None
    if not args.dry_run:
        # Each row is cleaned up with reset/clean, so don't run over local changes
        if git("status", "--porcelain", "--untracked-files=no") or git(
            "status", "--porcelain", "--", "_posts", str(IMG_ROOT.relative_to(REPO))
        ):
            raise SystemExit("Working tree has uncommitted changes; refusing to create branches.")
        orig_branch = git("rev-parse", "--abbrev-ref", "HEAD")
        git("fetch", "--quiet", "origin", args.base)
        start = git("rev-parse", f"origin/{args.base}")

    failures = 0
    for sub in pending:
        label = f"row {sub.row_number} ({sub.get(COL_TITLE)!r})"
        try:
            if args.dry_run:
                stem, written = build_post(source, sub)
                print(f"  {label}: wrote {', '.join(str(p.relative_to(REPO)) for p in written)}")
                continue
            # PRs all branch from the same commit; direct commits stack
            git("switch", "--quiet", "--detach", start)
            try:
                stem, written = build_post(source, sub)
                if mode == "direct":
                    url = publish_direct(sub, written, args.base)
                    start = git("rev-parse", "HEAD")
                else:
                    git("switch", "--quiet", "-c", f"blog/{stem}")
                    url = open_pr(sub, stem, written, args.base)
            finally:
                git("reset", "--quiet", "--hard", "HEAD")
                git("clean", "-fdq", "--", "_posts", str(IMG_ROOT.relative_to(REPO)))
                git("switch", "--quiet", "--detach", start)
            source.mark(sub, "published" if mode == "direct" else "imported", url)
            print(f"  {label}: {url}")
        except Exception as e:
            failures += 1
            msg = f"error: {e}"[:200]
            print(f"  {label}: {msg}", file=sys.stderr)
            if not args.dry_run:
                try:
                    source.mark(sub, msg)
                except Exception as mark_err:
                    print(f"    (could not update sheet: {mark_err})", file=sys.stderr)

    if orig_branch and orig_branch != "HEAD":
        git("switch", "--quiet", orig_branch)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
