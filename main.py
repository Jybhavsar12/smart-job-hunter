#!/usr/bin/env python3
"""
Smart Job Hunter - Main entry point
Automated job searching, scoring, and application tracking
"""
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from auto_apply import AutoApply
from job_scorer import JobScorer
from tracker import ApplicationTracker


def main():
    parser = argparse.ArgumentParser(description="Smart Job Hunter - Find and apply to jobs")
    parser.add_argument("--search", action="store_true", help="Search for new jobs")
    parser.add_argument("--apply", action="store_true", help="Actually submit applications")
    parser.add_argument("--stats", action="store_true", help="Show application statistics")
    parser.add_argument("--daily", action="store_true", help="Run daily hunt routine")
    
    args = parser.parse_args()
    
    if args.stats:
        tracker = ApplicationTracker()
        print(tracker.summary())
        return
    
    if args.search or args.daily:
        hunter = AutoApply()
        hunter.run_daily_hunt(dry_run=not args.apply)
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
