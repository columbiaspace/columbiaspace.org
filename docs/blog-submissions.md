# Blog submissions

Officers submit posts through the club's blog Google Form. Once a day a GitHub Action ([`.github/workflows/blog-import.yml`](../.github/workflows/blog-import.yml)) runs [`scripts/blog_import.py`](../scripts/blog_import.py), which turns each new response into a post:

1. Writes `_posts/YYYY-M-D-title.markdown`.
2. Downloads the photos, resizes them to 1600px wide, strips their metadata (including location), and saves them in `assets/media/img/posts/`.
3. Opens a pull request with the post.
4. Marks the row in the response sheet as `imported` with a link to the PR.

Merging the PR publishes the post, so check the text and photos first.

## How it's set up

The form, the response sheet and the Google Cloud project all belong to the club Google account. The webmaster has the project details.

The script reads the sheet as a Google service account. The response sheet is shared with it as Editor and the form's upload folder as Viewer, and it can't see anything else in the club's Drive.

There are no keys or passwords. GitHub Actions logs in to Google with Workload Identity Federation, which only trusts this repository's `master` branch. Locally, the webmaster's own Google account is allowed to act as the service account.

The Action needs three repository secrets (Settings > Secrets and variables > Actions). It skips itself if they're missing.

| Secret | Value |
|---|---|
| `BLOG_SHEET_ID` | The response sheet's ID, from its URL between `/d/` and `/edit` |
| `GCP_SERVICE_ACCOUNT` | The service account's email |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/<project number>/locations/global/workloadIdentityPools/<pool>/providers/<provider>` |

An org admin also needs to check Settings > Actions > General > "Allow GitHub Actions to create and approve pull requests".

## The form

The script reads the sheet by column header, so the question titles have to match exactly.

| Question | Type | Notes |
|---|---|---|
| Title | Short answer | Required |
| Team | Dropdown | Required. One option per line of `uv run scripts/blog_import.py --list-teams` |
| Author name | Short answer | Required |
| Body | Paragraph | Required. Help text: "Leave a blank line between paragraphs. Type [photo 2] where you want photo 2 to appear; other photos go at the end." |
| Photos | File upload | Images only, up to 10 files, 10 MB each |
| Captions | Paragraph | "One caption per line, in the same order as your photos." |
| Spotify link | Short answer | For podcast posts. Adds the Spotify player |
| Publish date | Date | Optional, defaults to the submission date |

Email collection is set to Verified. The sheet has two extra columns after `Publish date`, `Status` and `PR`, which the script fills in.

The Team list comes from the mission pages (each page's `jumbotitle` and `news-cat`), plus Podcast and General club news. To add a mission, create its page and add its `jumbotitle` to the dropdown. To retire one, move its page to `missions/past-missions/` and remove it from the dropdown.

## Reviewing posts

- New PRs are titled "Blog post: ...". Edit on the PR branch if needed, then merge. To reject one, close the PR and delete its branch.
- To import right away instead of waiting for the daily run, use Actions > Import blog submissions > Run workflow.
- Submitters' emails stay in the sheet and never go into the PR, since the repo is public.
- If a row says `error: ...`, fix the problem (for example, pick a valid Team in the sheet) and clear its Status cell so the next run tries again. If a `blog/...` branch was already pushed for it, delete that branch first.
- To skip a row, type anything in its Status cell.

## Running it locally

Install the Google Cloud CLI and log in as the service account. This only works once the webmaster has given your Google account permission.

```bash
brew install --cask google-cloud-sdk
gcloud auth application-default login --impersonate-service-account=<service account email>
export BLOG_SHEET_ID=<sheet id>
```

Then:

```bash
# Sample data, no Google access needed. Delete the files it writes afterwards.
uv run scripts/blog_import.py --fixture scripts/fixtures/sample-rows.json --dry-run

# The real sheet, without committing anything or updating the sheet
uv run scripts/blog_import.py --dry-run
```

Without `--dry-run` it does what the Action does: commits, pushes, opens PRs and updates the sheet. It needs the `gh` CLI logged in. Run it in a separate clean checkout of `master` so your own work isn't touched:

```bash
git worktree add --detach ../columbiaspace.org-publish origin/master
uv run scripts/blog_import.py --repo ../columbiaspace.org-publish
```

`--mode direct` (or `BLOG_PUBLISH_MODE=direct`) commits posts straight to `master` instead of opening PRs. Only use it while the form is limited to officers.

## Handing off

When the webmaster changes:

1. Add the new webmaster as an editor on the form and response sheet.
2. In the club's Google Cloud project, give their Google account the Service Account Token Creator role on the service account (IAM & Admin > Service Accounts > Permissions), and remove the old webmaster's.
3. Make sure they can merge PRs here, and that someone on the current board is an owner of the `columbiaspace` GitHub org.
4. Hand over the Google Cloud setup notes and project details.

Nothing needs to be rotated, since there are no keys.
