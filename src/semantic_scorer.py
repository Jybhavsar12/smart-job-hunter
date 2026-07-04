"""
Semantic Job Scoring Engine - Ranks jobs by embedding similarity to profile

Replaces substring keyword matching with sentence-transformer embeddings:
the profile and each job posting are encoded as dense vectors and compared
by cosine similarity. Rule-based checks are kept where rules are correct
(company exclusions, location preference).
"""
import re
import yaml
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

MODEL_NAME = "all-MiniLM-L6-v2"

# Final score = semantic similarity (0-70) + location (0-15) + keywords (0-15)
SEMANTIC_WEIGHT = 70
LOCATION_WEIGHT = 15
KEYWORD_WEIGHT = 15

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace for clean embedding input"""
    return WS_RE.sub(" ", TAG_RE.sub(" ", text or "")).strip()


class SemanticScorer:
    def __init__(self, config_path: str = "config/profile.yaml"):
        self.config = self._load_config(config_path)
        self._model = None
        self._profile_embedding = None

    def _load_config(self, path: str) -> Dict:
        config_file = Path(__file__).parent.parent / path
        with open(config_file, "r") as f:
            return yaml.safe_load(f)

    @property
    def model(self):
        """Lazy-load the model so importing this module stays cheap"""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(MODEL_NAME)
        return self._model

    def _build_profile_text(self) -> str:
        """Render the YAML profile as natural language for the encoder"""
        prefs = self.config.get("preferences", {})
        titles = ", ".join(prefs.get("titles", []))
        levels = ", ".join(prefs.get("experience_levels", []))
        skills = []
        for category in self.config.get("skills", {}).values():
            skills.extend(category)
        keywords = ", ".join(self.config.get("priority_keywords", []))
        return (
            f"Candidate seeking roles such as {titles}. "
            f"Experience level: {levels}. "
            f"Skilled in {', '.join(skills)}. "
            f"Interested in positions mentioning {keywords}."
        )

    @property
    def profile_embedding(self):
        if self._profile_embedding is None:
            self._profile_embedding = self.model.encode(
                self._build_profile_text(), normalize_embeddings=True
            )
        return self._profile_embedding

    def _job_text(self, job: Dict[str, Any]) -> str:
        title = job.get("title", "")
        company = job.get("company", "")
        description = strip_html(job.get("description", ""))[:2000]
        tags = ", ".join(job.get("tags", []))
        return f"{title} at {company}. {tags}. {description}"

    def _semantic_score(self, similarity: float) -> float:
        """Map cosine similarity to 0-SEMANTIC_WEIGHT points.

        Similarities below 0.2 are noise; above 0.75 is a near-perfect
        match. Linearly rescale that useful band to the full range.
        """
        rescaled = (similarity - 0.2) / (0.75 - 0.2)
        return max(0.0, min(1.0, rescaled)) * SEMANTIC_WEIGHT

    def _score_location(self, location: str) -> float:
        prefs = [loc.lower() for loc in self.config["preferences"]["locations"]]
        if "remote" in location:
            return LOCATION_WEIGHT
        for pref in prefs:
            if pref in location or location in pref:
                return LOCATION_WEIGHT
        if "canada" in location:
            return LOCATION_WEIGHT * 0.66
        return 0

    def _score_keywords(self, text: str) -> float:
        keywords = [k.lower() for k in self.config.get("priority_keywords", [])]
        matched = sum(1 for k in keywords if k in text)
        return min(KEYWORD_WEIGHT, matched * 5)

    def _is_excluded(self, company: str) -> bool:
        excluded = [c.lower() for c in self.config.get("excluded_companies", [])]
        return any(exc in company for exc in excluded if exc)

    def score_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Score a single job (convenience wrapper over rank_jobs)"""
        return self.rank_jobs([job])[0]

    def rank_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Score and rank jobs; encodes all descriptions in one batch"""
        if not jobs:
            return []
        embeddings = self.model.encode(
            [self._job_text(j) for j in jobs], normalize_embeddings=True
        )
        similarities = embeddings @ self.profile_embedding

        for job, sim in zip(jobs, similarities):
            title = job.get("title", "").lower()
            description = strip_html(job.get("description", "")).lower()
            location = job.get("location", "").lower()
            company = job.get("company", "").lower()

            semantic = self._semantic_score(float(sim))
            loc_score = self._score_location(location)
            kw_score = self._score_keywords(title + " " + description)
            score = semantic + loc_score + kw_score

            breakdown = {
                "semantic_similarity": round(float(sim), 4),
                "semantic_score": round(semantic, 2),
                "location_match": loc_score,
                "priority_keywords": kw_score,
            }
            if self._is_excluded(company):
                score = 0
                breakdown["excluded"] = True

            job["match_score"] = round(score, 2)
            job["score_breakdown"] = breakdown
            job["scored_at"] = datetime.now().isoformat()

        return sorted(jobs, key=lambda x: x["match_score"], reverse=True)
