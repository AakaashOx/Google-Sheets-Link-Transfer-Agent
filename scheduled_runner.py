
import os
import logging
from pathlib import Path
from datetime import datetime

# Always run relative to the project folder
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

from google_sheets import (
    get_google_sheets_service,
    read_form_responses,
    write_transfer_plan
)

from main import CLASSES, process_class

from week_registry import (
    load_registry,
    get_registered_week
)

from automation_registry import load_automation_settings


# ==========================================
# LOGGING SETUP
# ==========================================

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "automation.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


def log_message(message):
    print(message)
    logging.info(message)


# ==========================================
# SCHEDULED UPDATE
# ==========================================

def run_scheduled_update():

    log_message("========== SCHEDULED UPDATE STARTED ==========")

    # 1. Check automation settings
    settings = load_automation_settings()

    if not settings.get("enabled", False):
        log_message("Automation is disabled. No update performed.")
        return

    if settings.get("paused", False):
        log_message("Automation is paused. No update performed.")
        return

    selected_week = settings.get("selected_week")

    if selected_week is None:
        log_message("No week selected. No update performed.")
        return

    selected_week = int(selected_week)

    # 2. Check whether the selected week is registered
    registry = load_registry()

    evaluation_url = registry.get("evaluation_url", "")

    week_details = get_registered_week(selected_week)

    if not week_details:
        log_message(
            f"Week {selected_week} is not registered. "
            "No update performed."
        )
        return

    source_url = week_details.get("source_url", "")

    if not source_url or not evaluation_url:
        log_message("Missing spreadsheet URL. No update performed.")
        return

    log_message(f"Selected week: {selected_week}")

    try:

        # 3. Connect to Google Sheets
        service = get_google_sheets_service()

        # 4. Read weekly submissions
        submissions = read_form_responses(
            service,
            source_url
        )

        if not submissions:
            log_message("No submissions found. No update performed.")
            return

        # 5. Prepare both class transfer plans first
        prepared_updates = []

        for class_name in CLASSES.values():

            log_message(
                f"Preparing Week {selected_week} — {class_name}"
            )

            result = process_class(
                service,
                submissions,
                evaluation_url,
                class_name,
                selected_week
            )

            prepared_updates.append({
                "class_name": class_name,
                "plan": result["transfer"]["plan"]
            })

        # 6. Write only after both previews are prepared
        for item in prepared_updates:

            class_name = item["class_name"]
            plan = item["plan"]

            if not plan:
                log_message(
                    f"{class_name}: No links to transfer."
                )
                continue

            updated = write_transfer_plan(
                service,
                evaluation_url,
                class_name,
                selected_week,
                plan
            )

            log_message(
                f"Week {selected_week} — {class_name}: "
                f"{updated} links updated successfully."
            )

        log_message("========== SCHEDULED UPDATE COMPLETED ==========")

    except Exception as error:

        logging.exception(
            f"Scheduled update failed for Week {selected_week}"
        )

        log_message(f"ERROR: {error}")


if __name__ == "__main__":
    run_scheduled_update()
