"""Fetch PhonePe Apollo API directly and inspect structure."""
import requests, json, sys

sys.stdout.reconfigure(encoding="utf-8")

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.phonepe.com/careers/job-openings/",
}

r = requests.get("https://www.phonepe.com/apollo/job-postings/latest.json", headers=H, timeout=15, verify=False)
print(f"Status: {r.status_code}")
data = r.json()
results = data.get("results", [])
print(f"Total jobs: {len(results)}")
print(f"\nFirst 5 jobs:")
for job in results[:5]:
    print(json.dumps(job, indent=2))
    print()

# Count by status
from collections import Counter
statuses = Counter(j.get("status","") for j in results)
print(f"\nBy status: {dict(statuses)}")

# Show published ones
published = [j for j in results if j.get("status") == "PUBLISHED"]
print(f"\nPUBLISHED jobs ({len(published)}):")
for j in published[:10]:
    dept = j.get("department","")
    title = j.get("title","")
    loc = j.get("location","")
    status = j.get("status","")
    apply = j.get("applyUrl","") or j.get("apply_url","")
    print(f"  [{dept}] {title!r} | loc={loc!r} | url={str(apply)[:60]}")
