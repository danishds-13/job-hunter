import subprocess
import sys


def run_script(script_name):
    """
    Run a Python script and stop the pipeline if it fails.
    """

    print()
    print("=" * 50)
    print(f"RUNNING: {script_name}")
    print("=" * 50)

    result = subprocess.run(
        [sys.executable, script_name],
        check=False
    )

    if result.returncode != 0:
        print()
        print("=" * 50)
        print(f"FAILED: {script_name}")
        print("=" * 50)

        sys.exit(result.returncode)

    print()
    print("=" * 50)
    print(f"COMPLETED: {script_name}")
    print("=" * 50)


def main():

    print()
    print("=" * 50)
    print("       DEVOPS JOB HUNTER")
    print("=" * 50)

    # Step 1: Get jobs from Apify
    run_script("app.py")

    # Step 2: Match jobs against your profile
    run_script("matcher.py")

    # Step 3: Upload new jobs to Google Sheets
    #        and send Telegram notifications
    run_script("sheets.py")

    print()
    print("=" * 50)
    print("       JOB HUNT COMPLETED")
    print("=" * 50)
    print()
    print("Pipeline finished successfully.")
    print()


if __name__ == "__main__":
    main()

