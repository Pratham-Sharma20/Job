"""
Centralized filtering and classification module for Indian SDE / SWE / AI-ML / Data early-career roles.
"""

import re
from typing import Optional, Dict, Any

# 1. Technical Role Regex Patterns (with word boundaries)
TECHNICAL_TRACKS = {
    "Software Engineering": [
        re.compile(r"\bsoftware\s+enginee(r|ring)\b", re.IGNORECASE),
        re.compile(r"\bsoftware\s+develop(er|ment\s+engineer)\b", re.IGNORECASE),
        re.compile(r"\bsde\b", re.IGNORECASE),
        re.compile(r"\bswe\b", re.IGNORECASE),
        re.compile(r"\bbackend\s+(engineer|developer)\b", re.IGNORECASE),
        re.compile(r"\bfrontend\s+(engineer|developer)\b", re.IGNORECASE),
        re.compile(r"\bfull\s*stack\s+(engineer|developer)\b", re.IGNORECASE),
        re.compile(r"\bweb\s+developer\b", re.IGNORECASE),
        re.compile(r"\bmobile\s+developer\b", re.IGNORECASE),
        re.compile(r"\bios\s+developer\b", re.IGNORECASE),
        re.compile(r"\bandroid\s+developer\b", re.IGNORECASE),
        re.compile(r"\bsystems?\s+engineer\b", re.IGNORECASE),
    ],
    "AI / ML": [
        re.compile(r"\bmachine\s+learning\s+engineer\b", re.IGNORECASE),
        re.compile(r"\bml\s+engineer\b", re.IGNORECASE),
        re.compile(r"\bai\s+engineer\b", re.IGNORECASE),
        re.compile(r"\bartificial\s+intelligence\s+engineer\b", re.IGNORECASE),
        re.compile(r"\bapplied\s+scientist\b", re.IGNORECASE),
        re.compile(r"\bresearch\s+engineer\b", re.IGNORECASE),
        re.compile(r"\bresearch\s+scientist\b", re.IGNORECASE),
    ],
    "Data Engineering": [
        re.compile(r"\bdata\s+engineer\b", re.IGNORECASE),
        re.compile(r"\bdata\s+platform\s+engineer\b", re.IGNORECASE),
        re.compile(r"\bbig\s*data\s+engineer\b", re.IGNORECASE),
    ]
}

# 2. Senior keywords to strictly reject (specialist and fellow deliberately omitted)
SENIOR_PATTERNS = [
    re.compile(r"\bsenior\b", re.IGNORECASE),
    re.compile(r"\bsr\.?\b", re.IGNORECASE),
    re.compile(r"\bstaff\b", re.IGNORECASE),
    re.compile(r"\bprincipal\b", re.IGNORECASE),
    re.compile(r"\blead\b", re.IGNORECASE),
    re.compile(r"\bmanager\b", re.IGNORECASE),
    re.compile(r"\bdirector\b", re.IGNORECASE),
    re.compile(r"\barchitect\b", re.IGNORECASE),
    re.compile(r"\bhead\b", re.IGNORECASE),
    re.compile(r"\bvp\b", re.IGNORECASE),
    re.compile(r"\bvice\s+president\b", re.IGNORECASE),
]

# 3. Explicit early career keywords and patterns
INTERN_PATTERNS = [
    re.compile(r"\bintern(ship)?\b", re.IGNORECASE),
    re.compile(r"\btrainee\b", re.IGNORECASE),
    re.compile(r"\bapprentice\b", re.IGNORECASE),
]

EARLY_CAREER_PATTERNS = [
    re.compile(r"\bgraduate\b", re.IGNORECASE),
    re.compile(r"\bnew\s+grad\b", re.IGNORECASE),
    re.compile(r"\bfresher\b", re.IGNORECASE),
    re.compile(r"\bentry\s+level\b", re.IGNORECASE),
    re.compile(r"\bsde[- ]?1\b", re.IGNORECASE),
    re.compile(r"\bsde[- ]?i\b", re.IGNORECASE),
    re.compile(r"\bswe[- ]?1\b", re.IGNORECASE),
    re.compile(r"\bswe[- ]?i\b", re.IGNORECASE),
    re.compile(r"\bengineer[- ]?1\b", re.IGNORECASE),
    re.compile(r"\bengineer[- ]?i\b", re.IGNORECASE),
    re.compile(r"\bsoftware\s+engineer\s+(1|i)\b", re.IGNORECASE),
    re.compile(r"\b0[- ]?1\s*years?\b", re.IGNORECASE),
    re.compile(r"\b0\s*to\s*1\s*years?\b", re.IGNORECASE),
    re.compile(r"\bless\s+than\s+1\s*year\b", re.IGNORECASE),
]

# 4. India Location keywords & hub tokens
INDIA_TOKENS = [
    "india", "ind", "bengaluru", "bangalore", "hyderabad", "chennai", "pune",
    "gurugram", "gurgaon", "noida", "mumbai", "delhi", "delhi ncr", "kolkata",
    "ahmedabad", "kochi", "cochin", "thiruvananthapuram", "trivandrum",
    "karnataka", "telangana", "tamil nadu", "maharashtra", "haryana",
    "uttar pradesh", "west bengal", "gujarat", "kerala"
]


def is_india_location(location: str = "", country: str = "") -> bool:
    """Verifies that the job posting is located in India."""
    country_norm = str(country or "").strip().lower()
    if country_norm in ["india", "ind", "in"]:
        return True

    loc_norm = str(location or "").strip().lower()
    if not loc_norm:
        return False

    # Check for explicit token or endswith IND
    if loc_norm.upper().endswith("IND") or loc_norm.upper().endswith(", IN"):
        return True

    return any(token in loc_norm for token in INDIA_TOKENS)


def get_technical_track(title: str) -> Optional[str]:
    """Identifies the role track (Software Engineering, AI / ML, Data Engineering)."""
    title_clean = str(title or "").strip()
    for track, patterns in TECHNICAL_TRACKS.items():
        for pattern in patterns:
            if pattern.search(title_clean):
                return track
    return None


def is_senior_role(title: str) -> bool:
    """Checks if the title explicitly denotes a senior or leadership role."""
    title_clean = str(title or "").strip()
    for pattern in SENIOR_PATTERNS:
        if pattern.search(title_clean):
            return True
    return False


def is_internship(title: str) -> bool:
    """Checks if the role is explicitly an internship/trainee."""
    title_clean = str(title or "").strip()
    return any(p.search(title_clean) for p in INTERN_PATTERNS)


def is_explicit_early_career(title: str, experience_text: str = "") -> bool:
    """Checks if title or text explicitly denotes entry-level/fresher status."""
    text_to_check = f"{title} {experience_text}"
    return any(p.search(text_to_check) for p in EARLY_CAREER_PATTERNS)


def evaluate_job(
    title: str,
    location: str = "",
    country: str = "",
    min_exp: Optional[float] = None,
    max_exp: Optional[float] = None,
    experience_text: str = "",
) -> Dict[str, Any]:
    """
    Central qualification function for SDE and SDE Intern jobs in India.
    
    Returns a dict with:
        valid: bool
        track: str or None
        reason: str (diagnostic code)
    """
    # 1. Geographic Gate
    if not is_india_location(location, country):
        return {"valid": False, "track": None, "reason": "non_india"}

    # 2. Technical Gate
    track = get_technical_track(title)
    if not track:
        return {"valid": False, "track": None, "reason": "non_technical"}

    # 3. Seniority Exclusion Gate
    if is_senior_role(title):
        return {"valid": False, "track": track, "reason": "senior_role"}

    # 4. Explicit Internship Gate
    if is_internship(title):
        return {"valid": True, "track": track, "reason": "valid_intern"}

    # 5. Explicit Early Career / Fresher Gate
    if is_explicit_early_career(title, experience_text):
        # Even if experience is missing, an explicit early career title passes
        # But if max_exp or min_exp is explicitly > 1, reject
        if max_exp is not None and max_exp > 1.0:
            return {"valid": False, "track": track, "reason": "experience_too_high"}
        if min_exp is not None and min_exp > 1.0:
            return {"valid": False, "track": track, "reason": "experience_too_high"}
        return {"valid": True, "track": track, "reason": "valid_fresher"}

    # 6. Structured Experience Qualification
    # If structured experience is provided:
    if min_exp is not None and max_exp is not None:
        if max_exp <= 1.0:
            return {"valid": True, "track": track, "reason": "valid_experience"}
        else:
            return {"valid": False, "track": track, "reason": "experience_too_high"}

    if min_exp is not None:
        if min_exp <= 1.0:
            return {"valid": True, "track": track, "reason": "valid_experience"}
        else:
            return {"valid": False, "track": track, "reason": "experience_too_high"}

    if max_exp is not None:
        if max_exp <= 1.0:
            return {"valid": True, "track": track, "reason": "valid_experience"}
        else:
            return {"valid": False, "track": track, "reason": "experience_too_high"}

    # 7. Unspecified experience on plain Software Engineer titles
    # To prevent flooding with 3-7+ yr roles with missing experience metadata
    return {"valid": False, "track": track, "reason": "missing_early_career_signal"}
