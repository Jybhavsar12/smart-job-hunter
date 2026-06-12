"""
Job Scoring Engine - Ranks jobs based on profile match
"""
import yaml
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class JobScorer:
    def __init__(self, config_path: str = "config/profile.yaml"):
        self.config = self._load_config(config_path)
        self.skills = self._flatten_skills()
        
    def _load_config(self, path: str) -> Dict:
        config_file = Path(__file__).parent.parent / path
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _flatten_skills(self) -> List[str]:
        """Flatten all skills into a single lowercase list"""
        skills = []
        for category in self.config.get('skills', {}).values():
            skills.extend([s.lower() for s in category])
        return skills
    
    def score_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Score a job posting based on multiple factors"""
        score = 0
        breakdown = {}
        
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        location = job.get('location', '').lower()
        company = job.get('company', '').lower()
        
        # Title match (0-30 points)
        title_score = self._score_title(title)
        breakdown['title_match'] = title_score
        score += title_score
        
        # Skills match (0-40 points)
        skills_score = self._score_skills(description)
        breakdown['skills_match'] = skills_score
        score += skills_score
        
        # Location match (0-15 points)
        location_score = self._score_location(location)
        breakdown['location_match'] = location_score
        score += location_score
        
        # Priority keywords (0-15 points)
        keyword_score = self._score_keywords(title + ' ' + description)
        breakdown['priority_keywords'] = keyword_score
        score += keyword_score
        
        # Check exclusions
        if self._is_excluded(company):
            score = 0
            breakdown['excluded'] = True
        
        job['match_score'] = round(score, 2)
        job['score_breakdown'] = breakdown
        job['scored_at'] = datetime.now().isoformat()
        
        return job
    
    def _score_title(self, title: str) -> float:
        """Score based on job title match"""
        target_titles = [t.lower() for t in self.config['preferences']['titles']]
        
        for target in target_titles:
            if target in title:
                return 30
            # Partial match
            words = target.split()
            matches = sum(1 for w in words if w in title)
            if matches >= len(words) * 0.5:
                return 20
        return 5  # Base score for any job
    
    def _score_skills(self, description: str) -> float:
        """Score based on skills mentioned in description"""
        matched = sum(1 for skill in self.skills if skill in description)
        ratio = matched / len(self.skills) if self.skills else 0
        return min(40, ratio * 60)  # Cap at 40
    
    def _score_location(self, location: str) -> float:
        """Score based on location preference"""
        prefs = [loc.lower() for loc in self.config['preferences']['locations']]
        
        if 'remote' in location:
            return 15
        for pref in prefs:
            if pref in location or location in pref:
                return 15
        if 'canada' in location or 'ca' in location:
            return 10
        return 0
    
    def _score_keywords(self, text: str) -> float:
        """Bonus points for priority keywords"""
        keywords = [k.lower() for k in self.config.get('priority_keywords', [])]
        matched = sum(1 for k in keywords if k in text)
        return min(15, matched * 5)
    
    def _is_excluded(self, company: str) -> bool:
        """Check if company is in exclusion list"""
        excluded = [c.lower() for c in self.config.get('excluded_companies', [])]
        return any(exc in company for exc in excluded if exc)
    
    def rank_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Score and rank a list of jobs"""
        scored = [self.score_job(job) for job in jobs]
        return sorted(scored, key=lambda x: x['match_score'], reverse=True)


if __name__ == "__main__":
    # Test the scorer
    scorer = JobScorer()
    test_job = {
        "title": "Junior Software Developer",
        "company": "Tech Corp",
        "location": "Toronto, ON",
        "description": "Looking for a junior developer with Python, React, and AWS experience."
    }
    result = scorer.score_job(test_job)
    print(f"Score: {result['match_score']}/100")
    print(f"Breakdown: {result['score_breakdown']}")
