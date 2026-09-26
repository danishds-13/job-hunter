import os
import json
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

if not APIFY_API_TOKEN:
    raise ValueError("APIFY_API_TOKEN is missing from .env")

# Your Apify Actor
ACTOR_ID = "hKByXkMQaC5Qt9UMN"

# Apify API
BASE_URL = "https://api.apify.com/v2"

# Authentication
HEADERS = {
    "Authorization": f"Bearer {APIFY_API_TOKEN}",
    "Content-Type": "application/json",
}

# --------------------------------------------------
# 1. Actor input
# --------------------------------------------------

actor_input = {
    "urls": [
        "https://www.linkedin.com/jobs/search/?keywords=DevOps%20Engineer&location=Hyderabad%2C%20Telangana%2C%20India",
        "https://www.linkedin.com/jobs/search/?keywords=Cloud%20DevOps%20Engineer&location=Hyderabad%2C%20Telangana%2C%20India",
        "https://www.linkedin.com/jobs/search/?keywords=AWS%20DevOps%20Engineer&location=Hyderabad%2C%20Telangana%2C%20India",
        "https://www.linkedin.com/jobs/search/?keywords=Azure%20DevOps%20Engineer&location=Hyderabad%2C%20Telangana%2C%20India",
        "https://www.linkedin.com/jobs/search/?keywords=Platform%20Engineer&location=Hyderabad%2C%20Telangana%2C%20India",
        "https://www.linkedin.com/jobs/search/?keywords=SRE&location=Hyderabad%2C%20Telangana%2C%20India",
        "https://www.linkedin.com/jobs/search/?keywords=Site%20Reliability%20Engineer&location=Hyderabad%2C%20Telangana%2C%20India",
        "https://www.linkedin.com/jobs/search/?keywords=Cloud%20Engineer&location=Hyderabad%2C%20Telangana%2C%20India",
        "https://www.linkedin.com/jobs/search/?keywords=Kubernetes%20Engineer&location=Hyderabad%2C%20Telangana%2C%20India",
        "https://www.linkedin.com/jobs/search/?keywords=DevOps%20Terraform&location=Hyderabad%2C%20Telangana%2C%20India",
        "https://www.linkedin.com/jobs/search/?keywords=DevOps%20Kubernetes&location=Hyderabad%2C%20Telangana%2C%20India",
        "https://www.linkedin.com/jobs/search/?keywords=Cloud%20Infrastructure%20Engineer&location=Hyderabad%2C%20Telangana%2C%20India"
    ],
    "datePosted": "pastWeek",
    "companyIds": [],
    "under10Applicants": False,
    "autoConvertToAiSearch": True,
    "scrapeCompany": True,
    "limitPerSource": 25,
    "splitByLocation": False
}


# --------------------------------------------------
# 2. Start Apify Actor
# --------------------------------------------------

print("Starting Apify Actor...")

run_url = f"{BASE_URL}/actors/{ACTOR_ID}/runs"

response = requests.post(
    run_url,
    headers=HEADERS,
    json=actor_input,
    timeout=60,
)

response.raise_for_status()

run_data = response.json()["data"]

run_id = run_data["id"]
dataset_id = run_data["defaultDatasetId"]

print(f"Actor started successfully.")
print(f"Run ID: {run_id}")
print(f"Dataset ID: {dataset_id}")


# --------------------------------------------------
# 3. Wait for Actor to finish
# --------------------------------------------------

status_url = f"{BASE_URL}/actor-runs/{run_id}"

print("\nWaiting for Actor to finish...")

while True:

    response = requests.get(
        status_url,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    status_data = response.json()["data"]
    status = status_data["status"]

    print(f"Current status: {status}")

    if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
        break

    time.sleep(5)


# --------------------------------------------------
# 4. Check result
# --------------------------------------------------

if status != "SUCCEEDED":
    raise RuntimeError(
        f"Apify Actor did not complete successfully. Status: {status}"
    )

print("\nActor completed successfully!")


# --------------------------------------------------
# 5. Download dataset
# --------------------------------------------------

dataset_url = (
    f"{BASE_URL}/datasets/{dataset_id}/items"
    "?format=json&clean=true"
)

response = requests.get(
    dataset_url,
    headers=HEADERS,
    timeout=60,
)

response.raise_for_status()

jobs = response.json()


# --------------------------------------------------
# 6. Save jobs locally
# --------------------------------------------------

os.makedirs("data", exist_ok=True)

output_file = "data/jobs.json"

with open(output_file, "w", encoding="utf-8") as file:
    json.dump(jobs, file, indent=2, ensure_ascii=False)


# --------------------------------------------------
# 7. Display summary
# --------------------------------------------------

print("\n====================================")
print("JOB SEARCH COMPLETED")
print("====================================")

print(f"Jobs found: {len(jobs)}")
print(f"Saved to: {output_file}")

for index, job in enumerate(jobs, start=1):

    print(
        f"{index}. "
        f"{job.get('title', 'Unknown')} "
        f"at {job.get('companyName', 'Unknown')} "
        f"({job.get('location', 'Unknown')})"
    )