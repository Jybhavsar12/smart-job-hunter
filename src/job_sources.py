"""
Job Sources - Aggregates jobs from multiple sources using free APIs
"""
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import time


class JobSource:
    """Base class for job sources"""
    
    def __init__(self, name: str):
        self.name = name
        self.base_url = ""
    
    def search(self, query: str, location: str = "", **kwargs) -> List[Dict]:
        raise NotImplementedError


class RemoteOKSource(JobSource):
    """RemoteOK - Free API for remote jobs"""
    
    def __init__(self):
        super().__init__("RemoteOK")
        self.base_url = "https://remoteok.com/api"
    
    def search(self, query: str = "", location: str = "", **kwargs) -> List[Dict]:
        try:
            headers = {'User-Agent': 'SmartJobHunter/1.0'}
            response = requests.get(self.base_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            query_lower = query.lower()
            for item in data[1:]:  # Skip first item (metadata)
                if not isinstance(item, dict):
                    continue
                    
                title = item.get('position', '')
                tags = ' '.join(item.get('tags', []))
                
                # Filter by query if provided
                if query and query_lower not in title.lower() and query_lower not in tags.lower():
                    continue
                
                jobs.append({
                    'id': f"remoteok_{item.get('id', '')}",
                    'title': title,
                    'company': item.get('company', 'Unknown'),
                    'location': item.get('location', 'Remote'),
                    'description': item.get('description', '')[:500],
                    'url': item.get('url', ''),
                    'salary': item.get('salary', ''),
                    'tags': item.get('tags', []),
                    'source': self.name,
                    'posted_at': item.get('date', ''),
                    'fetched_at': datetime.now().isoformat()
                })
            
            return jobs[:50]  # Limit results
            
        except Exception as e:
            print(f"[{self.name}] Error: {e}")
            return []


class GitHubJobsSource(JobSource):
    """GitHub Jobs alternative - uses public job boards API"""
    
    def __init__(self):
        super().__init__("Arbeitnow")
        self.base_url = "https://www.arbeitnow.com/api/job-board-api"
    
    def search(self, query: str = "", location: str = "", **kwargs) -> List[Dict]:
        try:
            response = requests.get(self.base_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            jobs = []
            
            query_lower = query.lower() if query else ""
            
            for item in data.get('data', []):
                title = item.get('title', '')
                desc = item.get('description', '')
                
                if query_lower and query_lower not in title.lower() and query_lower not in desc.lower():
                    continue
                
                jobs.append({
                    'id': f"arbeitnow_{item.get('slug', '')}",
                    'title': title,
                    'company': item.get('company_name', 'Unknown'),
                    'location': item.get('location', 'Remote'),
                    'description': desc[:500],
                    'url': item.get('url', ''),
                    'remote': item.get('remote', False),
                    'tags': item.get('tags', []),
                    'source': self.name,
                    'posted_at': item.get('created_at', ''),
                    'fetched_at': datetime.now().isoformat()
                })
            
            return jobs[:50]
            
        except Exception as e:
            print(f"[{self.name}] Error: {e}")
            return []


class JobAggregator:
    """Aggregates jobs from all sources"""
    
    def __init__(self):
        self.sources = [
            RemoteOKSource(),
            GitHubJobsSource(),
        ]
    
    def search_all(self, queries: List[str], location: str = "") -> List[Dict]:
        """Search all sources with multiple queries"""
        all_jobs = []
        seen_ids = set()
        
        for source in self.sources:
            for query in queries:
                print(f"[{source.name}] Searching for '{query}'...")
                jobs = source.search(query, location)
                
                for job in jobs:
                    if job['id'] not in seen_ids:
                        seen_ids.add(job['id'])
                        all_jobs.append(job)
                
                time.sleep(1)  # Rate limiting
        
        print(f"Total unique jobs found: {len(all_jobs)}")
        return all_jobs
    
    def save_jobs(self, jobs: List[Dict], output_dir: str = "data/jobs"):
        """Save jobs to JSON file with date"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = output_path / f"jobs_{date_str}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'date': date_str,
                'count': len(jobs),
                'jobs': jobs
            }, f, indent=2)
        
        print(f"Saved {len(jobs)} jobs to {filename}")
        return str(filename)
