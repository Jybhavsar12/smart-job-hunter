# Smart Job Hunter

Automated job searching, scoring, and application tracking system.

![Daily Hunt](https://github.com/Jybhavsar12/smart-job-hunter/actions/workflows/daily-hunt.yml/badge.svg)

## Features

- **Multi-source job search** - Aggregates jobs from RemoteOK, Arbeitnow, and more
- **Smart scoring** - Ranks jobs based on your profile match (skills, location, title)
- **Application tracking** - Track all applications, statuses, and responses
- **Auto-apply ready** - Prepared for browser automation integration
- **Daily automation** - GitHub Actions runs on a schedule and commits job data

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Search for jobs (dry run)
python main.py --daily

# View your stats
python main.py --stats
```

## How It Works

1. **Daily at 9 AM EST**: GitHub Actions triggers the job hunt
2. **Search**: Queries multiple job boards for relevant positions
3. **Score**: Each job is scored 0-100 based on your profile match
4. **Track**: Results saved to `data/` folder
5. **Commit**: Changes automatically committed to keep your GitHub active

## Configuration

Edit `config/profile.yaml` to customize:
- Your profile information
- Target job titles and locations
- Skills for matching
- Priority keywords
- Excluded companies

## Project Structure

```
smart-job-hunter/
├── config/
│   └── profile.yaml      # Your profile & preferences
├── data/
│   ├── jobs/             # Daily job listings
│   ├── applications/     # Application records
│   └── stats/            # Daily statistics
├── src/
│   ├── job_sources.py    # Job board integrations
│   ├── job_scorer.py     # Scoring algorithm
│   ├── tracker.py        # Application tracking
│   └── auto_apply.py     # Auto-apply engine
├── .github/workflows/
│   └── daily-hunt.yml    # GitHub Actions automation
└── main.py               # Entry point
```

## Stats

<!-- STATS_START -->
**Last updated:** 2026-07-06 09:52 UTC

| Metric | Value |
|--------|-------|
| Search runs | 25 |
| Jobs found (all time) | 130 |
| Jobs found (latest run, 2026-07-06) | 13 |
| Best match (latest run) | Full Stack Developer first UK at Better Futures Multi Academy Trust (score 43) |
| Applications tracked | 0 |
<!-- STATS_END -->

## License

MIT
