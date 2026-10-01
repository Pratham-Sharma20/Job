"""
Central Pipeline for processing, filtering, deduplicating, saving, and alerting on scraped jobs.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from db import jobs_collection
from normalizer import normalize_job_dict
from filters import evaluate_job
from notifier import send_telegram_notification


class PipelineMetrics:
    """Tracks metrics for an individual scraper run."""
    def __init__(self, scraper_name: str):
        self.scraper_name = scraper_name
        self.started_at = datetime.now()
        self.finished_at: Optional[datetime] = None
        self.duration_seconds: float = 0.0
        self.fetched: int = 0
        self.qualified: int = 0
        self.saved: int = 0
        self.new_jobs: int = 0
        self.rejection_reasons: Dict[str, int] = {}
        self.status: str = "PENDING"
        self.error_message: Optional[str] = None

    def record_fetch(self):
        self.fetched += 1

    def record_rejection(self, reason: str):
        self.rejection_reasons[reason] = self.rejection_reasons.get(reason, 0) + 1

    def record_qualified(self):
        self.qualified += 1

    def record_save(self, is_new: bool = False):
        self.saved += 1
        if is_new:
            self.new_jobs += 1

    def finish(self, status: str = "SUCCESS", error_message: Optional[str] = None):
        self.finished_at = datetime.now()
        self.duration_seconds = round((self.finished_at - self.started_at).total_seconds(), 2)
        self.status = status
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scraper_name": self.scraper_name,
            "status": self.status,
            "duration_seconds": self.duration_seconds,
            "fetched": self.fetched,
            "qualified": self.qualified,
            "saved": self.saved,
            "new_jobs": self.new_jobs,
            "rejection_reasons": self.rejection_reasons,
            "error_message": self.error_message,
        }

    def summary_line(self) -> str:
        icon = "[OK]" if self.status == "SUCCESS" else "[X]"
        if self.status == "SUCCESS":
            return (
                f"{self.scraper_name:<25} {icon}  "
                f"{self.fetched:>4} fetched -> {self.qualified:>3} qualified -> "
                f"{self.new_jobs:>2} new ({self.duration_seconds}s)"
            )
        else:
            return (
                f"{self.scraper_name:<25} {icon}  "
                f"FAILED ({self.error_message or 'Unknown error'}) ({self.duration_seconds}s)"
            )


def process_single_job(raw_job: Dict[str, Any], metrics: Optional[PipelineMetrics] = None) -> Optional[Dict[str, Any]]:
    """
    Normalizes, filters, deduplicates, and saves a single job dictionary.
    Returns the saved job dict if qualified and saved, else None.
    """
    if metrics:
        metrics.record_fetch()

    normalized = normalize_job_dict(raw_job)

    if not normalized.get("title") or not normalized.get("apply_link"):
        if metrics:
            metrics.record_rejection("missing_title_or_link")
        return None

    # Evaluate via Central Filter
    eval_result = evaluate_job(
        title=normalized["title"],
        location=normalized["location"],
        country=normalized["country"],
        min_exp=normalized["min_exp"],
        max_exp=normalized["max_exp"],
        experience_text=normalized["experience_text"]
    )

    if not eval_result["valid"]:
        if metrics:
            metrics.record_rejection(eval_result["reason"])
        return None

    if metrics:
        metrics.record_qualified()

    # Prepare document for database
    job_doc = {
        "job_id": normalized["job_id"],
        "company": normalized["company"],
        "brand": normalized.get("brand", ""),
        "title": normalized["title"],
        "track": eval_result["track"],
        "filter_reason": eval_result["reason"],
        "location": normalized["location"],
        "country": normalized["country"] or "India",
        "experience_text": normalized["experience_text"],
        "min_exp": normalized["min_exp"],
        "max_exp": normalized["max_exp"],
        "apply_link": normalized["apply_link"],
        "posted_date": normalized["posted_date"],
        "description": normalized["description"],
        "source": normalized["source"],
        "scraped_at": datetime.now().isoformat(timespec="seconds"),
    }

    try:
        result = jobs_collection.update_one(
            {
                "company": job_doc["company"],
                "job_id": job_doc["job_id"]
            },
            {"$set": job_doc},
            upsert=True
        )

        is_new = (result.upserted_id is not None)

        if metrics:
            metrics.record_save(is_new=is_new)

        if is_new:
            send_telegram_notification(job_doc)

        return job_doc

    except Exception as e:
        print(f"Error saving job {job_doc.get('title')} to DB: {e}")
        if metrics:
            metrics.record_rejection("db_error")
        return None


def process_jobs_batch(raw_jobs: List[Dict[str, Any]], metrics: Optional[PipelineMetrics] = None) -> List[Dict[str, Any]]:
    """Processes a batch of raw jobs through the central pipeline."""
    saved_jobs = []
    for raw in raw_jobs:
        saved = process_single_job(raw, metrics)
        if saved:
            saved_jobs.append(saved)
    return saved_jobs
