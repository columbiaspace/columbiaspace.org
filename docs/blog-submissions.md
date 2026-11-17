# Blog submissions

Officers submit posts through the club's blog Google Form. Every day at 14:00 UTC, the [Import blog submissions](../.github/workflows/blog-import.yml) Action turns each new response into a pull request with the post and its photos, and marks the row `imported` in the response sheet. Merging the PR publishes the post.

## Setup

- The form, response sheet and Google Cloud project belong to the club Google account. The response sheet is shared with the project's service account as Editor, and the form's upload folder as Viewer.
- The Action logs in to Google without keys (Workload Identity Federation, trusted for this repo's `master` branch only). It needs the repository secrets `BLOG_SHEET_ID`, `GCP_SERVICE_ACCOUNT` and `GCP_WORKLOAD_IDENTITY_PROVIDER`, and skips itself if they're missing.
- When the webmaster changes, give the new one editor access to the form and sheet, and swap the Service Account Token Creator role in the Cloud project from the old webmaster to the new one. There are no keys to rotate.

## The form

Question titles must match exactly, since the script reads the sheet by column header. The sheet also needs `Status` and `PR` columns after `Publish date`.

| Question | Type | Notes |
|---|---|---|
| Title | Short answer | Required |
| Team | Dropdown | Required. Options from `uv run scripts/blog_import.py --list-teams` |
| Author name | Short answer | Required |
| Body | Paragraph | Required. "Type [photo 2] where you want photo 2 to appear." |
| Photos | File upload | Images, up to 10 |
| Captions | Paragraph | One per line, in photo order |
| Spotify link | Short answer | Optional, for podcast posts |
| Publish date | Date | Optional |

Teams come from the mission pages' `jumbotitle`, plus Podcast and General club news. When a mission is added or retired, update the dropdown.

## Reviewing

- Merge a "Blog post: ..." PR to publish it, or close it and delete its branch to reject it.
- To run the import now, use Actions > Import blog submissions > Run workflow.
- If a row shows `error: ...`, fix it and clear its Status cell to retry. Type anything in Status to skip a row.

## Running locally

```bash
uv run scripts/blog_import.py --fixture scripts/fixtures/sample-rows.json --dry-run
```

To read the real sheet, log in with `gcloud auth application-default login --impersonate-service-account=<service account>` (your account needs permission in the Cloud project), set `BLOG_SHEET_ID`, and add `--dry-run`.
