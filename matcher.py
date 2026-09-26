import json
import re
import os
from datetime import datetime, timedelta


# ============================================================
# YOUR PROFILE
# ============================================================

PROFILE = {
    "experience_years": 3,

    "target_roles": [
        "devops engineer",
        "cloud devops engineer",
        "platform engineer",
        "site reliability engineer",
        "sre",
        "cloud engineer",
        "kubernetes engineer",
    ],

    # Skills that are most important for your profile
    "core_skills": [
        "kubernetes",
        "docker",
        "terraform",
        "ci/cd",
        "linux",
    ],

    # Useful but not essential
    "supporting_skills": [
        "aws",
        "azure",
        "gitops",
        "argo cd",
        "hashicorp vault",
        "elasticsearch",
        "kibana",
        "prometheus",
        "grafana",
    ],

    "locations": [
        "bengaluru",
        "bangalore",
        "hyderabad",
        "pune",
        "chennai",
        "mumbai",
        "india",
    ],

    # Ignore jobs older than this many days
    "max_job_age_days": 14,
}


INPUT_FILE = "data/jobs.json"
OUTPUT_FILE = "data/matched_jobs.json"


# ============================================================
# HELPERS
# ============================================================

def normalize(text):
    if not text:
        return ""

    return str(text).lower().strip()


def get_job_text(job):
    fields = [
        job.get("title", ""),
        job.get("descriptionText", ""),
        job.get("descriptionHtml", ""),
        job.get("jobFunction", ""),
        job.get("industries", ""),
        job.get("seniorityLevel", ""),
        job.get("employmentType", ""),
    ]

    return normalize(" ".join(str(field) for field in fields))


# ============================================================
# SKILL ALIASES
# ============================================================

SKILL_ALIASES = {

    "kubernetes": [
        "kubernetes",
        "k8s",
    ],

    "docker": [
        "docker",
        "docker containers",
    ],

    "terraform": [
        "terraform",
    ],

    "ci/cd": [
        "ci/cd",
        "ci cd",
        "continuous integration",
        "continuous delivery",
        "continuous deployment",
    ],

    "linux": [
        "linux",
    ],

    "aws": [
        "aws",
        "amazon web services",
    ],

    "azure": [
        "azure",
        "microsoft azure",
    ],

    "gitops": [
        "gitops",
    ],

    "argo cd": [
        "argo cd",
        "argocd",
    ],

    "hashicorp vault": [
        "hashicorp vault",
        "vault",
    ],

    "elasticsearch": [
        "elasticsearch",
        "elastic search",
    ],

    "kibana": [
        "kibana",
    ],

    "prometheus": [
        "prometheus",
    ],

    "grafana": [
        "grafana",
    ],
}


def skill_present(text, skill):

    aliases = SKILL_ALIASES.get(skill, [skill])

    for alias in aliases:

        # Word-boundary search prevents accidental matches
        pattern = r"\b" + re.escape(alias.lower()) + r"\b"

        if re.search(pattern, text):
            return True

    return False


def find_skills(job):

    text = get_job_text(job)

    core_matched = []
    core_missing = []

    supporting_matched = []
    supporting_missing = []

    for skill in PROFILE["core_skills"]:

        if skill_present(text, skill):
            core_matched.append(skill)
        else:
            core_missing.append(skill)

    for skill in PROFILE["supporting_skills"]:

        if skill_present(text, skill):
            supporting_matched.append(skill)
        else:
            supporting_missing.append(skill)

    return (
        core_matched,
        core_missing,
        supporting_matched,
        supporting_missing,
    )


# ============================================================
# ROLE MATCH
# ============================================================

def find_role_matches(job):

    title = normalize(job.get("title", ""))

    matches = []

    for role in PROFILE["target_roles"]:

        if role in title:
            matches.append(role)

    return matches


# ============================================================
# EXPERIENCE EXTRACTION
# ============================================================

def extract_required_experience(job):

    text = get_job_text(job)

    patterns = [

        # Example: 6-9 years
        r"(\d+)\s*-\s*(\d+)\s*(?:years?|yrs?)",

        # Example: 5+ years
        r"(\d+)\s*\+\s*(?:years?|yrs?)",

        # Example: 5 years of experience
        r"(\d+)\s*(?:years?|yrs?)\s*(?:of\s+)?experience",
    ]

    for pattern in patterns:

        match = re.search(pattern, text)

        if match:

            numbers = match.groups()

            if len(numbers) == 2:

                minimum = int(numbers[0])
                maximum = int(numbers[1])

                return {
                    "minimum": minimum,
                    "maximum": maximum,
                    "raw": match.group(0),
                }

            minimum = int(numbers[0])

            return {
                "minimum": minimum,
                "maximum": None,
                "raw": match.group(0),
            }

    return {
        "minimum": None,
        "maximum": None,
        "raw": None,
    }


# ============================================================
# EXPERIENCE ANALYSIS
# ============================================================

def analyze_experience(job):

    experience = extract_required_experience(job)

    required = experience["minimum"]
    user_experience = PROFILE["experience_years"]

    if required is None:

        return {
            "status": "Not specified",
            "required": experience,
            "gap_years": 0,
        }

    gap = required - user_experience

    if gap <= 0:

        status = "Matches"

    elif gap <= 1:

        status = "Slight gap"

    else:

        status = "Experience gap"

    return {
        "status": status,
        "required": experience,
        "gap_years": max(gap, 0),
    }


# ============================================================
# LOCATION
# ============================================================

def check_location(job):

    location = normalize(job.get("location", ""))

    for target in PROFILE["locations"]:

        if target in location:
            return True

    return False


# ============================================================
# REMOTE
# ============================================================

def check_remote(job):

    text = get_job_text(job)

    remote_keywords = [
        "remote",
        "work from home",
        "100% remote",
        "fully remote",
        "remote work",
    ]

    return any(keyword in text for keyword in remote_keywords)


# ============================================================
# JOB DATE
# ============================================================

def analyze_freshness(job):

    posted_at = job.get("postedAt")

    if not posted_at:

        return {
            "fresh": False,
            "age_days": None,
            "status": "Unknown",
        }

    try:

        posted_date = datetime.strptime(
            posted_at,
            "%Y-%m-%d"
        ).date()

        today = datetime.now().date()

        age_days = (today - posted_date).days

        fresh = age_days <= PROFILE["max_job_age_days"]

        return {
            "fresh": fresh,
            "age_days": age_days,
            "status": "Fresh" if fresh else "Old",
        }

    except ValueError:

        return {
            "fresh": False,
            "age_days": None,
            "status": "Unknown",
        }


# ============================================================
# MATCH ENGINE
# ============================================================

def calculate_match(job):

    role_matches = find_role_matches(job)

    (
        core_matched,
        core_missing,
        supporting_matched,
        supporting_missing,
    ) = find_skills(job)

    experience = analyze_experience(job)

    location_match = check_location(job)

    remote = check_remote(job)

    freshness = analyze_freshness(job)

    score = 0

    reasons = []
    warnings = []

    # --------------------------------------------------------
    # ROLE — 25 POINTS
    # --------------------------------------------------------

    if role_matches:

        score += 25

        reasons.append(
            "Target DevOps-related role"
        )

    # --------------------------------------------------------
    # CORE SKILLS — 35 POINTS
    # --------------------------------------------------------

    if PROFILE["core_skills"]:

        core_score = (
            len(core_matched)
            / len(PROFILE["core_skills"])
        ) * 35

        score += core_score

    # --------------------------------------------------------
    # SUPPORTING SKILLS — 20 POINTS
    # --------------------------------------------------------

    if PROFILE["supporting_skills"]:

        supporting_score = (
            len(supporting_matched)
            / len(PROFILE["supporting_skills"])
        ) * 20

        score += supporting_score

    # --------------------------------------------------------
    # LOCATION / REMOTE — 10 POINTS
    # --------------------------------------------------------

    if location_match:

        score += 10

        reasons.append(
            "Target location"
        )

    elif remote:

        score += 10

        reasons.append(
            "Remote opportunity"
        )

    else:

        warnings.append(
            "Location does not match target locations"
        )

    # --------------------------------------------------------
    # EXPERIENCE — 10 POINTS
    # --------------------------------------------------------

    if experience["status"] == "Matches":

        score += 10

        reasons.append(
            "Experience requirement matches"
        )

    elif experience["status"] == "Not specified":

        score += 5

        warnings.append(
            "Experience requirement not specified"
        )

    elif experience["status"] == "Slight gap":

        score += 3

        warnings.append(
            "Slight experience gap"
        )

    else:

        warnings.append(
            "Experience requirement is significantly higher"
        )

    # --------------------------------------------------------
    # ROUND SCORE
    # --------------------------------------------------------

    score = round(score)

    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    if experience["status"] == "Experience gap":

        if score >= 65:
            category = "EXPERIENCE GAP"

        else:
            category = "LOW MATCH"

    elif score >= 80:

        category = "HIGH MATCH"

    elif score >= 65:

        category = "GOOD MATCH"

    elif score >= 50:

        category = "REVIEW"

    else:

        category = "LOW MATCH"

    # --------------------------------------------------------
    # FRESHNESS WARNING
    # --------------------------------------------------------

    if not freshness["fresh"]:

        warnings.append(
            f"Job is {freshness['age_days']} days old"
        )

    return {

        "match_score": score,

        "match_category": category,

        "role_matches": role_matches,

        "core_skills_matched": core_matched,

        "core_skills_missing": core_missing,

        "supporting_skills_matched": supporting_matched,

        "supporting_skills_missing": supporting_missing,

        "experience": experience,

        "location_match": location_match,

        "remote": remote,

        "freshness": freshness,

        "reasons": reasons,

        "warnings": warnings,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    if not os.path.exists(INPUT_FILE):

        raise FileNotFoundError(
            f"{INPUT_FILE} not found. Run app.py first."
        )

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        jobs = json.load(file)

    results = []

    print()
    print("======================================")
    print("JOB MATCHING ENGINE")
    print("======================================")

    for job in jobs:

        match = calculate_match(job)

        result = {

            "job_id": job.get("id"),

            "title": job.get("title"),

            "company": job.get("companyName"),

            "location": job.get("location"),

            "posted_at": job.get("postedAt"),

            "applicants": job.get("applicantsCount"),

            "job_url": job.get("link"),

            "apply_url": job.get("applyUrl"),

            "company_url": job.get("companyWebsite"),

            "match": match,
        }

        results.append(result)

        print()
        print("--------------------------------------")

        print(
            f"{job.get('title')} "
            f"| {job.get('companyName')}"
        )

        print(
            f"Score: {match['match_score']}"
        )

        print(
            f"Category: {match['match_category']}"
        )

        print(
            f"Core skills: "
            f"{len(match['core_skills_matched'])}/"
            f"{len(PROFILE['core_skills'])}"
        )

        print(
            f"Supporting skills: "
            f"{len(match['supporting_skills_matched'])}/"
            f"{len(PROFILE['supporting_skills'])}"
        )

        print(
            f"Experience: "
            f"{match['experience']['status']}"
        )

        print(
            f"Freshness: "
            f"{match['freshness']['status']}"
        )

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    results.sort(
        key=lambda x: x["match"]["match_score"],
        reverse=True,
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print("======================================")
    print("MATCHING COMPLETED")
    print("======================================")

    print(
        f"Jobs analyzed: {len(results)}"
    )

    print(
        f"Results saved to: {OUTPUT_FILE}"
    )

    print()
    print("TOP JOBS")
    print("--------------------------------------")

    for job in results[:5]:

        print(
            f"{job['match']['match_score']} | "
            f"{job['match']['match_category']} | "
            f"{job['title']} | "
            f"{job['company']}"
        )


if __name__ == "__main__":
    main()