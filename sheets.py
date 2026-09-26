import json
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from telegram import send_telegram_message


# ==========================================
# CONFIGURATION
# ==========================================

CREDENTIALS_FILE = "google_credentials.json"
SPREADSHEET_NAME = "DevOps Job Tracker"
DATA_FILE = "data/matched_jobs.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ==========================================
# GOOGLE SHEETS CONNECTION
# ==========================================

credentials = Credentials.from_service_account_file(
    CREDENTIALS_FILE,
    scopes=SCOPES,
)

client = gspread.authorize(credentials)

spreadsheet = client.open(SPREADSHEET_NAME)
worksheet = spreadsheet.sheet1


# ==========================================
# LOAD MATCHED JOBS
# ==========================================

with open(DATA_FILE, "r", encoding="utf-8") as file:
    jobs = json.load(file)

print(f"Jobs loaded from matcher: {len(jobs)}")


# ==========================================
# GET EXISTING JOB IDS
# ==========================================

existing_records = worksheet.get_all_records()

existing_job_ids = set()

for record in existing_records:
    job_id = str(record.get("Job ID", "")).strip()

    if job_id:
        existing_job_ids.add(job_id)


print(f"Existing jobs in Google Sheets: {len(existing_job_ids)}")


# ==========================================
# IMPORT JOBS
# ==========================================

today = datetime.now().strftime("%Y-%m-%d")

new_jobs = 0
skipped_jobs = 0


for job in jobs:

    job_id = str(job.get("job_id", "")).strip()

    if not job_id:
        print("Skipping job without Job ID")
        continue


    # ======================================
    # DUPLICATE CHECK
    # ======================================

    if job_id in existing_job_ids:
        skipped_jobs += 1
        print(f"Skipped duplicate: {job.get('title', '')}")
        continue


    # ======================================
    # BASIC JOB INFORMATION
    # ======================================

    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    posted_at = job.get("posted_at", "")
    applicants = job.get("applicants", "")

    job_url = job.get("job_url", "")
    company_url = job.get("company_url", "")


    # ======================================
    # MATCH INFORMATION
    # ======================================

    match = job.get("match", {})

    match_score = match.get("match_score", "")
    match_category = match.get("match_category", "")

    core_matched = match.get(
        "core_skills_matched",
        []
    )

    core_missing = match.get(
        "core_skills_missing",
        []
    )

    supporting_matched = match.get(
        "supporting_skills_matched",
        []
    )

    supporting_missing = match.get(
        "supporting_skills_missing",
        []
    )

    experience_data = match.get(
        "experience",
        {}
    )

    reasons = match.get(
        "reasons",
        []
    )

    warnings = match.get(
        "warnings",
        []
    )

    remote = match.get(
        "remote",
        False
    )


    # ======================================
    # EXPERIENCE
    # ======================================

    required_experience = experience_data.get(
        "required",
        {}
    )

    experience_raw = required_experience.get(
        "raw"
    )

    if experience_raw:
        experience = experience_raw
    else:
        experience = "Not specified"


    # ======================================
    # CONVERT LISTS TO TEXT
    # ======================================

    core_matched_text = ", ".join(core_matched)

    core_missing_text = ", ".join(core_missing)

    supporting_matched_text = ", ".join(
        supporting_matched
    )

    supporting_missing_text = ", ".join(
        supporting_missing
    )

    reasons_text = " | ".join(reasons)

    warnings_text = " | ".join(warnings)


    # ======================================
    # NOTES
    # ======================================

    notes = reasons_text

    if warnings_text:
        if notes:
            notes += " | "

        notes += f"Warnings: {warnings_text}"


    # ======================================
    # GOOGLE SHEETS ROW
    # ======================================

    row = [
        job_id,
        today,
        posted_at,
        company,
        title,
        location,
        match_score,
        match_category,
        experience,
        core_matched_text,
        supporting_matched_text,
        core_missing_text,
        supporting_missing_text,
        "Yes" if remote else "No",
        job_url,
        company_url,
        applicants,
        "NEW",
        notes,
    ]


    # ======================================
    # ADD JOB TO GOOGLE SHEETS
    # ======================================

    worksheet.append_row(row)

    existing_job_ids.add(job_id)

    new_jobs += 1

    print(
        f"Added: {title} | "
        f"{company} | "
        f"Score: {match_score}"
    )


    # ======================================
    # TELEGRAM NOTIFICATION
    # ======================================

    telegram_message = f"""🚨 NEW DEVOPS JOB

{title}
{company}

📍 {location}

🎯 Match: {match_score}%
🔥 {match_category}

Core Skills:
✓ {core_matched_text if core_matched_text else "None"}

Supporting Skills:
✓ {supporting_matched_text if supporting_matched_text else "None"}

Missing Core Skills:
• {core_missing_text if core_missing_text else "None"}

Missing Supporting Skills:
• {supporting_missing_text if supporting_missing_text else "None"}

💼 Experience:
{experience}

👥 Applicants:
{applicants if applicants else "Not available"}

🔗 Apply:
{job_url}

📝 Status: NEW
"""


    # ======================================
    # SEND TELEGRAM ALERT
    # ======================================

    if send_telegram_message(telegram_message):
        print("Telegram alert sent.")
    else:
        print("Telegram alert failed.")


# ==========================================
# SUMMARY
# ==========================================

print()
print("======================================")
print("GOOGLE SHEETS IMPORT COMPLETED")
print("======================================")
print(f"New jobs added     : {new_jobs}")
print(f"Duplicates skipped : {skipped_jobs}")
print("======================================")