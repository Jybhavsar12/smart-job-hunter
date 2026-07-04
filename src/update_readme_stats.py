"""Update the Stats section of README.md between STATS_START/STATS_END markers."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
JOBS_DIR = ROOT / "data" / "jobs"
APPS_FILE = ROOT / "data" / "applications" / "applications.json"

START = "<!-- STATS_START -->"
END = "<!-- STATS_END -->"


def collect_stats() -> dict:
    job_files = sorted(JOBS_DIR.glob("jobs_*.json"))
    total_jobs = 0
    latest = None
    for f in job_files:
        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        total_jobs += data.get("count", len(data.get("jobs", [])))
        latest = data

    best_match = None
    if latest and latest.get("jobs"):
        top = max(latest["jobs"], key=lambda j: j.get("match_score", 0))
        best_match = f"{top['title']} at {top['company']} (score {top.get('match_score', 0):.0f})"

    applications = 0
    if APPS_FILE.exists():
        try:
            applications = json.loads(APPS_FILE.read_text()).get("stats", {}).get("total", 0)
        except (json.JSONDecodeError, OSError):
            pass

    return {
        "runs": len(job_files),
        "total_jobs": total_jobs,
        "latest_date": latest.get("date", "n/a") if latest else "n/a",
        "latest_count": latest.get("count", 0) if latest else 0,
        "best_match": best_match or "n/a",
        "applications": applications,
    }


def render(stats: dict) -> str:
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return "\n".join([
        START,
        f"**Last updated:** {updated}",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Search runs | {stats['runs']} |",
        f"| Jobs found (all time) | {stats['total_jobs']} |",
        f"| Jobs found (latest run, {stats['latest_date']}) | {stats['latest_count']} |",
        f"| Best match (latest run) | {stats['best_match']} |",
        f"| Applications tracked | {stats['applications']} |",
        END,
    ])


def main():
    readme = README.read_text()
    if START not in readme or END not in readme:
        raise SystemExit("STATS markers not found in README.md")
    block = render(collect_stats())
    updated = re.sub(re.escape(START) + r".*?" + re.escape(END), block, readme, flags=re.DOTALL)
    README.write_text(updated)
    print("README stats updated")


if __name__ == "__main__":
    main()
