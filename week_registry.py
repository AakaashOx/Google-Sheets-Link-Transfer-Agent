
import json
from pathlib import Path
from datetime import datetime


CONFIG_DIR = Path(__file__).parent / "config"
CONFIG_FILE = CONFIG_DIR / "registered_weeks.json"


def load_registry():

    if not CONFIG_FILE.exists():
        return {
            "evaluation_url": "",
            "weeks": {}
        }

    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_registry(data):

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def register_week(week, source_url, evaluation_url):

    week = int(week)

    if week < 1:
        raise ValueError("Week number must be at least 1.")

    if not source_url.strip() or not evaluation_url.strip():
        raise ValueError("Both spreadsheet URLs are required.")

    registry = load_registry()

    existing_evaluation_url = registry.get("evaluation_url", "")

    if (
        existing_evaluation_url
        and existing_evaluation_url.strip() != evaluation_url.strip()
    ):
        raise ValueError(
            "The registered weeks already use a different evaluation spreadsheet."
        )

    registry["evaluation_url"] = evaluation_url.strip()

    registry["weeks"][str(week)] = {
        "source_url": source_url.strip(),
        "registered_at": datetime.now().astimezone().isoformat(
            timespec="seconds"
        )
    }

    save_registry(registry)

    return registry


def get_registered_week(week):

    registry = load_registry()

    return registry["weeks"].get(str(int(week)))


def get_registered_weeks():

    registry = load_registry()

    return sorted(
        registry["weeks"].keys(),
        key=int
    )




def unregister_week(week):

    from automation_registry import load_automation_settings

    data = load_registry()
    week_key = str(int(week))

    if week_key not in data["weeks"]:
        raise ValueError(f"Week {week} is not registered.")

    automation = load_automation_settings()

    if automation.get("selected_week") == int(week):
        raise ValueError(
            f"Week {week} is selected for automation. "
            "Disable automation and clear its selected week first."
        )

    del data["weeks"][week_key]

    if not data["weeks"]:
        data["evaluation_url"] = ""

    save_registry(data)

    return True

