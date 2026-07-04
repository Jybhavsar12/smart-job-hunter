"""
Auto Apply - Automated job application system
Note: For LinkedIn Easy Apply, Indeed Quick Apply, etc., we prepare applications
and can integrate with browser automation (Selenium/Playwright) for actual submission
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from job_scorer import JobScorer
from job_sources import JobAggregator
from tracker import ApplicationTracker


def make_scorer(engine: str = "semantic"):
    """Build the configured scorer, falling back to keyword matching
    when sentence-transformers is unavailable."""
    if engine == "semantic":
        try:
            from semantic_scorer import SemanticScorer
            return SemanticScorer()
        except ImportError:
            print("⚠️  sentence-transformers not installed; using keyword scorer")
    return JobScorer()


class AutoApply:
    def __init__(self):
        self.config = self._load_config()
        self.scorer = make_scorer(self.config.get('scoring', {}).get('engine', 'semantic'))
        self.aggregator = JobAggregator()
        self.tracker = ApplicationTracker()
        
        # Settings
        self.min_score = 40  # Minimum score to consider applying
        self.max_daily_applications = 50
    
    def _load_config(self) -> Dict:
        config_path = Path(__file__).parent.parent / "config" / "profile.yaml"
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def search_and_score(self) -> List[Dict]:
        """Search for jobs and score them"""
        queries = self.config['preferences']['titles'][:5]  # Top 5 job titles
        
        print("🔍 Searching for jobs...")
        jobs = self.aggregator.search_all(queries)
        
        print("📊 Scoring jobs...")
        scored_jobs = self.scorer.rank_jobs(jobs)
        
        # Save to file
        self.aggregator.save_jobs(scored_jobs)
        
        return scored_jobs
    
    def get_apply_candidates(self, jobs: List[Dict]) -> List[Dict]:
        """Filter jobs that meet criteria for auto-apply"""
        candidates = []
        
        for job in jobs:
            score = job.get('match_score', 0)
            
            if score < self.min_score:
                continue
            
            # Check if already applied
            job_id = job.get('id', '')
            already_applied = any(
                app['job_id'] == job_id 
                for app in self.tracker.applications['applications']
            )
            
            if not already_applied:
                candidates.append(job)
        
        return candidates[:self.max_daily_applications]
    
    def prepare_application(self, job: Dict) -> Dict:
        """Prepare application data for a job"""
        profile = self.config['profile']
        
        application = {
            "job": job,
            "applicant": {
                "name": profile['name'],
                "email": profile['email'],
                "phone": profile['phone'],
                "linkedin": profile['linkedin'],
                "github": profile['github'],
                "portfolio": profile['portfolio']
            },
            "prepared_at": datetime.now().isoformat(),
            "status": "prepared"
        }
        
        return application
    
    def run_daily_hunt(self, dry_run: bool = True) -> Dict:
        """Run the daily job hunt routine"""
        print("=" * 50)
        print(f"🎯 Smart Job Hunter - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 50)
        
        # Search and score
        jobs = self.search_and_score()
        print(f"\n📋 Found {len(jobs)} jobs total")
        
        # Get candidates
        candidates = self.get_apply_candidates(jobs)
        print(f"✨ {len(candidates)} jobs meet criteria (score >= {self.min_score})")
        
        # Show top jobs
        print("\n🏆 Top 10 Job Matches:")
        for i, job in enumerate(candidates[:10], 1):
            print(f"  {i}. [{job['match_score']:.0f}] {job['title']} @ {job['company']}")
        
        results = {
            "date": datetime.now().isoformat(),
            "total_found": len(jobs),
            "candidates": len(candidates),
            "applied": 0,
            "top_jobs": candidates[:10]
        }
        
        if not dry_run:
            # Record applications (in real scenario, would submit via browser automation)
            for job in candidates[:self.max_daily_applications]:
                self.tracker.add_application(job, status="applied")
                results["applied"] += 1
        
        # Save daily stats
        self.tracker.save_daily_stats()
        
        # Save run results
        self._save_run_results(results)
        
        applied_count = results["applied"]
        if dry_run:
            print("\n🏃 DRY RUN - No applications submitted")
        else:
            print(f"\n✅ Applied to {applied_count} jobs")
        print(self.tracker.summary())
        
        return results
    
    def _save_run_results(self, results: Dict):
        """Save run results to file"""
        output_dir = Path("data/runs")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = output_dir / f"run_{date_str}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)


if __name__ == "__main__":
    import sys
    
    hunter = AutoApply()
    dry_run = "--apply" not in sys.argv
    hunter.run_daily_hunt(dry_run=dry_run)
