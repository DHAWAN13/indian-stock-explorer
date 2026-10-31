# Automated NSE/BSE security-master refresh

## What it does

- Runs on weekdays at 22:15 India Standard Time via GitHub Actions.
- Downloads the latest available NSE MII security file by trying recent dated URLs.
- Downloads BSE's `scrip.zip` and selects the newest `BSE_EQ_SCRIP_DDMMYYYY.csv` member.
- Validates required headers, file integrity, source age, and eligible equity-record counts.
- Writes compact dated files that retain the field names consumed by the existing `NSEProvider` and `BSEProvider` implementations.
- Keeps only the latest dated file for each exchange to limit repository growth.
- Updates `data/exchange/security_master_manifest.json` with source dates and counts.
- Leaves the existing data files untouched if either source cannot be downloaded or validated.
- Commits only when the data changes; Render can then deploy from the GitHub push.

## Manual test

From the repository root:

```powershell
python backend/scripts/refresh_exchange_data.py --dry-run
```

The dry run downloads and validates both sources but does not change files.

## Manual refresh

```powershell
python backend/scripts/refresh_exchange_data.py
```

Then inspect the diff and run backend tests before committing:

```powershell
git status --short
git diff --stat
.\.venv\Scripts\python.exe -m pytest
```

## GitHub Actions setup

1. Commit this script and workflow to the `main` branch.
2. In GitHub, open **Settings → Actions → General**.
3. Under **Workflow permissions**, allow the `GITHUB_TOKEN` to have read and write permissions if repository policy requires this setting.
4. Open **Actions → Refresh NSE and BSE security masters** and choose **Run workflow** for the first manual run.
5. Inspect the workflow logs and the generated commit.

The workflow explicitly requests `contents: write`; repository/organization policy can still restrict that permission.

## Notes

- The NSE endpoint follows the dated MII security-file naming convention.
- The BSE ZIP endpoint used here was manually verified from the development environment; source availability and anti-bot policy can change.
- This workflow refreshes the reference data; it does not guarantee that Yahoo Finance has a quote for every new listing.
- GitHub scheduled workflows use UTC cron. `16:45 UTC` is `22:15 IST` (the current cron `45 16 * * 1-5`).
