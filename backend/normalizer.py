"""
Normalizer for cleaning raw job attributes across disparate platforms.
"""

import re
from typing import Tuple, Optional, Dict, Any

EXP_RANGE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
EXP_PLUS_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*\+", re.IGNORECASE)
EXP_SINGLE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", re.IGNORECASE)

def parse_experience_string(text: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    """
    Extracts (min_exp, max_exp) in years from arbitrary text strings.
    Examples:
        '0-1 Years' -> (0.0, 1.0)
        '0 to 1 Yrs' -> (0.0, 1.0)
        '2+ years' -> (2.0, None)
        'Freshers' -> (0.0, 0.0)
    """
    if not text:
        return None, None

    text_clean = str(text).strip().lower()

    if any(w in text_clean for w in ["fresher", "entry level", "new grad", "intern"]):
        return 0.0, 0.0

    # Match '0 - 1 years'
    m_range = EXP_RANGE_PATTERN.search(text_clean)
    if m_range:
        try:
            return float(m_range.group(1)), float(m_range.group(2))
        except ValueError:
            pass

    # Match '2+ years'
    m_plus = EXP_PLUS_PATTERN.search(text_clean)
    if m_plus:
        try:
            return float(m_plus.group(1)), None
        except ValueError:
            pass

    # Match '1 year'
    m_single = EXP_SINGLE_PATTERN.search(text_clean)
    if m_single:
        try:
            val = float(m_single.group(1))
            return val, val
        except ValueError:
            pass

    return None, None


def normalize_job_dict(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms raw scraped fields into a standard NormalizedJob dictionary.
    """
    company = str(raw.get("company") or "").strip()
    brand = str(raw.get("brand") or "").strip()
    title = str(raw.get("title") or "").strip()
    location = str(raw.get("location") or "").strip()
    country = str(raw.get("country") or "").strip()
    apply_link = str(raw.get("apply_link") or raw.get("link") or "").strip()
    job_id = str(raw.get("job_id") or apply_link).strip()
    source = str(raw.get("source") or company).strip()
    posted_date = str(raw.get("posted_date") or "").strip()
    description = str(raw.get("description") or "").strip()

    # Experience parsing
    exp_text = str(raw.get("experience_text") or "").strip()
    min_exp = raw.get("min_exp")
    max_exp = raw.get("max_exp")

    # If min_exp or max_exp is provided as float/int, keep it, otherwise parse exp_text
    if min_exp is not None:
        try:
            min_exp = float(min_exp)
        except (ValueError, TypeError):
            min_exp = None

    if max_exp is not None:
        try:
            max_exp = float(max_exp)
        except (ValueError, TypeError):
            max_exp = None

    if (min_exp is None and max_exp is None) and exp_text:
        min_exp, max_exp = parse_experience_string(exp_text)

    # Infer country if location clearly specifies India
    if not country:
        from filters import is_india_location
        if is_india_location(location):
            country = "India"

    return {
        "job_id": job_id,
        "company": company,
        "brand": brand,
        "title": title,
        "location": location,
        "country": country,
        "experience_text": exp_text,
        "min_exp": min_exp,
        "max_exp": max_exp,
        "apply_link": apply_link,
        "posted_date": posted_date,
        "description": description,
        "source": source,
    }
