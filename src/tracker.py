"""
Application Tracker - Tracks job applications and stats
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import hashlib


class ApplicationTracker:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.applications_file = self.data_dir / "applications" / "applications.json"
        self.stats_dir = self.data_dir / "stats"
        self._ensure_dirs()
        self.applications = self._load_applications()
    
    def _ensure_dirs(self):
        """Create necessary directories"""
        (self.data_dir / "applications").mkdir(parents=True, exist_ok=True)
        self.stats_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_applications(self) -> Dict:
        """Load existing applications"""
        if self.applications_file.exists():
            with open(self.applications_file, 'r') as f:
                return json.load(f)
        return {"applications": [], "stats": {"total": 0, "by_status": {}}}
    
    def _save_applications(self):
        """Save applications to file"""
        with open(self.applications_file, 'w') as f:
            json.dump(self.applications, f, indent=2)
    
    def _generate_id(self, job: Dict) -> str:
        """Generate unique ID for a job"""
        unique_str = f"{job.get('company', '')}-{job.get('title', '')}-{job.get('url', '')}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:12]
    
    def add_application(self, job: Dict, status: str = "applied") -> Dict:
        """Record a new job application"""
        app_id = self._generate_id(job)
        
        # Check if already applied
        for app in self.applications["applications"]:
            if app["id"] == app_id:
                print(f"Already applied to {job.get('title')} at {job.get('company')}")
                return app
        
        application = {
            "id": app_id,
            "job_id": job.get('id', ''),
            "title": job.get('title', ''),
            "company": job.get('company', ''),
            "location": job.get('location', ''),
            "url": job.get('url', ''),
            "match_score": job.get('match_score', 0),
            "status": status,
            "applied_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "notes": "",
            "response_date": None,
            "interview_dates": []
        }
        
        self.applications["applications"].append(application)
        self._update_stats()
        self._save_applications()
        
        print(f"✅ Applied to {job.get('title')} at {job.get('company')}")
        return application
    
    def update_status(self, app_id: str, status: str, notes: str = ""):
        """Update application status"""
        for app in self.applications["applications"]:
            if app["id"] == app_id:
                app["status"] = status
                app["updated_at"] = datetime.now().isoformat()
                if notes:
                    app["notes"] = notes
                if status in ["interview", "offer"]:
                    app["response_date"] = datetime.now().isoformat()
                self._update_stats()
                self._save_applications()
                return app
        return None
    
    def _update_stats(self):
        """Update application statistics"""
        stats = {"total": len(self.applications["applications"]), "by_status": {}}
        
        for app in self.applications["applications"]:
            status = app["status"]
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        self.applications["stats"] = stats
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        return self.applications["stats"]
    
    def save_daily_stats(self):
        """Save daily statistics snapshot"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        stats_file = self.stats_dir / f"stats_{date_str}.json"
        
        daily_stats = {
            "date": date_str,
            "timestamp": datetime.now().isoformat(),
            "stats": self.get_stats(),
            "recent_applications": [
                app for app in self.applications["applications"]
                if app["applied_at"].startswith(date_str)
            ]
        }
        
        with open(stats_file, 'w') as f:
            json.dump(daily_stats, f, indent=2)
        
        print(f"📊 Daily stats saved to {stats_file}")
        return daily_stats
    
    def get_pending_applications(self) -> List[Dict]:
        """Get applications awaiting response"""
        return [
            app for app in self.applications["applications"]
            if app["status"] in ["applied", "interview"]
        ]
    
    def summary(self) -> str:
        """Generate summary text"""
        stats = self.get_stats()
        lines = [
            f"📊 Application Summary",
            f"Total Applications: {stats['total']}",
            f"By Status:"
        ]
        for status, count in stats.get('by_status', {}).items():
            lines.append(f"  - {status}: {count}")
        return "\n".join(lines)


if __name__ == "__main__":
    tracker = ApplicationTracker()
    print(tracker.summary())
